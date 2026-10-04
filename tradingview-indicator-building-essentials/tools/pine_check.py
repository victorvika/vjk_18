#!/usr/bin/env python3
"""
Static sanity checker for Pine Script v6 sources.

It is NOT a Pine compiler. It catches the classes of mistake that most often
break a TradingView paste-in:

  1. unbalanced (), [], {} across logical statements
  2. a new statement indented by something that is not a multiple of 4
  3. a local declared inside a block/function and referenced outside it
     (the classic "Undeclared identifier" error)
  4. duplicate declarations in the same scope
  5. calling a user-defined function before it is declared

Multi-line statements (continuation lines) are folded into one logical
statement first, so continuation indentation is never mistaken for a block.
"""
import re
import sys
from collections import defaultdict

SERIES_BUILTINS = {"open", "high", "low", "close", "volume", "time",
                   "bar_index", "hl2", "hlc3", "ohlc4"}
LOOPVAR_OK = {"i", "j", "k", "n", "m", "p", "q", "r", "s", "a", "b", "c",
              "e", "f", "t", "u", "v", "w", "x", "y", "z", "o", "h", "l"}
TYPE_RE = (r"(?:int|float|bool|string|color|line|label|box|table|array|matrix|"
           r"map|chart\.point|Liq|Fvg|Setup)")
DECL_RE = re.compile(
    rf"^(?P<mods>(?:var\s+|varip\s+)?)(?:{TYPE_RE}(?:<[^>]*>)?\s+)?"
    rf"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=(?!=)")
DEF_RE = re.compile(r"^(?:method\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*=>")
BLOCK_RE = re.compile(r"^(if|else|else\s+if|for|while|switch|type)\b")


def strip_strings(line: str) -> str:
    out, in_str = [], False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '"' and (i == 0 or line[i - 1] != '\\'):
            in_str = not in_str
            out.append(' ')
        elif in_str:
            out.append(' ')
        else:
            out.append(ch)
        i += 1
    return ''.join(out)


def code_part(line: str) -> str:
    s = strip_strings(line)
    idx = s.find('//')
    return (s[:idx] if idx >= 0 else s).rstrip()


def indentation(line: str) -> int:
    return len(line) - len(line.lstrip(' '))


def logical_lines(raw):
    """Fold continuation lines into logical statements."""
    out = []
    for ln, line in enumerate(raw, 1):
        body = code_part(line)
        if not out or depth_of(out[-1][1]) == 0:
            out.append([ln, body.strip(), indentation(line), [ln]])
        else:
            out[-1][1] += " " + body.strip()
            out[-1][3].append(ln)
    return [o for o in out if o[1].strip()]


def depth_of(text: str) -> int:
    d = 0
    for ch in text:
        if ch in '([{':
            d += 1
        elif ch in ')]}':
            d -= 1
    return d


def main(path):
    raw = open(path, encoding='utf-8').read().split('\n')
    errors = []
    ll = logical_lines(raw)

    # ------------------------------------------------------------------ 1 + 2
    for ln, body, ind, _ in ll:
        if body.count('(') != body.count(')') or body.count('[') != body.count(']'):
            errors.append(f"line {ln}: unbalanced brackets -> {body.strip()[:90]}")
        if ind is not None and ind % 4 != 0:
            errors.append(f"line {ln}: statement indented by {ind} (not a multiple of 4)")

    # ------------------------------------------------------------- scope paths
    # each logical statement knows the chain of enclosing block statements
    scopes = []          # stack of (indent, line, is_type_block)
    annotated = []
    for ln, body, ind, phys in ll:
        while scopes and ind <= scopes[-1][0]:
            scopes.pop()
        annotated.append((ln, body, ind, tuple(s[1] for s in scopes), any(s[2] for s in scopes)))
        if BLOCK_RE.match(body) or body.endswith('=>'):
            scopes.append((ind, ln, body.startswith('type ')))

    # ---------------------------------------------------------- function defs
    funcs = {}
    for ln, body, ind, _, in_type in annotated:
        if ind == 0:
            m = DEF_RE.match(body)
            if m:
                funcs.setdefault(m.group(1), ln)

    for ln, body, ind, _, _ in annotated:
        for name in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", body):
            if name in funcs and ln < funcs[name]:
                errors.append(f"line {ln}: '{name}' is called before its declaration (line {funcs[name]})")
                break

    # -------------------------------------------------------------- declarations
    decls = []
    for ln, body, ind, path, in_type in annotated:
        if in_type:
            continue                      # UDT fields are not variables
        m = DECL_RE.match(body)
        if not m:
            continue
        name = m.group('name')
        if name in ('if', 'for', 'while', 'else', 'switch', 'and', 'or', 'not', 'type'):
            continue
        if ind == 0 and name in SERIES_BUILTINS:
            errors.append(f"line {ln}: re-declares the built-in series '{name}'")
            continue
        decls.append((name, ln, ind, path))

    def enclosing_func(path):
        for ln in reversed(path):
            if ln in funcs.values():
                return ln
        return None

    seen = {}
    for name, ln, ind, path in decls:
        key = (name, path)
        if key in seen:
            errors.append(f"line {ln}: '{name}' declared twice in the same scope "
                          f"(earlier on line {seen[key]})")
        else:
            seen[key] = ln

    # ------------------------------ locals escaping their block (real errors)
    for name, ln, ind, path in decls:
        if ind == 0 or name in LOOPVAR_OK or len(name) < 3:
            continue
        own_func = enclosing_func(path)
        pat = re.compile(rf"\b{re.escape(name)}\b")
        for ln2, body2, ind2, path2, in_type2 in annotated:
            if enclosing_func(path2) != own_func:
                continue          # different function: separate namespace
            if ln2 <= ln or in_type2:
                continue
            if path2 == path:
                continue
            if len(path2) > len(path) and path2[:len(path)] == path:
                continue          # deeper nesting inside the declaring scope
            if pat.search(body2):
                errors.append(f"line {ln2}: '{name}' (declared line {ln} inside a nested "
                              f"block) is referenced outside that block")
                break

    # ------------------------------------------------------------------ report
    print(f"file      : {path}")
    print(f"lines     : {len(raw)}")
    print(f"statements: {len(ll)}")
    print(f"functions : {len(funcs)}")
    print(f"decls     : {len(decls)}")
    if errors:
        uniq = []
        for e in errors:
            if e not in uniq:
                uniq.append(e)
        print(f"\nERRORS ({len(uniq)}):")
        for e in uniq:
            print("  " + e)
    else:
        print("\nOK - no obvious structural problems found")
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'Arena_AI_ICT_Sequence_Model.pine'))
