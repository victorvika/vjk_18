"""
Dev-only: Python mirror of the SmartRiskAPlus.pine state machine.

Imported by sim_final.py (random-walk statistics), test_rules.py (deterministic
rule tests) and preview.py (mock rendering), so all three exercise the same code
path. Keep this file in sync with the .pine script - it is the reference used to
verify the trading rules, not a trading tool.

Bar-by-bar order mirrors the script:
    HTF sweep engine (on the close of each HTF bar)
    -> LS event  -> extremes  -> structure failure  -> MSS  -> IFVG  -> CE tap
"""

import numpy as np

DEFAULTS = dict(
    ltf_per_htf=12,   # 5m bars per 1h bar
    swing=10,         # HTF major swing fractal length
    confirm=2,        # HTF candles confirming the sweep
    ltf_swing=5,      # LTF fractal length (MSS)
    disp=0.5,         # FVG disrespect: body >= disp * ATR
    sl_buf=0.10,      # SL placed sl_buf * ATR beyond the pre-MSS extreme
    rr_with=5.0,      # R:R with the HTF trend
    rr_against=3.0,   # R:R against the HTF trend
    trend_len=200,    # HTF trend EMA length
)


def rma(x, n):
    a = 1.0 / n
    out, acc = np.empty_like(x, dtype=float), float(x[0])
    for i, v in enumerate(x):
        acc = (v - acc) * a + acc
        out[i] = acc
    return out


def _pivot(src, L, R, is_high):
    """ta.pivothigh / ta.pivotlow: extreme must be unique inside the window
    (Pine ties resolve to the last occurrence, flat ranges therefore yield na)."""
    out = np.full(len(src), np.nan)
    for i in range(L + R, len(src)):
        w = src[i - L - R:i + 1]
        p = src[i - R]
        m = w.max() if is_high else w.min()
        if p == m and (w == m).sum() == 1:
            out[i] = p
    return out


def pivothigh(src, L, R):
    return _pivot(src, L, R, True)


def pivotlow(src, L, R):
    return _pivot(src, L, R, False)


def run(o, h, l, c, p=None):
    P = dict(DEFAULTS, **(p or {}))
    per, swing, confirm = P["ltf_per_htf"], P["swing"], P["confirm"]
    lsw, disp, slbuf = P["ltf_swing"], P["disp"], P["sl_buf"]
    N = len(c)
    n_htf = N // per

    hH = h[:n_htf * per].reshape(n_htf, per).max(axis=1)
    hL = l[:n_htf * per].reshape(n_htf, per).min(axis=1)
    hO = o[:n_htf * per].reshape(n_htf, per)[:, 0]
    hC = c[:n_htf * per].reshape(n_htf, per)[:, -1]

    prev = np.concatenate([[c[0]], c[:-1]])
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev), np.abs(l - prev)))
    atr = rma(tr, 14)
    ph, pl = pivothigh(h, lsw, lsw), pivotlow(l, lsw, lsw)
    htf_up = hC > rma(hC, P["trend_len"])
    # closed-HTF semantics: bars after the last complete HTF bar reuse its last value
    htf_up = {i: bool(htf_up[min(i // per, n_htf - 1)]) for i in range(N)}

    # ---------------- 1. HTF liquidity sweep ----------------
    hArr, lArr = [], []
    htfSH = htfSL = None
    pendDir, pendLvl, pendWick, pendCnt = 0, None, None, 0
    LS = {}
    for hb in range(n_htf):
        ltf_bar = hb * per + per - 1
        hArr.append(hH[hb]); lArr.append(hL[hb])
        if len(hArr) > 2 * swing + 5:
            hArr.pop(0); lArr.pop(0)

        idx = len(hArr) - 1 - swing
        if idx >= swing:
            wh = hArr[idx - swing:idx + swing + 1]
            if hArr[idx] == max(wh) and wh.count(max(wh)) == 1:
                htfSH = hArr[idx]
            wl = lArr[idx - swing:idx + swing + 1]
            if lArr[idx] == min(wl) and wl.count(min(wl)) == 1:
                htfSL = lArr[idx]

        if pendDir != 0:
            rev = (hC[hb] > hO[hb]) if pendDir == 1 else (hC[hb] < hO[hb])
            ins = ((hC[hb] > pendLvl and hL[hb] >= pendWick) if pendDir == 1
                   else (hC[hb] < pendLvl and hH[hb] <= pendWick))
            ok = (rev and ins) if pendCnt == 0 else ins
            if ok:
                pendCnt += 1
                if pendCnt >= confirm:
                    LS[ltf_bar] = pendDir
                    pendDir, pendCnt = 0, 0
            else:
                pendDir, pendCnt = 0, 0

        if htfSL is not None and hL[hb] < htfSL and hC[hb] > htfSL:
            pendDir, pendLvl, pendWick, pendCnt = 1, htfSL, hL[hb], 0
        elif htfSH is not None and hH[hb] > htfSH and hC[hb] < htfSH:
            pendDir, pendLvl, pendWick, pendCnt = -1, htfSH, hH[hb], 0

    # ---------------- 2-4. LTF sequence ----------------
    stDir = stStage = 0
    lsBar = extLow = extHigh = slLvl = mssRef = None
    zgTop = zgBot = zgBar = ceLvl = None
    lastPH = lastPHBar = lastPL = lastPLBar = None
    ev = dict(ls=[], mss=[], ifvg=[], invalid=[], structfail=[], entry=[])

    for i in range(2, N):
        if i in LS:
            stDir, stStage = LS[i], 1
            lsBar = i
            extLow, extHigh = l[i], h[i]
            zgTop = zgBot = zgBar = ceLvl = mssRef = None
            ev["ls"].append((i, LS[i]))

        if stStage >= 1:
            extLow = min(extLow, l[i])
            extHigh = max(extHigh, h[i])

        if not np.isnan(ph[i]):
            lastPH, lastPHBar = ph[i], i - lsw
        if not np.isnan(pl[i]):
            lastPL, lastPLBar = pl[i], i - lsw

        if stStage >= 2 and mssRef is not None:
            if (c[i] < mssRef) if stDir == 1 else (c[i] > mssRef):
                zgTop = zgBot = zgBar = ceLvl = mssRef = None
                stStage = 1
                extLow, extHigh = l[i], h[i]
                ev["structfail"].append(i)

        if stStage == 1:
            if (stDir == 1 and lastPH is not None and lastPHBar > lsBar
                    and c[i] > lastPH and c[i - 1] <= lastPH):
                slLvl, mssRef, stStage = extLow - slbuf * atr[i], extLow, 2
                zgTop = zgBot = zgBar = None
                ev["mss"].append((i, 1))
            elif (stDir == -1 and lastPL is not None and lastPLBar > lsBar
                    and c[i] < lastPL and c[i - 1] >= lastPL):
                slLvl, mssRef, stStage = extHigh + slbuf * atr[i], extHigh, 2
                zgTop = zgBot = zgBar = None
                ev["mss"].append((i, -1))

        body = abs(c[i] - o[i])
        if stStage == 2:
            if stDir == 1:
                if h[i] < l[i - 2]:                       # bearish (down) gap
                    zgTop, zgBot, zgBar = l[i - 2], h[i], i
                if (zgTop is not None and zgBar is not None and i > zgBar and c[i] > zgTop
                        and l[i] <= zgBot and body >= disp * atr[i] and c[i] > o[i]):
                    stStage, ceLvl = 3, (zgTop + zgBot) / 2.0
                    ev["ifvg"].append(dict(zgBar=zgBar, zgTop=zgTop, zgBot=zgBot, flipBar=i))
            else:
                if l[i] > h[i - 2]:                       # bullish (up) gap
                    zgTop, zgBot, zgBar = l[i], h[i - 2], i
                if (zgBot is not None and zgBar is not None and i > zgBar and c[i] < zgBot
                        and h[i] >= zgTop and body >= disp * atr[i] and c[i] < o[i]):
                    stStage, ceLvl = 3, (zgTop + zgBot) / 2.0
                    ev["ifvg"].append(dict(zgBar=zgBar, zgTop=zgTop, zgBot=zgBot, flipBar=i))

        if stStage in (3, 4):
            invalid = (c[i] < zgBot) if stDir == 1 else (c[i] > zgTop)
            if invalid:
                zgTop = zgBot = zgBar = ceLvl = None
                stStage = 2
                ev["invalid"].append(i)
            elif stStage == 3:
                if (l[i] > zgTop) if stDir == 1 else (h[i] < zgBot):
                    stStage = 4
            elif (l[i] <= ceLvl <= h[i]
                  and ((slLvl < ceLvl) if stDir == 1 else (slLvl > ceLvl))):
                risk = max(abs(ceLvl - slLvl), 1e-9)
                wt = (stDir == 1 and htf_up[i]) or (stDir == -1 and not htf_up[i])
                rr = P["rr_with"] if wt else P["rr_against"]
                tp = ceLvl + stDir * risk * rr
                ev["entry"].append(dict(bar=i, dir=stDir, ce=ceLvl, sl=slLvl, tp=tp, rr=rr,
                                        withTrend=bool(wt), risk=risk, lsBar=lsBar,
                                        zgBar=zgBar, zgTop=zgTop, zgBot=zgBot,
                                        extLow=extLow, extHigh=extHigh))
                stStage, stDir = 0, 0
    return ev
