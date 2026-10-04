#!/usr/bin/env python3
"""
test_pine_check.py - regression tests for tools/pine_check.py.

The two rules added after the CE10013 compile errors are tested here, because both error
classes are silent for a reader (the code looks fine) and can only be caught mechanically:

  * check 17 - block body must be indented exactly 4 spaces past the line that opens it.
               An 8 -> 16 jump is a hard Pine parse error:
               "Mismatched input 'float' expecting set 'end of line without line continuation'".
  * check 18 - a variable declared inside a block must only be used inside that block.

Usage:  python3 tools/test_pine_check.py
"""

import subprocess
import sys
import tempfile
import os

CHECKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pine_check.py")

# A correct block: 4 -> 8 -> 12 -> 16 -> 20, and every local is used inside its own block.
GOOD = '''//@version=6
indicator("t")
var array<float> xs = array.new<float>()
fBest(float p) =>
    float best = -1.0
    if xs.size() > 0
        for i = 0 to xs.size() - 1
            float v = xs.get(i)
            if v > p
                float d = v - p
                if na(best) or d < best
                    best := d
    best
plot(fBest(close))
'''

# Same code, but the "if v > p" line lost 4 spaces of indentation: the body that follows
# jumps 8 -> 16.  This is exactly the shape that TradingView rejects with CE10013.
BAD_INDENT = GOOD.replace("            if v > p", "        if v > p")

# Correct indentation, but a loop variable is read after the loop that declared it.
BAD_SCOPE = '''//@version=6
indicator("t")
fSum() =>
    float total = 0.0
    for i = 0 to 2
        float v = i * 2.0
    total := v
    total
plot(fSum())
'''

CASES = [
    ("correct code passes", GOOD, []),
    ("8 -> 16 indent jump is reported", BAD_INDENT,
     ["indented ", "spaces past line"]),
    ("use outside the declaring block is reported", BAD_SCOPE,
     ["outside its scope"]),
]


def run(src: str):
    with tempfile.NamedTemporaryFile("w", suffix=".pine", delete=False) as fh:
        fh.write(src)
        path = fh.name
    try:
        p = subprocess.run([sys.executable, CHECKER, path], capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr
    finally:
        os.unlink(path)


def main():
    failed = 0
    for name, src, expect in CASES:
        code, out = run(src)
        ok = True
        if expect:
            if code == 0:
                ok = False
            for needle in expect:
                if needle not in out:
                    ok = False
        else:
            if code != 0:
                ok = False
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            failed += 1
            for line in out.splitlines():
                if line.strip():
                    print("      " + line)
    print()
    print(f"{len(CASES) - failed}/{len(CASES)} regression cases pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
