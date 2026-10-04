"""
Dev-only: prints an ASCII candle chart of one model setup, with the IFVG zone,
the 50% CE line, the SL/TP levels and the LS / MSS / Entry bars marked.

This is a text rendering of exactly what the Pine script draws - useful because
it can be inspected without opening TradingView and without viewing an image.

    .venv/bin/python ascii_render.py
"""
import numpy as np

from model import run
from scenarios import scenario_long  # deterministic, hand-built setup

ROWS, COLS = 30, 74


def render(o, h, l, c, ev, entry, lo, hi):
    zt, zb, ce = entry["zgTop"], entry["zgBot"], entry["ce"]
    sl, tp = entry["sl"], entry["tp"]
    pmin = min(min(l[lo:hi]), sl, zb)
    pmax = max(max(h[lo:hi]), tp, zt)
    span = pmax - pmin or 1.0

    def row_of(p):
        return int(round((pmax - p) / span * (ROWS - 1)))

    grid = [[" "] * COLS for _ in range(ROWS)]
    for col, i in enumerate(range(lo, hi)):
        r_h, r_l = row_of(h[i]), row_of(l[i])
        r_o, r_c = row_of(o[i]), row_of(c[i])
        for r in range(r_h, r_l + 1):
            grid[r][col] = "|"
        for r in range(min(r_o, r_c), max(r_o, r_c) + 1):
            grid[r][col] = "#" if c[i] >= o[i] else "o"
        # zone fill + CE line, only between the zone bar and the tap (as the script draws them)
        if entry["zgBar"] <= i <= entry["bar"]:
            for r in range(row_of(zt), row_of(zb) + 1):
                if grid[r][col] == " ":
                    grid[r][col] = "."
            r = row_of(ce)
            if grid[r][col] == " ":
                grid[r][col] = "-"
            elif grid[r][col] in "|#o":
                grid[r][col] = "="  # CE line crossing a candle

    labels = {}
    for r, (name, val) in {
        row_of(zt): ("zone top", zt), row_of(zb): ("zone bot", zb), row_of(ce): ("CE 50%", ce),
        row_of(sl): ("SL", sl), row_of(tp): ("TP", tp),
    }.items():
        labels.setdefault(r, []).append(f"{name} {val:.4f}")

    marks = {}
    for b, d in ev["ls"]:
        if lo <= b < hi:
            marks.setdefault(b - lo, []).append("LS")
    for b, d in ev["mss"]:
        if lo <= b < hi:
            marks.setdefault(b - lo, []).append("MSS")
    marks.setdefault(entry["bar"] - lo, []).append("Entry")

    print(f"\n  bars {lo}..{hi}   ({'long' if entry['dir'] == 1 else 'short'}, "
          f"{entry['rr']:g}R {'with' if entry['withTrend'] else 'against'} trend)\n")
    for r in range(ROWS):
        gutter = "   ".join(labels.get(r, []))[:26]
        print(f"{gutter:<26} |" + "".join(grid[r]))
    bar_row = [" "] * COLS
    for col, names in marks.items():
        for k, nm in enumerate(names):
            if col + len(nm) <= COLS:
                for j, ch in enumerate(nm):
                    bar_row[col + j] = ch
                col += len(nm) + 1
    print(" " * 26 + " |" + "".join(bar_row))
    print(" " * 26 + " +" + "-" * COLS)
    print(f"\n  IFVG zone  {zb:.4f} .. {zt:.4f}   |   CE {ce:.4f}   |   SL {sl:.4f}   |   TP {tp:.4f}")
    print(f"  risk {entry['risk']:.4f}  ->  reward {abs(tp - ce):.4f}  ({entry['rr']:g}R)")


if __name__ == "__main__":
    o, h, l, c = scenario_long("with")
    ev = run(o, h, l, c)
    e = ev["entry"][0]
    lo = max(0, e["bar"] - (COLS - 12))
    hi = min(len(c), e["bar"] + 12)
    render(o, h, l, c, ev, e, lo, hi)
