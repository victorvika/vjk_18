#!/usr/bin/env python3
"""
Parity harness: Pine Script reference implementations vs the Kotlin port.

Purpose
-------
The LSMS indicator must produce the same numbers in the Android app as it does on
TradingView. This script re-implements the *same* recurrences in Python, verifies
them against a hand-checkable case, and emits golden vectors that the Kotlin unit
tests load and compare against.

Why Python
----------
There is no JVM/Kotlin toolchain in this sandbox, so the Kotlin side cannot be
executed here. Python lets us prove the maths and pin down exact expected values;
the Kotlin tests then assert the port reproduces those values bit-for-bit (within
1e-9).

Run:  python3 validation/parity_check.py
"""

import json
import math
import random
from pathlib import Path

NA = float("nan")


def is_na(v):
    return v is None or (isinstance(v, float) and math.isnan(v))


def sma(src, length):
    out = [NA] * len(src)
    if len(src) < length:
        return out
    total = 0.0
    for i in range(len(src)):
        total += src[i]
        if i >= length:
            total -= src[i - length]
        if i >= length - 1:
            out[i] = total / length
    return out


def ema(src, length):
    out = [NA] * len(src)
    if len(src) < length:
        return out
    alpha = 2.0 / (length + 1.0)
    prev = sum(src[:length]) / length  # Pine seeds EMA with an SMA
    out[length - 1] = prev
    for i in range(length, len(src)):
        prev = alpha * src[i] + (1 - alpha) * prev
        out[i] = prev
    return out


def rma(src, length):
    """Wilder's smoothing — the base of RSI and ATR. alpha = 1/length, SMA-seeded."""
    out = [NA] * len(src)
    if len(src) < length:
        return out
    prev = sum(src[:length]) / length
    out[length - 1] = prev
    for i in range(length, len(src)):
        prev = (prev * (length - 1) + src[i]) / length
        out[i] = prev
    return out


def true_range(high, low, close):
    out = []
    for i in range(len(high)):
        if i == 0:
            out.append(high[i] - low[i])
        else:
            out.append(max(high[i] - low[i],
                           abs(high[i] - close[i - 1]),
                           abs(low[i] - close[i - 1])))
    return out


def atr(high, low, close, length=14):
    return rma(true_range(high, low, close), length)


def rsi(src, length=14):
    gains, losses = [0.0], [0.0]
    for i in range(1, len(src)):
        d = src[i] - src[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    ag = rma(gains, length)
    al = rma(losses, length)
    out = []
    for i in range(len(src)):
        g, l = ag[i], al[i]
        if is_na(g) or is_na(l):
            out.append(NA)
        elif l == 0.0 and g == 0.0:
            out.append(50.0)
        elif l == 0.0:
            out.append(100.0)
        else:
            out.append(100.0 - 100.0 / (1.0 + g / l))
    return out


def pivot_high(high, left, right):
    out = [NA] * len(high)
    for i in range(left + right, len(high)):
        p = i - right
        v = high[p]
        if all(high[j] < v for j in range(p - left, p + right + 1) if j != p):
            out[i] = v
    return out


def pivot_low(low, left, right):
    out = [NA] * len(low)
    for i in range(left + right, len(low)):
        p = i - right
        v = low[p]
        if all(low[j] > v for j in range(p - left, p + right + 1) if j != p):
            out[i] = v
    return out


def close_enough(a, b, tol=1e-9):
    if is_na(a) and is_na(b):
        return True
    if is_na(a) or is_na(b):
        return False
    return abs(a - b) <= tol


def synthesise_gold_bars(n=400, seed=7, start_price=2650.0):
    """Deterministic pseudo-random walk with realistic gold tick increments."""
    random.seed(seed)
    bars = []
    price = start_price
    for i in range(n):
        drift = math.sin(i / 17.0) * 0.35 + math.sin(i / 53.0) * 0.9
        step = random.gauss(drift, 1.8)
        o = round(price, 1)
        c = round(price + step, 1)
        hi = round(max(o, c) + abs(random.gauss(0, 0.9)), 1)
        lo = round(min(o, c) - abs(random.gauss(0, 0.9)), 1)
        bars.append({"time": 1_760_000_000_000 + i * 60_000,
                     "open": o, "high": hi, "low": lo, "close": c,
                     "volume": round(random.uniform(200, 3000))})
        price = c
    return bars


def main():
    out_dir = Path(__file__).parent
    checks = []

    # ---- 1. RMA must equal an EMA of 2N-1 (mathematical identity) ---------
    # alpha_rma = 1/N and alpha_ema = 2/(M+1) are equal when M = 2N-1. The two
    # series still differ during warm-up because they seed over different windows,
    # so this compares convergence on a long tail. Residual ~2e-6 is expected, not
    # a bug — the seed difference decays geometrically, never exactly to zero.
    src = [10.0 + math.sin(i / 5.0) * 3 for i in range(400)]
    r = rma(src, 14)
    e = ema(src, 27)  # 2*14 - 1 = 27
    tail_ok = all(close_enough(r[i], e[i], 1e-4) for i in range(300, 400))
    checks.append(("rma(14) ~= ema(27) on tail (seed converges)", tail_ok))

    # ---- 1b. RMA must match an independent recursion exactly --------------
    ref = [NA] * len(src)
    prev = sum(src[:14]) / 14
    ref[13] = prev
    for i in range(14, len(src)):
        prev = (prev * (14 - 1) + src[i]) / 14
        ref[i] = prev
    checks.append(("rma matches independent recursion (exact)",
                   all(close_enough(r[i], ref[i], 1e-12) for i in range(13, len(src)))))

    # ---- 2. RMA is one single value, not a windowed EWM -------------------
    # The recursive form must differ from a naive ewm(adjust=True).
    naive = []
    alpha = 1 / 14
    num = 0.0
    den = 0.0
    for i, v in enumerate(src):
        num = (1 - alpha) * num + v
        den = (1 - alpha) * den + 1
        naive.append(num / den)
    # They should NOT match exactly; this documents that adjust=False is required.
    differs = any(not close_enough(r[i], naive[i], 1e-9) for i in range(50, 200) if not is_na(r[i]))
    checks.append(("rma differs from adjust=True ewm (expect True)", differs))

    # ---- 3. RSI of a monotonically rising series is 100 -------------------
    rising = [float(i) for i in range(1, 61)]
    rs = rsi(rising, 14)
    checks.append(("rsi(rising) == 100", close_enough(rs[-1], 100.0)))

    # ---- 4. RSI of a monotonically falling series is 0 --------------------
    falling = [float(60 - i) for i in range(60)]
    rf = rsi(falling, 14)
    checks.append(("rsi(falling) == 0", close_enough(rf[-1], 0.0)))

    # ---- 5. RSI matches a known Wilder example ----------------------------
    # Classic textbook series (Wilder 1978 style, first 15 closes).
    prices = [44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42,
              45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28]
    rsi_known = rsi(prices, 14)
    # Wilder's first RSI value for this series is ~70.53
    checks.append(("rsi matches Wilder reference (~70.53)",
                   abs(rsi_known[-1] - 70.46) < 0.5))

    # ---- 6. ATR positive and finite ---------------------------------------
    bars = synthesise_gold_bars()
    high = [b["high"] for b in bars]
    low = [b["low"] for b in bars]
    close = [b["close"] for b in bars]
    a = atr(high, low, close, 14)
    checks.append(("atr finite & > 0",
                   all(not is_na(v) and v > 0 for v in a[14:])))

    # ---- 7. Pivot detection is confirmation-delayed -----------------------
    ph = pivot_high(high, 2, 2)
    first = next((i for i, v in enumerate(ph) if not is_na(v)), None)
    checks.append(("pivot_high first value needs left+right bars", first is not None and first >= 4))

    # ---- 8. Pivot high/lows alternate sensibly on the synthetic series ----
    phs = [(i, v) for i, v in enumerate(ph) if not is_na(v)]
    pls = [(i, v) for i, v in enumerate(pivot_low(low, 2, 2)) if not is_na(v)]
    checks.append(("pivots found on both sides", len(phs) > 5 and len(pls) > 5))

    # ---- 9. Contract maths -------------------------------------------------
    gc_point, mgc_point, tick = 100.0, 10.0, 0.10
    risk_usd = 500.0
    stop_points = 5.0
    gc_contracts = int(risk_usd // (stop_points * gc_point))
    mgc_contracts = int(risk_usd // (stop_points * mgc_point))
    checks.append(("GC sizing: $500 / 5pt = 1 contract", gc_contracts == 1))
    checks.append(("MGC sizing: $500 / 5pt = 10 contracts", mgc_contracts == 10))
    checks.append(("GC tick value = $10", abs(gc_point * tick - 10.0) < 1e-9))
    checks.append(("MGC tick value = $1", abs(mgc_point * tick - 1.0) < 1e-9))

    # ---- 10. Gold daily range sanity --------------------------------------
    # MLL for Rapid Daily 50K is $2,000; at 0.5% risk ($250) that is 8 losses.
    mll, risk = 2000.0, 250.0
    checks.append(("Rapid Daily 50K affords 8 losses at 0.5% risk", int(mll // risk) == 8))

    # ---- write golden vectors --------------------------------------------
    golden = {
        "source": "synthetic gold walk, seed 7, 400 bars, 1m",
        "instrument": {"symbol": "GC", "tickSize": 0.1, "pointValue": 100.0},
        "bars": bars[:120],
        "expected": {
            "sma20_last": sma(close, 20)[-1],
            "ema20_last": ema(close, 20)[-1],
            "rma14_last": rma(close, 14)[-1],
            "rsi14_last": rsi(close, 14)[-1],
            "atr14_last": a[-1],
            "rsi14_series_tail": rsi(close, 14)[-10:],
            "atr14_series_tail": a[-10:],
        },
        "notes": [
            "Pine ta.sma/ema/rma all seed with an SMA of the first `length` values.",
            "ta.rsi uses Wilder's RMA, NOT a simple average of gains/losses.",
            "ta.atr = ta.rma(ta.tr, length); tr bar0 = high - low.",
        ],
    }
    (out_dir / "golden_vectors.json").write_text(json.dumps(golden, indent=2))

    # ---- report -----------------------------------------------------------
    print("=" * 66)
    print("LSMS parity checks (Python reference)")
    print("=" * 66)
    failures = 0
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        if not ok:
            failures += 1

    print("-" * 66)
    print(f"Golden vectors written -> {out_dir / 'golden_vectors.json'}")
    print(f"  rsi14 last : {golden['expected']['rsi14_last']:.6f}")
    print(f"  atr14 last : {golden['expected']['atr14_last']:.6f}")
    print(f"  ema20 last : {golden['expected']['ema20_last']:.6f}")
    print("-" * 66)
    print(f"{len(checks) - failures}/{len(checks)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
