"""
Parameter study with an honest in-sample / out-of-sample split.

The split is by DATE (first 60% of sessions = in-sample, last 40% = out-of-sample)
and the out-of-sample account always starts with a fresh $100,000, exactly like
a new prop-firm challenge.

Ranking is by the WEAKER of the two expectancies (a config that only works
in-sample is worthless) and configs with too few trades are dropped.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
from dataclasses import asdict, replace

import pandas as pd

from backtest import load_symbol, resample, run_backtest
from strategy import Config, prepare

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")


def split_prepared(d: pd.DataFrame, frac: float = 0.6):
    days = sorted(d["session_date"].unique())
    cut = days[int(len(days) * frac)]
    mask = d["session_date"] >= cut
    return d[~mask].reset_index(drop=True), d[mask].reset_index(drop=True), cut


def evaluate(d_is, d_oos, cfg: Config):
    r_is = run_backtest(d_is, cfg, ftmo_sim=False, skip_prepare=True)
    r_oo = run_backtest(d_oos, cfg, ftmo_sim=False, skip_prepare=True)
    s_is, s_oo = r_is["stats"], r_oo["stats"]
    return {
        "is_trades": s_is.get("trades", 0),
        "is_wr": s_is.get("win_rate", 0.0),
        "is_pf": s_is.get("profit_factor", 0.0),
        "is_exp": s_is.get("expectancy_r", 0.0),
        "is_dd": s_is.get("max_dd_pct", 0.0),
        "oo_trades": s_oo.get("trades", 0),
        "oo_wr": s_oo.get("win_rate", 0.0),
        "oo_pf": s_oo.get("profit_factor", 0.0),
        "oo_exp": s_oo.get("expectancy_r", 0.0),
        "oo_dd": s_oo.get("max_dd_pct", 0.0),
        "oo_pnl": s_oo.get("total_pnl", 0.0),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="QQQ")
    ap.add_argument("--tf", type=int, default=5)
    ap.add_argument("--min-trades", type=int, default=25)
    ap.add_argument("--out", default=os.path.join(RESULTS, "sweep.json"))
    args = ap.parse_args()

    raw = load_symbol(args.symbol)
    df = resample(raw, args.tf) if args.tf > 1 else raw

    grid = {
        "rr": [1.5, 2.0, 2.5, 3.0],
        "atr_stop_mult": [1.5, 2.0, 2.5, 3.0],
        "mom_strength_atr": [0.0, 0.5, 1.0, 1.5, 2.0],
        "mom_slope_confirm": [False, True],
        "entry_start_min": [9 * 60 + 45, 10 * 60 + 0],
        "min_minutes_to_flat": [0, 45],
        "use_htf_filter": [True, False],
        "use_vwap_filter": [True, False],
    }
    keys = list(grid)
    combos = list(itertools.product(*[grid[k] for k in keys]))
    print(f"grid size: {len(combos)} configs | {args.symbol} {args.tf}m")

    # prepare once per (vwap/htf-independent) indicator set -> cache by relevant knobs
    cache: dict = {}
    rows = []
    for i, combo in enumerate(combos):
        kw = dict(zip(keys, combo))
        cfg = Config(**kw)
        # indicators depend on: bb/kc (fixed), vwap filter, htf filter, htf len,
        # atr len, mom strength, mom slope -> cache key
        key = (cfg.use_vwap_filter, cfg.use_htf_filter, cfg.htf_minutes,
               cfg.htf_ema_len, cfg.atr_len, cfg.mom_strength_atr, cfg.mom_slope_confirm,
               cfg.bb_len, cfg.bb_mult, cfg.kc_len, cfg.kc_mult)
        if key not in cache:
            d = prepare(df, cfg)
            d_is, d_oo, cut = split_prepared(d)
            cache[key] = (d_is, d_oo, cut)
        d_is, d_oo, cut = cache[key]
        m = evaluate(d_is, d_oo, cfg)
        m.update(kw)
        m["score"] = min(m["is_exp"], m["oo_exp"])
        rows.append(m)
        if (i + 1) % 40 == 0:
            print(f"  {i+1}/{len(combos)} done")

    df_res = pd.DataFrame(rows)
    df_res = df_res[df_res["oo_trades"] >= args.min_trades]
    df_res = df_res.sort_values("score", ascending=False)

    os.makedirs(RESULTS, exist_ok=True)
    df_res.to_csv(os.path.join(RESULTS, f"sweep_{args.symbol}_{args.tf}m.csv"), index=False)
    with open(args.out, "w") as f:
        json.dump({"grid": grid, "split_day": str(cache[list(cache)[0]][2]),
                   "rows": rows}, f, indent=2, default=str)

    cols = ["rr", "atr_stop_mult", "mom_strength_atr", "mom_slope_confirm", "entry_start_min",
            "min_minutes_to_flat", "use_htf_filter", "is_trades", "is_exp", "oo_trades",
            "oo_exp", "oo_pf", "oo_wr", "oo_dd"]
    show = df_res[cols].head(25).copy()
    show["entry_start_min"] = (show["entry_start_min"] // 60 * 100 + show["entry_start_min"] % 60)
    print("\n=== TOP 25 (by min(IS,OOS) expectancy) ===")
    print(show.to_string(index=False))
    print(f"\nfull table -> results/sweep_{args.symbol}_{args.tf}m.csv")


if __name__ == "__main__":
    main()
