"""
Dev-only: hand-built OHLC fixtures shared by test_rules.py and ascii_render.py.

('htf', o,h,l,c) expands to 12 identical LTF bars so the resulting HTF bar has exactly
those OHLC values; ('ltf', o,h,l,c) appends a single LTF bar.
"""

import numpy as np

PER = 12


def build(segs):
    """segs: ('htf', o,h,l,c) expands to 12 identical LTF bars; ('ltf', o,h,l,c) is one bar."""
    o, h, l, c = [], [], [], []
    for seg in segs:
        kind = seg[0]
        bar = seg[1:5]
        reps = PER if kind == "htf" else 1
        for _ in range(reps):
            o.append(bar[0]); h.append(bar[1]); l.append(bar[2]); c.append(bar[3])
    return (np.array(o), np.array(h), np.array(l), np.array(c))


def htf_base(swing_bar, thereafter=(100.00, 100.00, 100.00, 100.00)):
    segs = [("htf", 100.00, 100.00, 100.00, 100.00)] * 12      # HTF 0..11 flat
    segs.append(("htf",) + swing_bar)                          # HTF 12 = major swing
    segs += [("htf",) + thereafter] * 12                       # HTF 13..24
    return segs


def tail(n=12, px=101.70):
    """Flat padding so the last HTF bar is complete."""
    return [("ltf", px, px, px, px)] * n


def scenario_long(trend="with"):
    if trend == "with":
        segs = htf_base((100.00, 100.00, 99.90, 99.95))        # major swing LOW 99.90
        sweep = [("htf", 99.98, 100.05, 99.50, 100.02),        # sweeps 99.90, closes inside
                 ("htf", 100.02, 100.30, 100.00, 100.25),      # reverses up, stays inside
                 ("htf", 100.25, 100.60, 100.05, 100.50)]      # confirms -> LS
        base = 100.50
    else:  # counter-trend: HTF series declines into the sweep -> EMA(200) lags above price
        segs = [("htf", 110.00 - 0.30 * b, 110.00 - 0.30 * b,
                 109.90 - 0.30 * b, 109.95 - 0.30 * b) for b in range(12)]
        segs.append(("htf", 106.30, 106.40, 106.00, 106.10))   # major swing low 106.00
        segs += [("htf", 106.00 + 0.08 * k, 106.10 + 0.08 * k,
                  105.95 + 0.08 * k, 106.05 + 0.08 * k) for k in range(1, 13)]
        sweep = [("htf", 106.50, 106.60, 105.60, 106.20),
                 ("htf", 106.20, 106.45, 106.05, 106.35),
                 ("htf", 106.35, 106.60, 106.10, 106.50)]
        base = 106.50
    segs += sweep
    segs += [("ltf", base, base, base, base)] * 6               # 336..341
    segs += [("ltf", base, base + 0.50, base, base)]            # 342: pivot high
    segs += [("ltf", base, base, base, base)] * 5               # 343..347 -> pivot confirmed
    segs += [("ltf", base, base + 0.70, base - 0.05, base + 0.70)]   # 348: MSS up
    segs += [("ltf", base + 0.80, base + 0.80, base + 0.60, base + 0.75)]  # 349 (gap top)
    segs += [("ltf", base + 0.70, base + 0.75, base + 0.55, base + 0.60)]  # 350
    segs += [("ltf", base + 0.50, base + 0.40, base + 0.35, base + 0.45)]  # 351: bearish FVG
    segs += [("ltf", base + 0.45, base + 1.15, base + 0.35, base + 1.10)]  # 352: disrespect
    segs += [("ltf", base + 1.10, base + 1.30, base + 0.70, base + 1.20)]  # 353: leaves zone
    segs += [("ltf", base + 1.20, base + 1.25, base + 0.45, base + 0.60)]  # 354: taps CE
    segs += tail(14, base + 0.60)
    return build(segs)
