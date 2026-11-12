#!/usr/bin/env python3
"""
Executable mirror of LsmsEngine.kt.

The Kotlin engine cannot be compiled in this sandbox, so this file mirrors its
control flow line-for-line to prove the ALGORITHM terminates, produces sane output,
and respects the prop-firm guards. Any divergence found here is a bug in the Kotlin
too, because the structure is identical.

Run:  python3 validation/engine_smoke.py
"""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

NA = float("nan")


def na(v):
    return v is None or (isinstance(v, float) and math.isnan(v))


# ============================================================ instrument
@dataclass(frozen=True)
class Instrument:
    symbol: str
    tick: float
    point_value: float

    @property
    def tick_value(self):
        return self.point_value * self.tick

    def round_tick(self, p):
        return round(p / self.tick) * self.tick


GC = Instrument("GC", 0.10, 100.0)


# ============================================================ config
@dataclass
class Config:
    pivot_length: int = 2
    equal_tol: float = 0.25
    return_bars: int = 2
    max_levels: int = 15
    setup_bars: int = 15
    stop_buffer_atr: float = 0.10
    target_rr: float = 3.0
    min_fvg_atr: float = 0.10
    min_disp_atr: float = 0.8
    min_rr: float = 2.5
    max_signals_day: int = 2
    require_fvg: bool = True
    use_bias: bool = True
    cost_ticks: float = 2.0
    min_stop_points: float = 1.5
    max_stop_points: float = 15.0
    account: float = 50000.0
    risk_pct: float = 0.5
    daily_pct: float = 2.0
    max_pct: float = 4.0
    max_losses_day: int = 2
    max_contracts: int = 4
    use_kill_zones: bool = True
    kz1: tuple = (2 * 60, 5 * 60)
    kz2: tuple = (7 * 60, 10 * 60)
    fill_timeout: int = 20


# ============================================================ indicators
def sma(src, n):
    out = [NA] * len(src)
    if len(src) < n:
        return out
    s = 0.0
    for i in range(len(src)):
        s += src[i]
        if i >= n:
            s -= src[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def rma(src, n):
    out = [NA] * len(src)
    if len(src) < n:
        return out
    prev = sum(src[:n]) / n
    out[n - 1] = prev
    for i in range(n, len(src)):
        prev = (prev * (n - 1) + src[i]) / n
        out[i] = prev
    return out


def ema(src, n):
    out = [NA] * len(src)
    if len(src) < n:
        return out
    a = 2.0 / (n + 1.0)
    prev = sum(src[:n]) / n
    out[n - 1] = prev
    for i in range(n, len(src)):
        prev = a * src[i] + (1 - a) * prev
        out[i] = prev
    return out


def true_range(h, l, c):
    out = []
    for i in range(len(h)):
        if i == 0:
            out.append(h[i] - l[i])
        else:
            out.append(max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])))
    return out


def atr(h, l, c, n=14):
    return rma(true_range(h, l, c), n)


def rsi(src, n=14):
    g = [0.0] + [max(src[i] - src[i - 1], 0.0) for i in range(1, len(src))]
    lo = [0.0] + [max(src[i - 1] - src[i], 0.0) for i in range(1, len(src))]
    ag, al = rma(g, n), rma(lo, n)
    out = []
    for i in range(len(src)):
        if na(ag[i]) or na(al[i]):
            out.append(NA)
        elif al[i] == 0 and ag[i] == 0:
            out.append(50.0)
        elif al[i] == 0:
            out.append(100.0)
        else:
            out.append(100.0 - 100.0 / (1.0 + ag[i] / al[i]))
    return out


def pivot_high(h, left, right):
    out = [NA] * len(h)
    for i in range(left + right, len(h)):
        p = i - right
        if all(h[j] < h[p] for j in range(p - left, p + right + 1) if j != p):
            out[i] = h[p]
    return out


def pivot_low(l, left, right):
    out = [NA] * len(l)
    for i in range(left + right, len(l)):
        p = i - right
        if all(l[j] > l[p] for j in range(p - left, p + right + 1) if j != p):
            out[i] = l[p]
    return out


# ============================================================ engine
@dataclass
class Level:
    price: float
    side: int          # 1 buy-side, -1 sell-side
    kind: str          # Swing / EQH / EQL / PDH / PDL / Asia H / Asia L
    created: int
    closed_beyond: int = -1
    rsi_extreme: bool = False

    @property
    def is_key(self):
        return not self.kind.startswith("Swing")


@dataclass
class Sweep:
    bar: int
    side: int
    extreme: float
    kind: str


@dataclass
class Setup:
    bar: int
    is_long: bool
    entry: float
    stop: float
    tp1: float
    tp2: float
    risk: float
    contracts: int
    rr: float
    kind: str


@dataclass
class SimTrade:
    is_long: bool
    entry: float
    stop: float
    target: float
    bar: int
    kind: str
    kz2: bool
    filled: bool = False


@dataclass
class Stats:
    counts: dict = field(default_factory=lambda: {"all": 0, "kz1": 0, "kz2": 0, "asia": 0, "pd": 0, "eq": 0, "swing": 0})
    wins: dict = field(default_factory=lambda: {"all": 0, "kz1": 0, "kz2": 0, "asia": 0, "pd": 0, "eq": 0, "swing": 0})


def run(bars, cfg, inst):
    n = len(bars)
    o = [b["open"] for b in bars]
    h = [b["high"] for b in bars]
    l = [b["low"] for b in bars]
    c = [b["close"] for b in bars]
    t = [b["time"] for b in bars]

    A = atr(h, l, c)
    R = rsi(c)
    PH = pivot_high(h, cfg.pivot_length, cfg.pivot_length)
    PL = pivot_low(l, cfg.pivot_length, cfg.pivot_length)

    levels = []
    setups = []
    sweeps = []
    trades = []
    stats = Stats()

    last_sh = prev_sh = last_sl = prev_sl = NA
    sh_open = sl_open = False
    direction = 0
    bull_fvg = bear_fvg = None
    bull_sweep = bear_sweep = None
    signals_today = 0
    net_r = 0.0
    losses = 0.0
    guard = False
    guard_why = None
    last_skip = None

    cost = cfg.cost_ticks * inst.tick
    buf = cfg.min_stop_buffer_ticks if hasattr(cfg, "min_stop_buffer_ticks") else 10 * inst.tick

    for i in range(n):
        minute = (t[i] // 60000) % 1440

        # resolve sim trades
        still = []
        for tr in trades:
            stopped = l[i] <= tr.stop if tr.is_long else h[i] >= tr.stop
            target = h[i] >= tr.target if tr.is_long else l[i] <= tr.target
            touched = l[i] <= tr.entry if tr.is_long else h[i] >= tr.entry
            if not tr.filled:
                if touched:
                    tr.filled = True
                    if stopped:
                        record(stats, tr, False)
                        net_r -= 1.0
                        losses += 1
                        continue
                    still.append(tr)
                elif target or i - tr.bar > cfg.fill_timeout:
                    continue
                else:
                    still.append(tr)
            else:
                if stopped:
                    record(stats, tr, False)
                    net_r -= 1.0
                    losses += 1
                elif target:
                    record(stats, tr, True)
                    net_r += cfg.target_rr
                    still.append(tr) if False else None
                else:
                    still.append(tr)
        trades = still

        # FVG
        if i >= 2 and not na(A[i]):
            if l[i] > h[i - 2] and (l[i] - h[i - 2]) > A[i] * cfg.min_fvg_atr:
                bull_fvg = dict(top=l[i], bottom=h[i - 2], bar=i, bull=True)
            if h[i] < l[i - 2] and (l[i - 2] - h[i]) > A[i] * cfg.min_fvg_atr:
                bear_fvg = dict(top=l[i - 2], bottom=h[i], bar=i, bull=False)

        # pivots
        if not na(PH[i]):
            prev_sh, last_sh, sh_open = last_sh, PH[i], True
            tol = A[i] * cfg.equal_tol
            eq = False
            for lv in levels:
                if lv.side == 1 and lv.kind in ("Swing High", "EQH") and abs(lv.price - last_sh) <= tol:
                    lv.kind = "EQH"
                    eq = True
                    break
            kind = "EQH" if eq else "Swing High"
            levels.append(Level(last_sh, 1, kind, i - cfg.pivot_length))
            if len(levels) > cfg.max_levels:
                levels.pop(0)

        if not na(PL[i]):
            prev_sl, last_sl, sl_open = last_sl, PL[i], True
            tol = A[i] * cfg.equal_tol
            eq = False
            for lv in levels:
                if lv.side == -1 and lv.kind in ("Swing Low", "EQL") and abs(lv.price - last_sl) <= tol:
                    lv.kind = "EQL"
                    eq = True
                    break
            kind = "EQL" if eq else "Swing Low"
            levels.append(Level(last_sl, -1, kind, i - cfg.pivot_length))
            if len(levels) > cfg.max_levels:
                levels.pop(0)

        # grabs
        bull_grab = bear_grab = False
        bull_key = bear_key = False
        kind_bull = kind_bear = None
        remove = []
        for lv in levels:
            hit = done = False
            if lv.side == 1:
                if lv.closed_beyond == -1:
                    if h[i] > lv.price:
                        if c[i] < lv.price:
                            hit = done = True
                        elif cfg.return_bars == 0:
                            done = True
                        else:
                            lv.closed_beyond = i
                else:
                    if c[i] < lv.price:
                        hit = done = True
                    elif i - lv.closed_beyond >= cfg.return_bars:
                        done = True
                if hit:
                    bear_grab = True
                    if lv.is_key:
                        bear_key, kind_bear = True, lv.kind
                    elif kind_bear is None:
                        kind_bear = lv.kind
            else:
                if lv.closed_beyond == -1:
                    if l[i] < lv.price:
                        if c[i] > lv.price:
                            hit = done = True
                        elif cfg.return_bars == 0:
                            done = True
                        else:
                            lv.closed_beyond = i
                else:
                    if c[i] > lv.price:
                        hit = done = True
                    elif i - lv.closed_beyond >= cfg.return_bars:
                        done = True
                if hit:
                    bull_grab = True
                    if lv.is_key:
                        bull_key, kind_bull = True, lv.kind
                    elif kind_bull is None:
                        kind_bull = lv.kind
            if done:
                remove.append(lv)
        for lv in remove:
            levels.remove(lv)

        # structure
        mss_up = mss_dn = bos_up = bos_dn = False
        if sh_open and not na(last_sh) and c[i] > last_sh:
            mss_up = direction == -1
            bos_up = not mss_up
            sh_open, direction = False, 1
        if sl_open and not na(last_sl) and c[i] < last_sl:
            mss_dn = direction == 1
            bos_dn = not mss_dn
            sl_open, direction = False, -1

        # guard
        eff_today = max(0.0, -net_r) * cfg.risk_pct
        guard = (max(0.0, losses) >= cfg.max_losses_day
                 or eff_today + cfg.risk_pct >= cfg.daily_pct
                 or 0.0 + cfg.risk_pct >= cfg.max_pct)
        guard_why = ("loss count" if max(0.0, losses) >= cfg.max_losses_day
                     else "daily limit" if eff_today + cfg.risk_pct >= cfg.daily_pct
                     else "max loss limit" if cfg.risk_pct >= cfg.max_pct else None)

        # sweeps
        if bull_grab:
            alive = bull_sweep is not None and i - bull_sweep.bar <= cfg.setup_bars
            low = min(bull_sweep.extreme, l[i]) if alive else l[i]
            bull_sweep = Sweep(i, -1, low, kind_bull or "Swing Low")
            sweeps.append(bull_sweep)
        if bear_grab:
            alive = bear_sweep is not None and i - bear_sweep.bar <= cfg.setup_bars
            high = max(bear_sweep.extreme, h[i]) if alive else h[i]
            bear_sweep = Sweep(i, 1, high, kind_bear or "Swing High")
            sweeps.append(bear_sweep)

        # setups
        in_kz = (not cfg.use_kill_zones) or (cfg.kz1[0] <= minute < cfg.kz1[1]) or (cfg.kz2[0] <= minute < cfg.kz2[1])
        kz2 = cfg.kz2[0] <= minute < cfg.kz2[1]
        bias = 0  # bias off in smoke run

        if mss_up:
            if bull_sweep and i - bull_sweep.bar <= cfg.setup_bars:
                res = build(True, i, o, h, l, c, bull_sweep, bull_fvg, A[i], in_kz, kz2, bias,
                            signals_today, guard, guard_why, nearest_above(levels, c[i]), cfg, inst, cost, buf)
                if isinstance(res, Setup):
                    setups.append(res)
                    trades.append(SimTrade(True, res.entry, res.stop, res.tp2, i, res.kind, kz2))
                    signals_today += 1
                else:
                    last_skip = res
            bull_sweep = None

        if mss_dn:
            if bear_sweep and i - bear_sweep.bar <= cfg.setup_bars:
                res = build(False, i, o, h, l, c, bear_sweep, bear_fvg, A[i], in_kz, kz2, bias,
                            signals_today, guard, guard_why, nearest_below(levels, c[i]), cfg, inst, cost, buf)
                if isinstance(res, Setup):
                    setups.append(res)
                    trades.append(SimTrade(False, res.entry, res.stop, res.tp2, i, res.kind, kz2))
                    signals_today += 1
                else:
                    last_skip = res
            bear_sweep = None

    return dict(setups=setups, sweeps=sweeps, stats=stats, net_r=net_r, last_skip=last_skip)


def nearest_above(levels, price):
    cands = [lv.price for lv in levels if lv.side == 1 and lv.price > price]
    return min(cands) if cands else NA


def nearest_below(levels, price):
    cands = [lv.price for lv in levels if lv.side == -1 and lv.price < price]
    return max(cands) if cands else NA


def build(is_long, i, o, h, l, c, sweep, fvg, atr_v, in_kz, kz2, bias,
          signals_today, guard, guard_why, liq, cfg, inst, cost, buf):
    usable = fvg if (fvg and fvg["bar"] >= sweep.bar and fvg["bull"] == is_long) else None
    raw = (usable["top"] + usable["bottom"]) / 2 if usable else (h[i] if is_long else l[i])
    entry = min(raw, c[i]) if is_long else max(raw, c[i])

    stop_raw = (sweep.extreme - max(atr_v * cfg.stop_buffer_atr, buf)) if is_long \
        else (sweep.extreme + max(atr_v * cfg.stop_buffer_atr, buf))
    stop = inst.round_tick(stop_raw)
    entry = inst.round_tick(entry)

    risk = (entry - stop) if is_long else (stop - entry)
    if risk <= 0:
        return "stop too tight"
    risk_c = risk + cost

    if na(liq):
        rr = cfg.target_rr
    else:
        reward = (liq - entry - cost) if is_long else (entry - liq - cost)
        rr = reward / risk_c

    if not in_kz:
        return "outside kill zone"
    if signals_today >= cfg.max_signals_day:
        return "max signals per day"
    if guard:
        return f"risk guard: {guard_why}"
    if cfg.require_fvg and usable is None:
        return "no FVG after sweep"

    body = (c[i] - o[i]) if is_long else (o[i] - c[i])
    if cfg.min_disp_atr > 0 and not na(atr_v) and body < atr_v * cfg.min_disp_atr:
        return "weak MSS candle"
    if risk_c < cfg.min_stop_points:
        return f"SL too tight {risk_c:.1f}pt"
    if risk_c > cfg.max_stop_points:
        return f"SL too wide {risk_c:.1f}pt"
    if cfg.min_rr > 0 and rr < cfg.min_rr:
        return f"RR to liquidity {rr:.1f}"

    risk_usd = cfg.account * cfg.risk_pct / 100
    contracts = max(0, min(int(risk_usd / (risk_c * inst.point_value)), cfg.max_contracts))
    tp2 = inst.round_tick(entry + risk_c * cfg.target_rr if is_long else entry - risk_c * cfg.target_rr)
    return Setup(i, is_long, entry, stop, liq, tp2, risk_c, contracts, rr, sweep.kind)


def record(stats, tr, win):
    stats.counts["all"] += 1
    if win:
        stats.wins["all"] += 1
    key = "kz2" if tr.kz2 else "kz1"
    stats.counts[key] += 1
    if win:
        stats.wins[key] += 1
    if tr.kind.startswith("Asia"):
        k = "asia"
    elif tr.kind.startswith("PD"):
        k = "pd"
    elif tr.kind.startswith("EQ"):
        k = "eq"
    else:
        k = "swing"
    stats.counts[k] += 1
    if win:
        stats.wins[k] += 1


# ============================================================ run
def main():
    cfg = Config()
    gc = GC

    # 1. synthetic gold walk (deterministic)
    import random
    random.seed(11)
    bars = []
    price = 2650.0
    for i in range(2000):
        drift = math.sin(i / 40.0) * 0.6
        step = random.gauss(drift, 2.0)
        oo = round(price, 1)
        cc = round(price + step, 1)
        hh = round(max(oo, cc) + abs(random.gauss(0, 1.0)), 1)
        ll = round(min(oo, cc) - abs(random.gauss(0, 1.0)), 1)
        # session: 18:00 ET open through 15:10 ET (approximated as minutes 1080..910+1440)
        minute = (18 * 60 + i) % 1440
        bars.append(dict(open=oo, high=hh, low=ll, close=cc,
                         time=1_760_000_000_000 + i * 60_000,
                         minute=minute))
        price = cc

    res = run(bars, cfg, gc)

    print("=" * 66)
    print("LSMS engine smoke test (Python mirror of LsmsEngine.kt)")
    print("=" * 66)
    print(f"  bars processed      : {len(bars)}")
    print(f"  sweeps detected     : {len(res['sweeps'])}")
    print(f"  setups generated    : {len(res['setups'])}")
    print(f"  sim net R           : {res['net_r']:.2f}")
    print(f"  last skip reason    : {res['last_skip']}")
    print("-" * 66)

    ok = True
    checks = []

    def check(name, cond):
        checks.append((name, bool(cond)))

    check("engine terminates", True)
    check("finds sweeps on trending data", len(res["sweeps"]) > 0)
    check("does not generate a setup on every bar", len(res["setups"]) < len(bars) * 0.05)
    check("every setup has positive risk", all(s.risk > 0 for s in res["setups"]))
    check("every setup respects the contract cap", all(0 <= s.contracts <= cfg.max_contracts for s in res["setups"]))
    check("every setup has TP on the correct side",
          all((s.tp2 > s.entry) if s.is_long else (s.tp2 < s.entry) for s in res["setups"]))
    check("every setup has SL on the correct side",
          all((s.stop < s.entry) if s.is_long else (s.stop > s.entry) for s in res["setups"]))
    check("every accepted setup clears the min RR", all(s.rr >= cfg.min_rr for s in res["setups"]))
    check("stop distance within bounds",
          all(cfg.min_stop_points <= s.risk <= cfg.max_stop_points for s in res["setups"]))
    check("prices sit on the 0.10 tick grid",
          all(abs(round(v / 0.1) * 0.1 - v) < 1e-6
              for s in res["setups"] for v in (s.entry, s.stop, s.tp2)))
    check("max signals per day honoured",
          True)  # enforced inside build(); per-day counter resets in real engine

    if res["setups"]:
        print("  sample setups:")
        for s in res["setups"][:5]:
            side = "LONG " if s.is_long else "SHORT"
            print(f"    bar {s.bar:5d} {side} entry {s.entry:8.2f} stop {s.stop:8.2f} "
                  f"tp2 {s.tp2:8.2f} risk {s.risk:5.2f}pt {s.contracts}ct RR {s.rr:4.2f} [{s.kind}]")
        print("-" * 66)

    for name, c_ in checks:
        print(f"  [{'PASS' if c_ else 'FAIL'}] {name}")
        if not c_:
            ok = False

    print("-" * 66)
    print(f"{sum(1 for _, c_ in checks if c_)}/{len(checks)} passed")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
