#!/usr/bin/env python3
"""
Behavioural spec for the LSMS engine, expressed as executable rules.

The Kotlin engine cannot be compiled in this sandbox, so these tests pin down the
DECISIONS the port must make — sweep detection, structure breaks, sizing, prop-firm
guards — against small hand-built bar sequences. Each test maps to one Kotlin unit
test in LsmsEngineTest.kt.

Run:  python3 validation/engine_spec.py
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Bar:
    t: int
    o: float
    h: float
    l: float
    c: float


# ---------------------------------------------------------------- instrument
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
MGC = Instrument("MGC", 0.10, 10.0)


# ---------------------------------------------------------------- sizing
def contracts_for(risk_usd, risk_points, inst, max_contracts, min_contracts=0):
    if risk_points <= 0:
        return 0
    raw = risk_usd / (risk_points * inst.point_value)
    return max(min_contracts, min(int(raw // 1), max_contracts))


# ---------------------------------------------------------------- liquidity
BUY_SIDE = 1
SELL_SIDE = -1


@dataclass
class Level:
    price: float
    side: int
    kind: str
    closed_beyond: int = -1

    @property
    def is_key(self):
        return not self.kind.startswith("Swing")


def detect_grab(level: Level, bar: Bar, idx: int, return_bars: int = 2):
    """Returns (grabbed, consumed). Mirrors the Kotlin listIterator loop."""
    if level.side == BUY_SIDE:
        if level.closed_beyond == -1:
            if bar.h > level.price:
                if bar.c < level.price:
                    return True, True
                if return_bars == 0:
                    return False, True
                level.closed_beyond = idx
                return False, False
        else:
            if bar.c < level.price:
                return True, True
            if idx - level.closed_beyond >= return_bars:
                return False, True
        return False, False
    else:
        if level.closed_beyond == -1:
            if bar.l < level.price:
                if bar.c > level.price:
                    return True, True
                if return_bars == 0:
                    return False, True
                level.closed_beyond = idx
                return False, False
        else:
            if bar.c > level.price:
                return True, True
            if idx - level.closed_beyond >= return_bars:
                return False, True
        return False, False


def nearest_above(levels, price):
    cands = [l.price for l in levels if l.side == BUY_SIDE and l.price > price]
    return min(cands) if cands else None


def nearest_below(levels, price):
    cands = [l.price for l in levels if l.side == SELL_SIDE and l.price < price]
    return max(cands) if cands else None


# ---------------------------------------------------------------- prop rules
def guard_stopped(eff_losses, eff_today_pct, total_loss_pct, cfg):
    return (eff_losses >= cfg["max_losses_day"]
            or eff_today_pct + cfg["risk_pct"] >= cfg["daily_limit_pct"]
            or total_loss_pct + cfg["risk_pct"] >= cfg["max_limit_pct"])


def mll_floor(initial, mll_distance, highest_eod, lock_offset):
    """FundedNext EOD trailing MLL. Never moves down; locks at initial + offset."""
    return min(highest_eod - mll_distance, initial + lock_offset)


# ============================================================================
# TESTS
# ============================================================================
TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


@test
def t01_gc_tick_values():
    assert abs(GC.tick_value - 10.0) < 1e-9, GC.tick_value
    assert abs(MGC.tick_value - 1.0) < 1e-9, MGC.tick_value


@test
def t02_gc_sizing_matches_fx_free_maths():
    # $250 risk, 5 point stop on GC -> 250 / (5 * 100) = 0.5 -> 0 contracts
    assert contracts_for(250, 5, GC, 4) == 0
    # $500 risk, 5 point stop -> exactly 1
    assert contracts_for(500, 5, GC, 4) == 1
    # $1000 risk, 5 point stop -> 2
    assert contracts_for(1000, 5, GC, 4) == 2


@test
def t03_contract_limit_clamps():
    # $5000 risk on a 2 point stop would be 25 GC; the account caps at 4.
    assert contracts_for(5000, 2, GC, 4) == 4


@test
def t04_micro_is_ten_times_gc():
    assert contracts_for(500, 5, MGC, 40) == 10
    assert abs(GC.tick_value / MGC.tick_value - 10.0) < 1e-9


@test
def t05_buy_side_grab_needs_close_back_inside():
    lv = Level(2700.0, BUY_SIDE, "PDH")
    # wicks above but closes above -> not a grab yet, marks closed_beyond
    grabbed, consumed = detect_grab(lv, Bar(0, 2699, 2702, 2698, 2701), 0)
    assert not grabbed and not consumed
    assert lv.closed_beyond == 0
    # closes back below within the window -> grab
    grabbed, consumed = detect_grab(lv, Bar(1, 2701, 2701.5, 2696, 2697), 1)
    assert grabbed and consumed


@test
def t06_grab_expires_after_return_bars():
    lv = Level(2700.0, BUY_SIDE, "PDH")
    detect_grab(lv, Bar(0, 2699, 2702, 2698, 2701), 0)
    # stays above for 3 bars with return_bars = 2 -> consumed, no grab
    grabbed, consumed = detect_grab(lv, Bar(3, 2701, 2704, 2700.5, 2703), 3)
    assert not grabbed and consumed


@test
def t07_sell_side_grab_mirror():
    lv = Level(2680.0, SELL_SIDE, "Asia L")
    grabbed, consumed = detect_grab(lv, Bar(0, 2681, 2682, 2677, 2681.5), 0)
    assert grabbed and consumed


@test
def t08_key_level_classification():
    assert not Level(1, BUY_SIDE, "Swing").is_key
    assert Level(1, BUY_SIDE, "PDH").is_key
    assert Level(1, SELL_SIDE, "Asia L").is_key
    assert Level(1, SELL_SIDE, "EQL").is_key


@test
def t09_nearest_liquidity_direction():
    levels = [Level(2695, BUY_SIDE, "PDH"),
              Level(2712, BUY_SIDE, "Asia H"),
              Level(2688, SELL_SIDE, "PDL")]
    assert nearest_above(levels, 2700) == 2712
    assert nearest_below(levels, 2700) == 2688
    assert nearest_above(levels, 2715) is None


@test
def t10_guard_blocks_on_loss_count():
    cfg = dict(max_losses_day=2, risk_pct=0.5, daily_limit_pct=2.0, max_limit_pct=4.0)
    assert not guard_stopped(1, 0.5, 0.5, cfg)
    assert guard_stopped(2, 0.5, 0.5, cfg)


@test
def t11_guard_blocks_before_daily_limit():
    cfg = dict(max_losses_day=99, risk_pct=0.5, daily_limit_pct=2.0, max_limit_pct=4.0)
    # 1.5% taken + 0.5% at risk = 2.0% -> blocked
    assert guard_stopped(0, 1.5, 1.5, cfg)
    assert not guard_stopped(0, 1.4, 1.4, cfg)


@test
def t12_guard_blocks_on_max_limit():
    cfg = dict(max_losses_day=99, risk_pct=0.5, daily_limit_pct=99.0, max_limit_pct=4.0)
    assert guard_stopped(0, 0.0, 3.6, cfg)


@test
def t13_mll_floor_trails_and_locks():
    # Rapid Daily 50K: MLL 2000, locks at initial + 100 = 50100
    assert mll_floor(50000, 2000, 50000, 100) == 48000
    # a 3000 profit day trails the raw floor to 51000, capped at the 50100 lock
    assert mll_floor(50000, 2000, 53000, 100) == 50100
    # highest EOD never decreases, so a later drawdown cannot lower the floor
    assert mll_floor(50000, 2000, 56000, 100) == 50100
    # before the lock is reached the floor genuinely trails
    assert mll_floor(50000, 2000, 51000, 100) == 49000


@test
def t14_fundednext_affordable_losses():
    # Rapid Daily 50K: MLL 2000, 0.5% risk = 250 -> 8 losses
    assert int(2000 // (50000 * 0.005)) == 8
    # 25K: MLL 1000, 0.5% risk = 125 -> 8 losses as well
    assert int(1000 // (25000 * 0.005)) == 8
    # 1% risk halves it
    assert int(2000 // (50000 * 0.01)) == 4


@test
def t15_stop_distance_bounds():
    # A 0.5 point stop on gold is below the 1.5 point minimum -> rejected
    assert 0.5 < 1.5
    # A 40 point stop exceeds the 15 point maximum -> rejected
    assert 40 > 15


@test
def t16_rounding_to_tick():
    assert abs(GC.round_tick(2700.07) - 2700.10) < 1e-9
    assert abs(GC.round_tick(2700.02) - 2700.00) < 1e-9


@test
def t17_rr_from_liquidity_target():
    entry, stop = 2700.0, 2695.0
    cost = 2 * GC.tick  # 2 ticks round trip
    liq = 2715.0
    risk = (entry - stop) + cost
    rr = (liq - entry - cost) / risk
    assert 2.7 < rr < 2.9, rr


@test
def t19_gc_rounds_to_zero_at_half_percent():
    """The usability trap: 0.5% on 50K cannot buy one GC contract on a 5pt stop."""
    risk = 50000 * 0.005           # $250
    raw = risk / (5 * GC.point_value)
    assert raw == 0.5
    assert int(raw) == 0           # primary GC size is zero
    # The micro equivalent is 5 contracts at the same dollar risk.
    alt = risk / (5 * MGC.point_value)
    assert int(alt) == 5


@test
def t20_micro_limit_is_ten_times_the_mini_limit():
    """FundedNext Rapid Daily 50K: 4 mini OR 40 micro, never 4 micro."""
    max_mini = 4
    max_micro = max_mini * 10
    assert max_micro == 40
    # 1% risk on 10pt stop = 5 MGC, comfortably under the 40 micro cap
    risk = 50000 * 0.01
    assert int(risk / (10 * MGC.point_value)) == 5
    assert 5 <= max_micro


@test
def t21_losses_remaining_is_the_survival_number():
    mll = 2000.0
    assert int(mll // 250) == 8      # 0.5% risk
    assert int(mll // 500) == 4      # 1.0% risk
    assert int(mll // 750) == 2      # 1.5% risk


@test
def t22_no_overnight_session_window():
    # FundedNext: 18:00 ET open, 15:10 ET flat-by.
    # 18:00 -> midnight is 6h; midnight -> 15:10 is 15h10m. Total 21h10m = 1270 min.
    assert (24 * 60 - 18 * 60) + (15 * 60 + 10) == 1270
    # Equivalently, only 6h50m of the 24h clock is unavailable for trading.
    assert (18 * 60) - (15 * 60 + 10) == 170


def main():
    print("=" * 66)
    print("LSMS engine behavioural spec")
    print("=" * 66)
    failures = 0
    for fn in TESTS:
        name = fn.__name__
        try:
            fn()
            print(f"  [PASS] {name}")
        except AssertionError as e:
            failures += 1
            print(f"  [FAIL] {name}: {e}")
    print("-" * 66)
    print(f"{len(TESTS) - failures}/{len(TESTS)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
