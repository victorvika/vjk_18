#!/usr/bin/env python3
"""
pine_check.py - static consistency checker for the VJK-18 Pine Script v6 indicator.

It cannot replace the TradingView compiler, but it catches the mechanical error classes that
matter most for a script of this size:

  1. unbalanced parentheses / brackets / quotes
  2. tab characters and non-conforming indentation
  3. calls to undeclared functions (typos)
  4. wrong argument count for user defined functions and UDT constructors
  5. UDT member access on an object whose type is known locally
  6. use of identifiers that are not declared yet (use-before-declaration)
  7. request.security lookahead misuse (repainting risk)
  8. history operator applied to objects (illegal in Pine)
  9. global scalar assignment from inside a user function (illegal in Pine)
 10. duplicate declarations in the same scope

Usage:  python3 tools/pine_check.py pine/VJK18_ICT_Model.pine
"""

import re
import sys
from collections import defaultdict

BUILTIN_NAMESPACES = {
    "ta", "math", "str", "array", "box", "label", "line", "table", "color", "request",
    "input", "timeframe", "strategy", "matrix", "map", "chart", "runtime", "session",
    "syminfo", "time", "barstate", "alert", "ticker", "currency", "dayofweek", "display",
    "extend", "format", "hline", "location", "order", "plot", "position", "scale",
    "shape", "size", "text", "xloc", "yloc", "adjustment", "backadjustment", "barmerge",
    "earnings", "font", "settlement_as_close", "splits", "dividends", "log",
}

BUILTIN_FUNCS = {
    # series / general
    "abs", "acos", "alert", "alertcondition", "asin", "atan", "avg", "barcolor", "bgcolor",
    "bool", "box", "ceil", "close", "color", "cos", "dayofmonth", "dayofweek", "exp", "fill",
    "fixnan", "float", "floor", "heikinashi", "high", "hline", "hour", "indicator", "input",
    "int", "label", "line", "linreg", "log", "low", "math", "max", "min", "minute", "month",
    "na", "nz", "open", "plot", "plotarrow", "plotbar", "plotcandle", "plotchar", "plotshape",
    "request", "round", "second", "sign", "sin", "sqrt", "str", "sum", "table", "tan", "ta",
    "ticker", "time", "timestamp", "time_close", "timeframe", "to", "tostring", "tr", "valuewhen",
    "var", "varip", "volume", "year", "switch", "if", "for", "while", "and", "or", "not",
    "library", "linefill", "polyline", "chart", "runtime", "session", "syminfo", "barstate",
    "strategy", "matrix", "map", "array", "box", "label", "line", "table", "color", "type",
    "method", "enum", "export", "import", "continue", "break", "return",
}

BUILTIN_CONSTS = {
    "true", "false", "na", "open", "high", "low", "close", "volume", "time", "hl2", "hlc3",
    "ohlc4", "hlcc4", "bar_index", "last_bar_index", "time_close", "hour", "minute", "second",
    "dayofmonth", "dayofweek", "weekofyear", "month", "year", "syminfo", "timeframe",
    "barstate", "na", "int", "float", "bool", "string", "color", "line", "label", "box",
    "table", "array", "matrix", "map", "strategy", "timenow", "session", "math", "str",
    "chart", "runtime", "request", "ta", "display", "extend", "format", "position", "size",
    "text", "xloc", "yloc", "alert", "barmerge", "location", "scale", "shape", "order",
    "adjustment", "backadjustment", "currency", "dayofweek", "earnings", "font", "hline",
    "ticker", "type", "log", "method", "polyline",
}

RESERVED = {
    "if", "else", "for", "while", "switch", "var", "varip", "type", "enum", "method",
    "export", "import", "and", "or", "not", "in", "to", "by", "na", "true", "false",
    "int", "float", "bool", "string", "color", "line", "label", "box", "table", "array",
    "matrix", "map", "polyline", "linefill", "continue", "break", "return", "series",
    "simple", "const", "input", "plot", "indicator", "strategy", "library", "new",
}

ERRORS = []
WARNINGS = []


def err(line, msg):
    ERRORS.append((line, msg))


def warn(line, msg):
    WARNINGS.append((line, msg))


def strip_comment(line: str) -> str:
    """remove trailing // comment, ignoring // inside string literals"""
    out = []
    in_str = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '"' and (i == 0 or line[i - 1] != '\\'):
            in_str = not in_str
            out.append(ch)
        elif not in_str and ch == '/' and i + 1 < len(line) and line[i + 1] == '/':
            break
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def blank_strings(line: str) -> str:
    """replace string literal contents (keeps the quotes) so token scans ignore prose"""
    out, in_str = [], False
    for i, ch in enumerate(line):
        if ch == '"' and (i == 0 or line[i - 1] != '\\'):
            in_str = not in_str
            out.append(ch)
        elif in_str:
            out.append("x")
        else:
            out.append(ch)
    return "".join(out)


def split_args(argstr: str):
    """split a function argument string on top-level commas"""
    args, depth, cur, in_str = [], 0, "", False
    for ch in argstr:
        if ch == '"':
            in_str = not in_str
        if not in_str:
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            elif ch == "," and depth == 0:
                args.append(cur.strip())
                cur = ""
                continue
        cur += ch
    if cur.strip():
        args.append(cur.strip())
    return args


def find_calls(line: str):
    """yield (name, argstring) for every call in the line"""
    for m in re.finditer(r"(?<![\w.])([A-Za-z_][A-Za-z0-9_]*)\s*\(", line):
        name = m.group(1)
        start = m.end() - 1
        depth, i, in_str = 0, start, False
        while i < len(line):
            ch = line[i]
            if ch == '"':
                in_str = not in_str
            if not in_str:
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        break
            i += 1
        yield name, line[start + 1:i], m.start()


def main(path):
    src = open(path).read()
    lines = src.split("\n")
    # ---- multi-line handling: join lines that end with an operator or open paren
    logical = []          # (first_line_no, text)
    buf, buf_start, depth = "", 0, 0
    for n, raw in enumerate(lines, 1):
        code = blank_strings(strip_comment(raw))
        if buf == "":
            buf_start = n
        buf += (" " if buf else "") + code
        depth += code.count("(") - code.count(")")
        depth += code.count("[") - code.count("]")
        if depth > 0:
            continue
        logical.append((buf_start, buf))
        buf, depth = "", 0
    if buf:
        logical.append((buf_start, buf))

    # ---------------- declarations ----------------
    udt = {}                       # type name -> [field names]
    cur_type = None
    for n, raw in enumerate(lines, 1):
        code = strip_comment(raw)
        m = re.match(r"^type\s+([A-Za-z_][A-Za-z0-9_]*)\s*$", code)
        if m:
            cur_type = m.group(1)
            udt[cur_type] = []
            continue
        if cur_type:
            mf = re.match(r"^\s+([A-Za-z_][A-Za-z0-9_]*(?:<[^>]+>)?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=", code)
            if mf:
                udt[cur_type].append(mf.group(2))
                continue
            fm = re.match(r"^\s+([A-Za-z_][A-Za-z0-9_]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*$", code)
            if fm:
                udt[cur_type].append(fm.group(2))
                continue
            if code.strip() and not code.startswith(" "):
                cur_type = None

    funcs = {}                     # name -> [params]
    for n, raw in enumerate(lines, 1):
        code = strip_comment(raw)
        m = re.match(r"^\s*(?:method\s+)?(?:(?:array<[^>]+>|matrix<[^>]+>|map<[^>]+>|[A-Za-z_][A-Za-z0-9_.]*)\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*=>", code)
        if m:
            params = [p.strip() for p in split_args(m.group(2))] if m.group(2).strip() else []
            pnames = []
            for p in params:
                parts = p.split()
                pnames.append(parts[-1] if parts else p)
            if m.group(1) in funcs:
                err(n, f"duplicate function definition: {m.group(1)}")
            funcs[m.group(1)] = pnames

    # ---------------- checks ----------------
    # Pine has no return-type annotation: "string f(x) =>" is a parse error (CE10152)
    for n, raw in enumerate(lines, 1):
        code = blank_strings(strip_comment(raw))
        if re.match(r"^\s*(?:string|float|int|bool|color|line|label|box|table|polyline|linefill|void|array<[^>]+>|matrix<[^>]+>|map<[^>]+>)\s+[A-Za-z_][A-Za-z0-9_]*\s*\([^)]*\)\s*=>\s*$", code):
            err(n, "typed function declaration is not valid Pine - remove the type prefix")
        if re.match(r"^\s*const\s+", code):
            warn(n, "'const' declaration keyword - verify it is supported by your Pine version")
    # fields sharing a name with a built-in namespace or a reserved keyword are risky
    for tname, fields in udt.items():
        for f in fields:
            if f in BUILTIN_NAMESPACES:
                warn(0, f"type {tname}: field name '{f}' collides with a built-in namespace")
            if f in RESERVED:
                err(0, f"type {tname}: field name '{f}' is a reserved keyword")

    # identifiers that shadow a Pine namespace are illegal ("'line' is not a valid type keyword")
    for n, raw in enumerate(lines, 1):
        code = blank_strings(strip_comment(raw))
        if code.strip().startswith("//"):
            continue
        code_no_loops = re.sub(r"\b(for|while)\b[^\n]*", "", code)
        for m in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?::=|=)(?!=)", code_no_loops):
            vartype, name = m.group(1), m.group(2)
            if name in RESERVED or name in BUILTIN_NAMESPACES:
                err(n, f"variable '{name}' is named like a reserved word / built-in namespace")
            TYPE_KEYWORDS = {"int", "float", "bool", "string", "color", "line", "label", "box",
                             "table", "array", "matrix", "map", "polyline", "linefill",
                             "series", "simple", "const", "var", "varip"}
            if vartype in RESERVED and vartype not in TYPE_KEYWORDS and vartype not in udt:
                err(n, f"'{vartype}' is not a valid type keyword for '{name}'")
    declared = {}                  # global identifier -> line
    # globals declared with var/typed at indent 0 (illegal to reassign with := inside functions)
    global_scalars = set()
    for ln, code in logical:
        if code.startswith(("var ", "varip ", "const ")) and "=>" not in code:
            m = re.match(r"(?:var|varip|const)\s+(?:float|int|bool|string|color)\s+([A-Za-z_][A-Za-z0-9_]*)", code)
            if m:
                global_scalars.add(m.group(1))
    # function bodies (indented blocks that follow a "=>" definition)
    body_owner = {}
    cur_fun = None
    for ln, code in logical:
        if code.strip() == "":
            continue
        indent = len(code) - len(code.lstrip(" "))
        if indent == 0:
            if "=>" in code:
                m = re.match(r"^\s*(?:method\s+)?(?:(?:[A-Za-z_][A-Za-z0-9_.]*)\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(", code)
                cur_fun = m.group(1) if m else None
            else:
                cur_fun = None
        elif cur_fun:
            body_owner[ln] = cur_fun

    # global declarations and their line numbers (for use-before-declaration inside functions)
    global_decl_line = {}
    for ln, code in logical:
        code_clean = code.lstrip()
        if code.strip() and not code.startswith(" ") and "=>" not in code:
            m = re.match(r"(?:var|varip|const)\s+[\w<>]+\s+([A-Za-z_][A-Za-z0-9_]*)", code_clean)
            if m:
                global_decl_line.setdefault(m.group(1), ln)
            m2 = re.match(r"[\w<>]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*=", code_clean)
            if m2:
                global_decl_line.setdefault(m2.group(1), ln)
            m3 = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*=", code_clean)
            if m3:
                global_decl_line.setdefault(m3.group(1), ln)

    for ln, code in logical:
        if not code.strip():
            continue
        if ln in body_owner:
            for m in re.finditer(r"(?<![\w.])([A-Za-z_][A-Za-z0-9_]*)", code):
                ident = m.group(1)
                if ident in global_decl_line and global_decl_line[ident] > ln:
                    err(ln, f"function '{body_owner[ln]}' uses the global '{ident}' before its declaration (line {global_decl_line[ident]})")
            for m in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*:=", code):
                if m.group(1) in global_scalars:
                    err(ln, f"user function '{body_owner[ln]}' reassigns the global scalar '{m.group(1)}' (illegal in Pine)")
        indent = len(code) - len(code.lstrip(" "))
        stripped = code.strip()

        # 2. tabs
        if "\t" in code:
            err(ln, "tab character found (Pine requires spaces)")
        if indent % 4 != 0:
            err(ln, f"indentation {indent} is not a multiple of 4")

        # 1. bracket balance
        for open_ch, close_ch in (("(", ")"), ("[", "]"), ("{", "}")):
            if code.count(open_ch) != code.count(close_ch):
                err(ln, f"unbalanced '{open_ch}{close_ch}'")
        if code.count('"') % 2 != 0:
            err(ln, "unbalanced quote")

        # 7. lookahead misuse
        if "lookahead_on" in code:
            err(ln, "request.security with lookahead_on breaks the non-repainting guarantee")
        if re.search(r"\[\s*-\d", code):
            err(ln, "negative history offset (looks into the future)")
        if re.search(r"request\.security\s*\([^)]*\)\s*\[", code):
            err(ln, "history operator applied to request.security result")

        # 2b. trailing tokens after a complete call (e.g. "Foo.new(...), 0" leftovers)
        for m1 in re.finditer(r"\w+\.new\s*\(", code):
            # only inspect constructors that are the OUTERMOST call on the line
            pre = code[:m1.start()]
            if pre.count("(") - pre.count(")") != 0:
                continue
            st = m1.end() - 1
            d, j, s_in = 0, st, False
            while j < len(code):
                ch = code[j]
                if ch == '"':
                    s_in = not s_in
                if not s_in:
                    if ch == "(":
                        d += 1
                    elif ch == ")":
                        d -= 1
                        if d == 0:
                            break
                j += 1
            tail = code[j + 1:].strip()
            if tail and not tail.startswith(("//", "+", ".")) and re.match(r"^[,)]", tail):
                err(ln, f"unexpected trailing tokens after constructor call: {tail[:40]}")

        # 3/4. function calls
        for name, argstr, pos in find_calls(code):
            args = split_args(argstr)
            args = [a for a in args if a != ""]
            if name in funcs:
                want = len(funcs[name])
                got = len(args)
                if got != want:
                    err(ln, f"{name}(): expected {want} args, found {got}")
            elif name in udt:
                want = len(udt[name])
                got = len(args)
                if got != want:
                    err(ln, f"{name}.new(): expected {want} args, found {got}")
            elif name.isupper() or name[0].isupper():
                pass
            elif name not in BUILTIN_FUNCS and not re.search(r"\.\s*" + name + r"\s*\(", code):
                if name not in declared and name not in ("if", "for", "while", "switch", "and", "or", "not"):
                    err(ln, f"call to undeclared function: {name}()")

        # 4b. UDT constructor calls Type.new(...) - argument count must match the field count
        for m in re.finditer(r"\b([A-Z][A-Za-z0-9_]*)\.new\s*\(", code):
            tname = m.group(1)
            if tname not in udt:
                continue
            start = m.end() - 1
            depth, i2, in_str = 0, start, False
            while i2 < len(code):
                ch = code[i2]
                if ch == '"':
                    in_str = not in_str
                if not in_str:
                    if ch == "(":
                        depth += 1
                    elif ch == ")":
                        depth -= 1
                        if depth == 0:
                            break
                i2 += 1
            args = [a for a in split_args(code[start + 1:i2]) if a.strip()]
            if len(args) != len(udt[tname]):
                err(ln, f"{tname}.new(): {len(args)} arguments for {len(udt[tname])} fields")

        # 5. member access on known object types
        for m in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\.\s*([A-Za-z_][A-Za-z0-9_]*)", code):
            base, field = m.group(1), m.group(2)
            if base in udt:
                continue
            vtype = None
            for tname in udt:
                if re.search(r"\b" + tname + r"\s+" + base + r"\b", code):
                    vtype = tname
            if vtype and field not in udt[vtype] and field != "new":
                err(ln, f"{vtype}.{field} does not exist (available: {', '.join(udt[vtype])})")

        # 8. history operator on user objects
        for m in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\[", code):
            base = m.group(1)
            if base in udt or (base[0].isupper()):
                err(ln, f"history operator applied to object type {base}")
            if base in funcs:
                err(ln, f"history operator applied to function result {base}")

        # 9. global mutation from inside a function: catch obviously scalar globals
        #    (handled manually - reported as informational only)

        # 6. use before declaration (global scope assignments and declarations)
        if indent == 0 and "=>" not in stripped:
            for m in re.finditer(r"\b([a-z_][a-z0-9_]*)\b", code):
                ident = m.group(1)
                if ident in BUILTIN_CONSTS or ident in BUILTIN_FUNCS or ident in funcs or ident in udt:
                    continue
                if re.search(r"#[0-9a-fA-F]{6}", code) and re.search(r"#\s*" + ident, code):
                    continue
                if ident in ("input", "plot", "alert", "type", "var", "varip", "const", "float",
                             "int", "bool", "string", "color", "line", "label", "box", "table",
                             "array", "matrix", "map", "and", "or", "not", "if", "else", "for",
                             "while", "switch", "continue", "break", "return", "export", "in",
                             "series", "simple", "export", "to", "by", "and"):
                    continue
                # skip identifiers that are part of a documented member access
                if re.search(r"\.\s*" + ident + r"\b", code):
                    continue
                # named argument (kwarg) inside a call
                if re.search(ident + r"\s*=[^=]", code) and "(" in code:
                    continue
                if set(ident) == {"x"} or ident.startswith("xx"):
                    continue
                # declared on this very line
                if re.search(r"\b" + ident + r"\s*(?::=|=)(?!=)", code):
                    continue
                if ident not in declared:
                    warn(ln, f"identifier used before declaration at global scope: {ident}")
            # register declarations on this line
            for m in re.finditer(r"(?:^|\s)(?:var|varip|const)?\s*(?:float|int|bool|string|color|line|label|box|table|polyline|linefill|array<[^>]+>|matrix<[^>]+>|map<[^>]+>|[A-Z][A-Za-z0-9_]*)?\s*([a-z_][a-z0-9_]*)\s*(?::=|=)(?!=)", code):
                ident = m.group(1)
                if ident not in ("if", "else", "for", "while"):
                    declared.setdefault(ident, ln)
            for m in re.finditer(r"^\[([^\]]+)\]\s*=", code):
                for ident in m.group(1).split(","):
                    declared.setdefault(ident.strip(), ln)

    # ---------------- function definition order (Pine requires definition before use) --------
    defline = {}
    for n, raw in enumerate(lines, 1):
        code = blank_strings(strip_comment(raw))
        m = re.match(r"^\s*(?:method\s+)?(?:(?:array<[^>]+>|matrix<[^>]+>|map<[^>]+>|[A-Za-z_][A-Za-z0-9_.]*)\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*=>", code)
        if m and m.group(1) in funcs:
            defline.setdefault(m.group(1), n)
    for name, dln in defline.items():
        for n, raw in enumerate(lines, 1):
            if n == dln:
                continue
            code = blank_strings(strip_comment(raw))
            if re.search(r"(?<![\w.])" + name + r"\s*\(", code):
                if n < dln:
                    err(n, f"function '{name}' is called on line {n} but defined later (line {dln})")

    # ---------------- report ----------------
    print(f"file: {path}")
    print(f"lines: {len(lines)}   logical lines: {len(logical)}")
    print(f"user functions: {len(funcs)}   user types: {len(udt)}")
    print(f"types: {', '.join(sorted(udt))}")
    print()
    if ERRORS:
        print(f"ERRORS ({len(ERRORS)}):")
        for ln, msg in sorted(ERRORS):
            print(f"  line {ln}: {msg}")
    else:
        print("ERRORS: none")
    print()
    if WARNINGS:
        print(f"WARNINGS ({len(WARNINGS)}):")
        for ln, msg in sorted(set(WARNINGS)):
            print(f"  line {ln}: {msg}")
    else:
        print("WARNINGS: none")
    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "pine/VJK18_ICT_Model.pine"))
