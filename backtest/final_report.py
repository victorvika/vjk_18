"""
Final report generator
======================
1) runs the chosen configuration on QQQ/SPY at 1m and 5m
2) simulates the FTMO 2-Step evaluation + funded account on the full year
3) runs ablations (remove one filter at a time) to show what each layer is worth
4) runs a risk-sensitivity test (what breaks a prop account)

Writes results/final_report.json and prints markdown tables.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, replace

import pandas as pd

from backtest import load_symbol, resample, run_backtest
from strategy import Config, prepare

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")

# SHIPPED CONFIGURATION ("LazyBear-native 5m")
# chosen because it is the only setting that is positive out-of-sample on BOTH
# QQQ and SPY with a broad, stable neighbourhood and no knife-edge filter.
BEST = dict(
    rr=3.0,
    atr_stop_mult=1.5,
    mom_strength_atr=0.0,      # momentum-strength filter OFF (knife-edge)
    mom_slope_confirm=True,    # LazyBear's own "momentum is rising" rule
    entry_start_min=10 * 60,   # 10:00
    min_minutes_to_flat=45,    # no new entry with < 45 min to the close
    use_htf_filter=True,
    use_vwap_filter=True,
)

# the aggressive 1-minute variant (much better backtest, tiny sample)
KNIFE = dict(
    rr=3.0,
    atr_stop_mult=2.5,
    mom_strength_atr=1.5,
    mom_slope_confirm=False,
    entry_start_min=10 * 60,
    min_minutes_to_flat=45,
    use_htf_filter=False,
    use_vwap_filter=False,
)


def load(symbol, tf):
    raw = load_symbol(symbol)
    return resample(raw, tf) if tf > 1 else raw


def run(symbol, tf, cfg, ftmo=True):
    df = load(symbol, tf)
    d = prepare(df, cfg)
    return run_backtest(d, cfg, ftmo_sim=ftmo, skip_prepare=True)


def fmt_ftmo(f):
    if not f:
        return "-"
    if f["breached"]:
        return f"FAILED ({f['breach_reason'].split('(')[0].strip()} on {f['breach_day']})"
    if f["phase"] == 3:
        return "PASSED both phases -> FUNDED"
    if f["phase"] == 2:
        return f"passed P1 on {f['phase1_pass_day']}"
    return "still in phase 1"


def main():
    os.makedirs(RESULTS, exist_ok=True)
    out = {"best_config": BEST, "runs": [], "ablations": [], "risk_sensitivity": []}

    # ---------------- 1) base runs ----------------
    print("### 1) Base configuration (risk 0.5%)\n")
    print("| Symbol | TF | Trades | Win% | PF | Exp/trade | Total P&L | Max DD | FTMO |")
    print("|---|---|---|---|---|---|---|---|---|")
    for sym in ["QQQ", "SPY"]:
        for tf in [5, 1]:
            cfg = Config(risk_pct=0.005, **BEST)
            r = run(sym, tf, cfg)
            s, f = r["stats"], r["ftmo"]
            out["runs"].append({"symbol": sym, "tf": tf, "risk": 0.005, "stats": s, "ftmo": f})
            print(f"| {sym} | {tf}m | {s['trades']} | {s['win_rate']*100:.1f}% | "
                  f"{s['profit_factor']:.2f} | {s['expectancy_r']:+.3f}R | "
                  f"${s['total_pnl']:,.0f} | {s['max_dd_pct']*100:.1f}% | {fmt_ftmo(f)} |")

    # ---------------- 1b) the aggressive 1m variant ----------------
    print("\n### 1b) Aggressive 1-minute variant (momK=1.5) - small sample\n")
    print("| Symbol | Trades | Win% | PF | Exp/trade | Total P&L | Max DD | FTMO |")
    print("|---|---|---|---|---|---|---|---|")
    for sym in ["QQQ", "SPY"]:
        cfg = Config(risk_pct=0.005, **KNIFE)
        r = run(sym, 1, cfg)
        s, f = r["stats"], r["ftmo"]
        out["runs"].append({"symbol": sym, "tf": 1, "risk": 0.005, "variant": "1m-knife", "stats": s, "ftmo": f})
        print(f"| {sym} | {s['trades']} | {s['win_rate']*100:.1f}% | {s['profit_factor']:.2f} | "
              f"{s['expectancy_r']:+.3f}R | ${s['total_pnl']:,.0f} | {s['max_dd_pct']*100:.1f}% | {fmt_ftmo(f)} |")

    # ---------------- 2) ablations ----------------
    print("\n### 2) Ablations - what each layer is worth (QQQ 5m, risk 0.5%)\n")
    print("| Variant | Trades | Win% | PF | Exp/trade | Total P&L | Max DD |")
    print("|---|---|---|---|---|---|---|")
    variants = {
        "FULL (all filters)": {},
        "- momentum-strength filter": {"mom_strength_atr": 0.0},
        "- VWAP filter": {"use_vwap_filter": False},
        "- HTF trend filter": {"use_htf_filter": False},
        "- both directional filters": {"use_vwap_filter": False, "use_htf_filter": False},
        "FULL, no daily-loss lock": {"daily_loss_stop_pct": 0.0},
        "FULL, no EOD flat (overnight allowed)": {"flatten_min": 24 * 60},
    }
    for name, override in variants.items():
        kw = dict(BEST)
        kw.update(override)
        cfg = Config(risk_pct=0.005, **kw)
        r = run("QQQ", 5, cfg, ftmo=False)
        s = r["stats"]
        out["ablations"].append({"variant": name, "stats": s})
        print(f"| {name} | {s['trades']} | {s['win_rate']*100:.1f}% | {s['profit_factor']:.2f} | "
              f"{s['expectancy_r']:+.3f}R | ${s['total_pnl']:,.0f} | {s['max_dd_pct']*100:.1f}% |")

    # ---------------- 3) risk sensitivity ----------------
    print("\n### 3) Risk sensitivity (QQQ 5m) - FTMO 2-step verdict\n")
    print("| Risk/trade | Trades | Win% | PF | Total P&L | Max DD | Daily-loss locks | FTMO |")
    print("|---|---|---|---|---|---|---|---|")
    for risk in [0.0025, 0.005, 0.0075, 0.01, 0.02, 0.03]:
        cfg = Config(risk_pct=risk, **BEST)
        r = run("QQQ", 5, cfg)
        s, f = r["stats"], r["ftmo"]
        out["risk_sensitivity"].append({"risk": risk, "stats": s, "ftmo": f})
        print(f"| {risk*100:.2f}% | {s['trades']} | {s['win_rate']*100:.1f}% | {s['profit_factor']:.2f} | "
              f"${s['total_pnl']:,.0f} | {s['max_dd_pct']*100:.1f}% | {len(f['blocked_days'])} | {fmt_ftmo(f)} |")

    # ---------------- 4) per-day detail for the base run ----------------
    cfg = Config(risk_pct=0.005, **BEST)
    r = run("QQQ", 5, cfg)
    day_pnl = r["day_pnl"]
    dp = pd.Series(day_pnl).sort_index()
    out["day_pnl_qqq5"] = {str(k): float(v) for k, v in dp.items()}
    out["day_stats"] = {
        "trading_days": int(len(dp)),
        "win_days": int((dp > 0).sum()),
        "loss_days": int((dp < 0).sum()),
        "flat_days": int((dp == 0).sum()),
        "best_day": float(dp.max()),
        "worst_day": float(dp.min()),
        "worst_day_pct": float(dp.min() / 100000 * 100),
        "avg_day": float(dp.mean()),
    }
    print("\n### 4) Day-by-day distribution (QQQ 5m, full year)\n")
    for k, v in out["day_stats"].items():
        print(f"- {k}: {v}")

    with open(os.path.join(RESULTS, "final_report.json"), "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nsaved -> results/final_report.json")


if __name__ == "__main__":
    main()
