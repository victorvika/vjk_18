"""
Dev-only: renders a MOCK of what the SmartRiskAPlus indicator draws.
Runs the shared state machine (model.py) over synthetic 5m data, picks a clean
with-trend long setup and paints the candles + IFVG box + CE line + TP/SL lines +
labels so the styling and geometry can be eyeballed. (Not a TradingView screenshot.)

    .venv/bin/python preview.py
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from model import run

FWD = 12
C_BULL, C_BEAR, C_NEUT = "#4A7C74", "#A86A6A", "#6B7A8F"
C_TP, C_SL = "#4A7C74", "#A86A6A"


def build(seed, n_htf=3000, per=12):
    rng = np.random.default_rng(seed)
    n = n_htf * per
    step = rng.normal(0, 0.0009, n) + 0.00003 * np.sin(np.arange(n) / 1400.0)
    c = 100 * np.exp(np.cumsum(step))
    o = np.concatenate([[100.0], c[:-1]])
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.0006, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.0006, n)))
    return n, o, h, l, c


# ---------------- pick a clean with-trend long setup ----------------
found = None
for seed in range(1, 40):
    N, o, h, l, c = build(seed)
    ev = run(o, h, l, c)
    for e in ev["entry"]:
        if e["dir"] != 1:
            continue
        span = e["bar"] - e["lsBar"]
        risk = (e["ce"] - e["sl"]) / e["ce"] * 100
        if 30 <= span <= 160 and 0.10 <= risk <= 0.6 and e["withTrend"]:
            found = (seed, N, o, h, l, c, ev, e)
            break
    if found:
        break

if not found:
    raise SystemExit("no suitable setup found")

seed, N, o, h, l, c, ev, e = found
lo = max(0, e["lsBar"] - 25)
hi = min(N, e["bar"] + 26)
xs = np.arange(lo, hi)

fig, ax = plt.subplots(figsize=(15, 7.2), dpi=130)
fig.patch.set_facecolor("#FBFBF9")
ax.set_facecolor("#FBFBF9")

# candles
for i in xs:
    up = c[i] >= o[i]
    body_lo, body_hi = min(o[i], c[i]), max(o[i], c[i])
    ax.plot([i, i], [l[i], h[i]], color="#9AA3AA", lw=0.9, zorder=2, solid_capstyle="butt")
    ax.add_patch(Rectangle((i - 0.32, body_lo), 0.64, max(body_hi - body_lo, 1e-6),
                           facecolor="#DCE5E1" if up else "#EADFDF",
                           edgecolor=C_BULL if up else C_BEAR, lw=0.9, zorder=3))

# IFVG box: 95% transparent fill + thin dashed border
ax.add_patch(Rectangle((e["zgBar"] - 0.5, e["zgBot"]), (e["bar"] - e["zgBar"] + 1),
                       e["zgTop"] - e["zgBot"], facecolor=C_BULL, alpha=0.05,
                       edgecolor=C_BULL, lw=1.0, ls=(0, (5, 3)), zorder=1))

# 50% CE line (thin, dotted), price leaves the zone and taps it
ax.plot([e["zgBar"] - 0.5, e["bar"]], [e["ce"], e["ce"]], color=C_NEUT, lw=1.0, ls=(0, (1, 2)), zorder=4)

# SL / TP: short dashed lines to the right + tiny text past the candles
ax.plot([e["bar"], e["bar"] + FWD], [e["sl"], e["sl"]], color=C_SL, lw=1.1, ls=(0, (6, 3)), zorder=4)
ax.plot([e["bar"], e["bar"] + FWD], [e["tp"], e["tp"]], color=C_TP, lw=1.1, ls=(0, (6, 3)), zorder=4)
ax.text(e["bar"] + FWD + 0.6, e["sl"], "SL", color=C_SL, fontsize=8, va="center")
ax.text(e["bar"] + FWD + 0.6, e["tp"], "TP", color=C_TP, fontsize=8, va="center")

# labels: style_none text kept clear of the wicks
for (b, d) in ev["ls"]:
    if lo <= b <= hi:
        ax.text(b, l[b] if d == 1 else h[b], "LS", color=C_NEUT, fontsize=8,
                ha="center", va="top" if d == 1 else "bottom")
for (b, d) in ev["mss"]:
    if lo <= b <= hi:
        ax.text(b, l[b] if d == 1 else h[b], "MSS", color=C_NEUT, fontsize=8,
                ha="center", va="top" if d == 1 else "bottom")
ax.text(e["bar"], l[e["bar"]], "Entry", color=C_BULL, fontsize=9, ha="center", va="top")

ax.set_xlim(lo - 1, hi + FWD + 4)
pad = (max(h[xs]) - min(l[xs])) * 0.08
ax.set_ylim(min(l[xs]) - pad, max(h[xs]) + pad)
ax.set_xticks([])
ax.set_yticks([])
for s in ("top", "right", "left", "bottom"):
    ax.spines[s].set_visible(False)
ax.set_title("Smart Risk A+  —  mock rendering of the indicator drawings (synthetic data)",
             color="#55606B", fontsize=11, loc="left", pad=12)
plt.tight_layout()
plt.savefig("/home/user/vjk_18/dev/preview.png", facecolor=fig.get_facecolor())
print("setup:", {k: (round(v, 5) if isinstance(v, float) else v) for k, v in e.items()})
print("saved dev/preview.png")
