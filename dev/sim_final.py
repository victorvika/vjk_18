"""
Dev-only: faithful Python mirror of SmartRiskAPlus.pine (final structure).
Validates that the LS -> MSS -> IFVG -> leave-zone -> CE-tap chain fires and that the
produced SL/TP are coherent. Run over several random-walk seeds.
"""
import numpy as np
import statistics as st

LTF_PER_HTF = 12
SWING, CONFIRM, LTFSW = 10, 2, 5
DISP, SLBUF, RRW, RRA = 0.5, 0.10, 5.0, 3.0


def rma(x, n):
    a = 1.0 / n
    out = np.empty_like(x)
    acc = x[0]
    for i, v in enumerate(x):
        acc = (v - acc) * a + acc
        out[i] = acc
    return out


def pivothigh(src, L, R):
    out = np.full(len(src), np.nan)
    for i in range(L + R, len(src)):
        w = src[i - L - R:i + 1]
        p = src[i - R]
        if p == w.max() and (w == p).sum() == 1:
            out[i] = p
    return out


def pivotlow(src, L, R):
    out = np.full(len(src), np.nan)
    for i in range(L + R, len(src)):
        w = src[i - L - R:i + 1]
        p = src[i - R]
        if p == w.min() and (w == p).sum() == 1:
            out[i] = p
    return out


def run(seed, N_HTF=4000):
    rng = np.random.default_rng(seed)
    N = N_HTF * LTF_PER_HTF
    step = rng.normal(0.0, 0.0009, N) + 0.00002 * np.sin(np.arange(N) / 900.0)
    c = 100 * np.exp(np.cumsum(step))
    o = np.concatenate([[100.0], c[:-1]])
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.0006, N)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.0006, N)))

    hH = h.reshape(N_HTF, LTF_PER_HTF).max(axis=1)
    hL = l.reshape(N_HTF, LTF_PER_HTF).min(axis=1)
    hO = o.reshape(N_HTF, LTF_PER_HTF)[:, 0]
    hC = c.reshape(N_HTF, LTF_PER_HTF)[:, -1]

    prev = np.concatenate([[c[0]], c[:-1]])
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev), np.abs(l - prev)))
    atr = rma(tr, 14)
    ph, pl = pivothigh(h, LTFSW, LTFSW), pivotlow(l, LTFSW, LTFSW)
    htfUp = hC > rma(hC, 200)

    # ---------- HTF sweep engine ----------
    hArr, lArr = [], []
    htfSH = htfSL = None
    pendDir, pendLvl, pendWick, pendCnt = 0, None, None, 0
    LS = {}
    for hb in range(N_HTF):
        ltf_bar = hb * LTF_PER_HTF + LTF_PER_HTF - 1
        hArr.append(hH[hb]); lArr.append(hL[hb])
        if len(hArr) > 2 * SWING + 5:
            hArr.pop(0); lArr.pop(0)
        n = len(hArr); idx = n - 1 - SWING
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

    # ---------- LTF state machine ----------
    stDir = stStage = 0
    lsBar = extLow = extHigh = slLvl = mssRef = None
    zgTop = zgBot = zgBar = ceLvl = flipBar = None
    lastPH = lastPHBar = lastPL = lastPLBar = None
    stats = dict(LS=0, MSS=0, IFVG=0, ENTRY=0, INVAL=0, LONG=0, SHORT=0, WT=0, STRUCTFAIL=0)
    waits, risks = [], []

    for i in range(2, N):
        if i in LS:
            stDir, stStage = LS[i], 1
            lsBar = i
            extLow, extHigh = l[i], h[i]
            zgTop = zgBot = zgBar = ceLvl = flipBar = mssRef = None
            stats['LS'] += 1
        if stStage >= 1:
            extLow = min(extLow, l[i]); extHigh = max(extHigh, h[i])
        if stStage >= 2 and mssRef is not None:
            if (c[i] < mssRef) if stDir == 1 else (c[i] > mssRef):
                zgTop = zgBot = zgBar = ceLvl = flipBar = mssRef = None
                stStage = 1
                extLow, extHigh = l[i], h[i]
                stats['STRUCTFAIL'] += 1
        if not np.isnan(ph[i]):
            lastPH, lastPHBar = ph[i], i - LTFSW
        if not np.isnan(pl[i]):
            lastPL, lastPLBar = pl[i], i - LTFSW
        if stStage == 1:
            if (stDir == 1 and lastPH is not None and lastPHBar > lsBar
                    and c[i] > lastPH and c[i - 1] <= lastPH):
                slLvl = extLow - SLBUF * atr[i]; mssRef = extLow; stStage = 2
                zgTop = zgBot = zgBar = None; stats['MSS'] += 1
            elif (stDir == -1 and lastPL is not None and lastPLBar > lsBar
                    and c[i] < lastPL and c[i - 1] >= lastPL):
                slLvl = extHigh + SLBUF * atr[i]; mssRef = extHigh; stStage = 2
                zgTop = zgBot = zgBar = None; stats['MSS'] += 1

        body = abs(c[i] - o[i])
        if stStage == 2:
            if stDir == 1:
                if l[i] > h[i - 2]:
                    zgTop, zgBot, zgBar = h[i - 2], h[i], i
                if (zgTop is not None and zgBar is not None and i > zgBar and c[i] > zgTop
                        and l[i] <= zgBot and body >= DISP * atr[i] and c[i] > o[i]):
                    stStage, flipBar, ceLvl = 3, i, (zgTop + zgBot) / 2.0
                    stats['IFVG'] += 1
            else:
                if h[i] < l[i - 2]:
                    zgTop, zgBot, zgBar = l[i], l[i - 2], i
                if (zgBot is not None and zgBar is not None and i > zgBar and c[i] < zgBot
                        and h[i] >= zgTop and body >= DISP * atr[i] and c[i] < o[i]):
                    stStage, flipBar, ceLvl = 3, i, (zgTop + zgBot) / 2.0
                    stats['IFVG'] += 1

        if stStage in (3, 4):
            invalid = (c[i] < zgBot) if stDir == 1 else (c[i] > zgTop)
            if invalid:
                zgTop = zgBot = ceLvl = None
                stStage = 2
                stats['INVAL'] += 1
            elif stStage == 3:
                if (l[i] > zgTop) if stDir == 1 else (h[i] < zgBot):
                    stStage = 4
            elif l[i] <= ceLvl <= h[i] and ((slLvl < ceLvl) if stDir == 1 else (slLvl > ceLvl)):
                risk = max(abs(ceLvl - slLvl), 1e-9)
                wt = (stDir == 1 and htfUp[i // LTF_PER_HTF]) or (stDir == -1 and not htfUp[i // LTF_PER_HTF])
                tp = ceLvl + stDir * risk * (RRW if wt else RRA)
                assert (tp > ceLvl > slLvl) if stDir == 1 else (tp < ceLvl < slLvl), "bad TP/SL geometry"
                stats['ENTRY'] += 1
                stats['LONG' if stDir == 1 else 'SHORT'] += 1
                stats['WT'] += 1 if wt else 0
                waits.append(i - flipBar); risks.append(risk / ceLvl * 100)
                stStage, stDir = 0, 0

    return stats, waits, risks, N


for seed in (11, 23, 42, 77):
    s, w, r, N = run(seed)
    print(f"seed {seed:>3} | {N/(12*24):5.0f}d | LS {s['LS']:3d} -> MSS {s['MSS']:3d} -> IFVG {s['IFVG']:3d} "
          f"-> entries {s['ENTRY']:3d} (L{s['LONG']}/S{s['SHORT']}, with-trend {s['WT']}) "
          f"| structfail {s['STRUCTFAIL']:3d} inval {s['INVAL']:2d} | one entry/{N/max(s['ENTRY'],1):.0f} bars "
          f"| flip->tap med {st.median(w) if w else 0:.0f} bars | risk med {st.median(r) if r else 0:.2f}%")
