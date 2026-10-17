"""
Validation of the 1-minute candidate configuration.

Checks that the result is a STABLE PLATEAU and not a single lucky cell:
  1) neighbourhood table (rr x ATR-mult) for BOTH symbols
  2) quarterly stability (4 sub-periods, fresh account each)
  3) trade distribution (clocks, days, exit reasons, holding time)
  4) walk-forward: use IS-optimal parameters, trade OOS
  5) cost stress: 2x and 3x slippage
"""
from __future__ import annotations

import os
from dataclasses import replace

import numpy as np
import pandas as pd

from backtest import load_symbol, resample, run_backtest
from strategy import Config, prepare

BASE = dict(
    rr=3.0,
    atr_stop_mult=2.5,
    mom_strength_atr=1.5,
    mom_slope_confirm=False,
    entry_start_min=10 * 60,
    min_minutes_to_flat=45,
    use_htf_filter=False,
    use_vwap_filter=False,
)


def prep(symbol, tf, cfg):
    raw = load_symbol(symbol)
    df = resample(raw, tf) if tf > 1 else raw
    return prepare(df, cfg)


def run_on(d, cfg, ftmo=False):
    return run_backtest(d, cfg, ftmo_sim=ftmo, skip_prepare=True)


def main():
    print("=" * 100)
    print("1) NEIGHBOURHOOD STABILITY (1-minute, OOS split, expectancy in R)")
    print("=" * 100)
    for sym in ["QQQ", "SPY"]:
        print(f"\n{sym}: rows = ATR stop multiple, cols = R multiple   [momK=1.5, 10:00, runway 45, no HTF/VWAP]")
        cache = {}
        for am in [1.5, 2.0, 2.5, 3.0, 3.5]:
            row = []
            for rr in [1.5, 2.0, 2.5, 3.0, 3.5]:
                cfg = Config(risk_pct=0.005, **{**BASE, "atr_stop_mult": am, "rr": rr})
                if id(cfg) not in cache:
                    cache[id(cfg)] = prep(sym, 1, cfg)
                d = cache[id(cfg)]
                days = sorted(d["session_date"].unique())
                cut = days[int(len(days) * 0.6)]
                oo = d[d["session_date"] >= cut].reset_index(drop=True)
                r = run_on(oo, cfg)
                st = r["stats"]
                row.append(f"{st['expectancy_r']:+.2f}/{st['trades']:>3}")
            print(f"  ATR x{am:<4} " + "  ".join(f"{x:>10}" for x in row))

    print("\n" + "=" * 100)
    print("2) MOMENTUM-STRENGTH SENSITIVITY (1m, OOS, rr=3.0 atr=2.5)")
    print("=" * 100)
    print(f"{'sym':<6}" + "".join(f"  momK={k:<8}" for k in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]))
    for sym in ["QQQ", "SPY"]:
        row = []
        for mk in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]:
            cfg = Config(risk_pct=0.005, **{**BASE, "mom_strength_atr": mk})
            d = prep(sym, 1, cfg)
            days = sorted(d["session_date"].unique())
            cut = days[int(len(days) * 0.6)]
            oo = d[d["session_date"] >= cut].reset_index(drop=True)
            st = run_on(oo, cfg)["stats"]
            row.append(f"{st['expectancy_r']:+.3f}/{st['trades']:>3}")
        print(f"{sym:<6}" + "".join(f"  {x:<14}" for x in row))

    print("\n" + "=" * 100)
    print("3) QUARTERLY STABILITY (1m, full year split into 4 quarters, fresh $100k each)")
    print("=" * 100)
    print(f"{'sym':<6} {'period':<26} {'n':>4} {'win%':>6} {'PF':>6} {'exp':>7} {'P&L':>9} {'maxDD':>7}")
    for sym in ["QQQ", "SPY"]:
        cfg = Config(risk_pct=0.005, **BASE)
        d = prep(sym, 1, cfg)
        days = sorted(d["session_date"].unique())
        for i in range(4):
            lo = days[int(len(days) * i / 4)]
            hi = days[int(len(days) * (i + 1) / 4)]
            part = d[(d["session_date"] >= lo) & (d["session_date"] < hi)].reset_index(drop=True)
            r = run_on(part, cfg)
            st = r["stats"]
            print(f"{sym:<6} {str(lo)+' -> '+str(hi):<26} {st['trades']:>4} "
                  f"{st['win_rate']*100:>5.1f}% {st['profit_factor']:>6.2f} {st['expectancy_r']:>+7.3f} "
                  f"{st['total_pnl']:>9,.0f} {st['max_dd_pct']*100:>6.1f}%")

    print("\n" + "=" * 100)
    print("4) TRADE DISTRIBUTION (1m, QQQ, full year, base config)")
    print("=" * 100)
    cfg = Config(risk_pct=0.005, **BASE)
    d = prep("QQQ", 1, cfg)
    r = run_on(d, cfg)
    tr = r["trades_df"].copy()
    tr["ts"] = pd.to_datetime(tr["ts"])
    tr["date"] = tr["ts"].dt.date
    tr["hour"] = tr["ts"].dt.hour
    print(f"total trades: {len(tr)}   days traded: {tr['date'].nunique()}")
    print("\nby exit reason:"); print(tr["reason"].value_counts().to_string())
    print("\nby hour:"); print(tr.groupby("hour").size().to_string())
    print("\nby side:"); print(tr["side"].value_counts().to_string())
    hold = (tr["ts"].diff().dt.total_seconds() / 60).dropna()
    print(f"\nholding time (min): median={hold.median():.0f} mean={hold.mean():.0f} "
          f"p90={hold.quantile(0.9):.0f}")
    per_day = tr.groupby("date").size()
    print(f"trades per traded day: mean={per_day.mean():.2f} max={per_day.max()}")
    print(f"R distribution: mean={tr['r'].mean():+.3f} std={tr['r'].std():.3f} "
          f"best={tr['r'].max():+.2f} worst={tr['r'].min():+.2f}")
    worst_days = r["day_pnl"]
    s = pd.Series(worst_days).sort_values()
    print(f"\nworst 5 days: " + ", ".join(f"{k} ${v:,.0f}" for k, v in s.head(5).items()))
    print(f"best 5 days:  " + ", ".join(f"{k} ${v:,.0f}" for k, v in s.tail(5).items()))

    print("\n" + "=" * 100)
    print("5) COST STRESS TEST (1m, QQQ full year, base config)")
    print("=" * 100)
    for slip, label in [(0.01, "1 tick (realistic)"), (0.02, "2 ticks"), (0.03, "3 ticks"), (0.05, "5 ticks (stressed)")]:
        cfg = Config(risk_pct=0.005, slippage_ticks=slip, **BASE)
        r = run_on(prep("QQQ", 1, cfg), cfg)
        st = r["stats"]
        print(f"  slippage {label:<22} exp={st['expectancy_r']:+.3f}R  PF={st['profit_factor']:.2f}  "
              f"P&L=${st['total_pnl']:,.0f}")

    print("\n" + "=" * 100)
    print("6) WALK-FORWARD (1m): parameters picked on IS, traded on OOS")
    print("=" * 100)
    for sym in ["QQQ", "SPY"]:
        grid = []
        for am in [1.5, 2.0, 2.5, 3.0]:
            for rr in [2.0, 2.5, 3.0]:
                for mk in [1.0, 1.5, 2.0]:
                    grid.append({"atr_stop_mult": am, "rr": rr, "mom_strength_atr": mk})
        d0 = prep(sym, 1, Config(**BASE))
        days = sorted(d0["session_date"].unique())
        cut = days[int(len(days) * 0.6)]
        is_part = d0[d0["session_date"] < cut].reset_index(drop=True)
        oo_part = d0[d0["session_date"] >= cut].reset_index(drop=True)
        best, best_exp = None, -9
        for g in grid:
            cfg = Config(risk_pct=0.005, **{**BASE, **g})
            st = run_on(is_part, cfg)["stats"]
            if st["expectancy_r"] > best_exp:
                best_exp, best = st["expectancy_r"], g
        cfg = Config(risk_pct=0.005, **{**BASE, **best})
        st = run_on(oo_part, cfg)["stats"]
        print(f"  {sym}: IS picked {best} (IS exp {best_exp:+.3f}R) -> OOS exp {st['expectancy_r']:+.3f}R "
              f"PF {st['profit_factor']:.2f} on {st['trades']} trades")


if __name__ == "__main__":
    main()
