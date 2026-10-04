"""
Dev-only: grammar-checks SmartRiskAPlus.pine with an offline Pine parser.

    python3 -m venv .venv && .venv/bin/pip install pynescript
    .venv/bin/python check_syntax.py

Parsing does not replace compiling in the TradingView Pine Editor (that also does
type checking), but it catches syntax errors, bad indentation and malformed calls.
"""
import os
import sys

from pynescript.ast import parse

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, os.pardir, "SmartRiskAPlus.pine")

source = open(SCRIPT, encoding="utf-8").read()
try:
    tree = parse(source, filename=os.path.basename(SCRIPT))
except Exception as exc:  # pynescript raises its own SyntaxError subclasses
    print(f"PARSE FAILED: {type(exc).__name__}")
    print(str(exc)[:4000])
    sys.exit(1)

print(f"PARSE OK  ({len(source.splitlines())} lines)")
print(f"top-level statements: {len(tree.body)}")
