"""
Dev-only: renders a MOCK of what the SmartRiskAPlus indicator draws.
Runs the same state machine over synthetic 5m data, picks a clean with-trend long
setup and paints the candles + IFVG box + CE line + TP/SL lines + labels so the
styling and geometry can be eyeballed. (Not a TradingView screenshot.)
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

LTF_PER_HTF = 12
SWING, CONFIRM, LTFSW = 10, 2, 5
DISP, SLBUF, RRW, RRA = 0.5, 0.10, 5.0, 3.0
FWD = 12

C_BULL, C_BEAR, C_NEUT = "#4A7C74", "#A86A6A", "#6B7A8F"
C_TP, C_SL = "#4A7C74", "#A86A6A"


def rma(x, n):
    a = 1.0 / n
    out, acc = np.empty_like(x), x[0]
    for i, v in enumerate(x):
        acc = (v - acc) * a + acc
        out[i] = acc
    return out


def pivothigh(src, L, R):
    out = np.full(len(src), np.nan)
    for i in range(L + R, len(src)):
        w, p = src[i - L - R:i + 1], src[i - R]
        if p == w.max() and (w == p).sum() == 1:
            out[i] = p
    return out


def pivotlow(src, L, R):
    out = np.full(len(src), np.nan)
    for i in range(L + R, len(src)):
        w, p = src[i - L - R:i + 1], src[i - R]
        if p == w.min() and (w == p).sum() == 1:
            out[i] = p
    return out


def build(seed, N_HTF=3000):
    rng = np.random.default_rng(seed)
    N = N_HTF * LTF_PER_HTF
    step = rng.normal(0, 0.0009, N) + 0.00003 * np.sin(np.arange(N) / 1400.0)
    c = 100 * np.exp(np.cumsum(step))
    o = np.concatenate([[100.0], c[:-1]])
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.0006, N)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.0006, N)))
    return N_HTF, N, o, h, l, c


def run(N_HTF, N, o, h, l, c):
    hH = h.reshape(N_HTF, LTF_PER_HTF).max(axis=1)
    hL = l.reshape(N_HTF, LTF_PER_HTF).min(axis=1)
    hO = o.reshape(N_HTF, LTF_PER_HTF)[:, 0]
    hC = c.reshape(N_HTF, LTF_PER_HTF)[:, -1]
    prev = np.concatenate([[c[0]], c[:-1]])
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev), np.abs(l - prev)))
    atr = rma(tr, 14)
    ph, pl = pivothigh(h, LTFSW, LTFSW), pivotlow(l, LTFSW, LTFSW)
    htfUp = hC > rma(hC, 200)

    hArr, lArr, htfSH, htfSL = [], [], None, None
    pendDir, pendLvl, pendWick, pendCnt = 0, None, None, 0
    LS = {}
    for hb in range(N_HTF):
        ltf_bar = hb * LTF_PER_HTF + LTF_PER_HTF - 1
        hArr.append(hH[hb]); lArr.append(hL[hb])
        if len(hArr) > 2 * SWING + 5:
            hArr.pop(0); lArr.pop(0)
        idx = len(hArr) - 1 - SWING
        if idx >= SWING:
            if hArr[idx] == max(hArr[idx - SWING:idx + SWING + 1]):
                htfSH = hArr[idx]
            if lArr[idx] == min(lArr[idx - SWING:idx + SWING + 1]):
                htfSL = lArr[idx]
        if pendDir != 0:
            rev = (hC[hb] > hO[hb]) if pendDir == 1 else (hC[hb] < hO[hb])
            ins = ((hC[hb] > pendLvl and hL[hb] >= pendWick) if pendDir == 1
                   else (hC[hb] < pendLvl and hH[hb] <= pendWick))
            if (rev and ins) if pendCnt == 0 else ins:
                pendCnt += 1
                if pendCnt >= CONFIRM:
                    LS[ltf_bar] = pendDir
                    pendDir, pendCnt = 0, 0
            else:
                pendDir, pendCnt = 0, 0
        if htfSL is not None and hL[hb] < htfSL and hC[hb] > htfSL:
            pendDir, pendLvl, pendWick, pendCnt = 1, htfSL, hL[hb], 0
        elif htfSH is not None and hH[hb] > htfSH and hC[hb] < htfSH:
            pendDir, pendLvl, pendWick, pendCnt = -1, htfSH, hH[hb], 0

    stDir = stStage = 0
    lsBar = extLow = extHigh = slLvl = mssRef = None
    zgTop = zgBot = zgBar = ceLvl = None
    lastPH = lastPHBar = lastPL = lastPLBar = None
    ev = {"ls": [], "mss": [], "ifvg": [], "entry": []}
    for i in range(2, N):
        if i in LS:
            stDir, stStage = LS[i], 1
            lsBar = i
            extLow, extHigh = l[i], h[i]
            zgTop = zgBot = zgBar = ceLvl = mssRef = None
            ev["ls"].append((i, LS[i]))
        if stStage >= 1:
            extLow = min(extLow, l[i]); extHigh = max(extHigh, h[i])
        if not np.isnan(ph[i]):
            lastPH, lastPHBar = ph[i], i - LTFSW
        if not np.isnan(pl[i]):
            lastPL, lastPLBar = pl[i], i - LTFSW
        if stStage >= 2 and mssRef is not None:
            if (c[i] < mssRef) if stDir == 1 else (c[i] > mssRef):
                zgTop = zgBot = zgBar = ceLvl = mssRef = None
                stStage = 1
                extLow, extHigh = l[i], h[i]
        if stStage == 1:
            if (stDir == 1 and lastPH is not None and lastPHBar > lsBar and c[i] > lastPH and c[i - 1] <= lastPH):
                slLvl, mssRef, stStage = extLow - SLBUF * atr[i], extLow, 2
                zgTop = zgBot = zgBar = None
                ev["mss"].append((i, 1))
            elif (stDir == -1 and lastPL is not None and lastPLBar > lsBar and c[i] < lastPL and c[i - 1] >= lastPL):
                slLvl, mssRef, stStage = extHigh + SLBUF * atr[i], extHigh, 2
                zgTop = zgBot = zgBar = None
                ev["mss"].append((i, -1))
        body = abs(c[i] - o[i])
        if stStage == 2:
            if stDir == 1:
                if h[i] < l[i - 2]:
                    zgTop, zgBot, zgBar = l[i - 2], h[i], i
                if (zgTop is not None and zgBar is not None and i > zgBar and c[i] > zgTop
                        and l[i] <= zgBot and body >= DISP * atr[i] and c[i] > o[i]):
                    stStage, ceLvl = 3, (zgTop + zgBot) / 2.0
                    ev["ifvg"].append((zgBar, zgTop, zgBot))
            else:
                if l[i] > h[i - 2]:
                    zgTop, zgBot, zgBar = l[i], h[i - 2], i
                if (zgBot is not None and zgBar is not None and i > zgBar and c[i] < zgBot
                        and h[i] >= zgTop and body >= DISP * atr[i] and c[i] < o[i]):
                    stStage, ceLvl = 3, (zgTop + zgBot) / 2.0
                    ev["ifvg"].append((zgBar, zgTop, zgBot))
        if stStage in (3, 4):
            invalid = (c[i] < zgBot) if stDir == 1 else (c[i] > zgTop)
            if invalid:
                zgTop = zgBot = zgBar = ceLvl = None
                stStage = 2
            elif stStage == 3:
                if (l[i] > zgTop) if stDir == 1 else (h[i] < zgBot):
                    stStage = 4
            elif (l[i] <= ceLvl <= h[i]
                  and ((slLvl < ceLvl) if stDir == 1 else (slLvl > ceLvl))):
                risk = max(abs(ceLvl - slLvl), 1e-9)
                wt = (stDir == 1 and htfUp[i // LTF_PER_HTF]) or (stDir == -1 and not htfUp[i // LTF_PER_HTF])
                tp = ceLvl + stDir * risk * (RRW if wt else RRA)
                ev["entry"].append(dict(bar=i, dir=stDir, ce=ceLvl, sl=slLvl, tp=tp, rr=(RRW if wt else RRA),
                                        lsBar=lsBar, zgBar=zgBar, zgTop=zgTop, zgBot=zgBot))
                stStage, stDir = 0, 0
    return ev


# ---------------- pick a clean with-trend long setup ----------------
found = None
for seed in range(1, 40):
    N_HTF, N, o, h, l, c = build(seed)
    ev = run(N_HTF, N, o, h, l, c)
    for e in ev["entry"]:
        if e["dir"] != 1:
            continue
        span = e["bar"] - e["lsBar"]
        risk = (e["ce"] - e["sl"]) / e["ce"] * 100
        if 30 <= span <= 160 and 0.15 <= risk <= 0.8 and e["rr"] == RRW:
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
