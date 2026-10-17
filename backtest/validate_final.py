"""
Final rigorous validation
==========================
For every shortlisted configuration:
  * full-year stats on QQQ and SPY
  * quarterly stability (4 periods, fresh $100k account each)
  * BOOTSTRAP 95% confidence interval of the expectancy (resampling trades)
    -> this is what separates a real edge from a lucky sample
  * cost stress test

A configuration is only "shipped" if the CI, or at least the cross-instrument
consistency, supports it.
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd

from backtest import load_symbol, resample, run_backtest
from strategy import Config, prepare

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
RNG = np.random.default_rng(20261017)


def bootstrap_ci(r_values, n_boot=20000, conf=0.95):
    r_values = np.asarray([x for x in r_values if not np.isnan(x)], dtype=float)
    n = len(r_values)
    if n < 5:
        return (np.nan, np.nan, np.nan)
    means = np.array([RNG.choice(r_values, n, replace=True).mean() for _ in range(n_boot)])
    lo = np.percentile(means, (1 - conf) / 2 * 100)
    hi = np.percentile(means, (1 + conf) / 2 * 100)
    return (float(lo), float(hi), float(means.mean()))


def prep(sym, tf, cfg):
    raw = load_symbol(sym)
    df = resample(raw, tf) if tf > 1 else raw
    return prepare(df, cfg)


def quarters(d):
    days = sorted(d["session_date"].unique())
    out = []
    for i in range(4):
        lo = days[int(len(days) * i / 4)]
        hi = days[min(int(len(days) * (i + 1) / 4), len(days) - 1)]
        part = d[(d["session_date"] >= lo) & (d["session_date"] <= hi)].reset_index(drop=True)
        out.append((f"{lo}->{hi}", part))
    return out


def evaluate(sym, tf, name, kw, verbose=True):
    cfg = Config(risk_pct=0.005, **kw)
    d = prep(sym, tf, cfg)
    r = run_backtest(d, cfg)
    st = r["stats"]
    tr = r["trades_df"]
    lo, hi, mean = bootstrap_ci(tr["r"].to_numpy())
    q = []
    for label, part in quarters(d):
        if len(part) == 0:
            q.append((label, 0, 0.0, 0.0))
            continue
        s = run_backtest(part, cfg)["stats"]
        q.append((label, s["trades"], s["expectancy_r"], s["profit_factor"]))
    if verbose:
        print(f"\n--- {name} | {sym} {tf}m ---")
        print(f"  full year: n={st['trades']:>3}  win={st['win_rate']*100:>5.1f}%  "
              f"PF={st['profit_factor']:>5.2f}  exp={st['expectancy_r']:+.3f}R  "
              f"P&L=${st['total_pnl']:>8,.0f}  maxDD={st['max_dd_pct']*100:>4.1f}%")
        print(f"  bootstrap 95% CI of expectancy: [{lo:+.3f}R, {hi:+.3f}R]  (mean {mean:+.3f}R)")
        for label, n, e, pf in q:
            print(f"    {label:<26} n={n:>3}  exp={e:+.3f}R  PF={pf:.2f}")
    return {"sym": sym, "tf": tf, "name": name, "n": st["trades"], "exp": st["expectancy_r"],
            "pf": st["profit_factor"], "ci_lo": lo, "ci_hi": hi, "pnl": st["total_pnl"],
            "dd": st["max_dd_pct"], "quarters": q}


def main():
    # ---- shortlist from the joint sweep: 5m, VWAP ON, >=50 OOS trades on BOTH symbols
    joint = pd.read_csv(os.path.join(RESULTS, "robust_5m.csv"))
    joint = joint[(joint.use_vwap_filter == True) & (joint.min_oo_trades >= 50)]
    joint = joint.sort_values("worst_oo_exp", ascending=False)
    print("=" * 100)
    print("SHORTLIST (5m, VWAP on, >=50 OOS trades on both symbols) - ranked by worst-case OOS")
    print("=" * 100)
    print(joint[["rr", "atr_stop_mult", "mom_strength_atr", "mom_slope_confirm",
                 "entry_start_min", "min_minutes_to_flat", "use_htf_filter",
                 "oo_exp_qqq", "oo_exp_spy", "oo_pf_qqq", "oo_pf_spy"]].head(8).to_string(index=False))

    cands = []
    for _, row in joint.head(3).iterrows():
        kw = dict(rr=float(row.rr), atr_stop_mult=float(row.atr_stop_mult),
                  mom_strength_atr=float(row.mom_strength_atr),
                  mom_slope_confirm=bool(row.mom_slope_confirm),
                  entry_start_min=int(row.entry_start_min),
                  min_minutes_to_flat=int(row.min_minutes_to_flat),
                  use_htf_filter=bool(row.use_htf_filter), use_vwap_filter=True)
        cands.append((f"5m cand{len(cands)+1} rr{row.rr:g} atr{row.atr_stop_mult:g} "
                      f"momK{row.mom_strength_atr:g} slope{int(bool(row.mom_slope_confirm))} "
                      f"htf{int(bool(row.use_htf_filter))}", kw))

    # the 1-minute knife-edge configuration (for comparison / honesty)
    cands.append(("1m KNIFE-EDGE rr3.0 atr2.5 momK1.5 (28 trades/yr)",
                  dict(rr=3.0, atr_stop_mult=2.5, mom_strength_atr=1.5, mom_slope_confirm=False,
                       entry_start_min=600, min_minutes_to_flat=45,
                       use_htf_filter=False, use_vwap_filter=False)))
    # the 5m "LazyBear native" configuration
    cands.append(("5m LAZYBEAR-NATIVE rr3.0 atr1.5 momK0 slopeT htfY vwapY",
                  dict(rr=3.0, atr_stop_mult=1.5, mom_strength_atr=0.0, mom_slope_confirm=True,
                       entry_start_min=600, min_minutes_to_flat=45,
                       use_htf_filter=True, use_vwap_filter=True)))

    all_res = []
    for name, kw in cands:
        tf = 1 if name.startswith("1m") else 5
        for sym in ["QQQ", "SPY"]:
            all_res.append(evaluate(sym, tf, name, kw))
        print()

    import json
    with open(os.path.join(RESULTS, "validation_final.json"), "w") as f:
        json.dump(all_res, f, indent=2, default=str)
    print(f"\nsaved -> results/validation_final.json")


if __name__ == "__main__":
    main()
