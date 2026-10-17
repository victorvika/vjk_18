"""
Joint analysis: merge the four sweeps and find configurations that are
positive OUT-OF-SAMPLE on BOTH instruments (QQQ and SPY).

A config that only works on one symbol is luck; a config that works on both
is a candidate for the final recommendation.
"""
from __future__ import annotations

import os
import pandas as pd

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
KEY = ["rr", "atr_stop_mult", "mom_strength_atr", "mom_slope_confirm",
       "entry_start_min", "min_minutes_to_flat", "use_htf_filter", "use_vwap_filter"]


def load(tag):
    p = os.path.join(RESULTS, f"sweep_{tag}.csv")
    return pd.read_csv(p) if os.path.exists(p) else None


def main():
    tabs = {}
    for tag in ["QQQ_5m", "SPY_5m", "QQQ_1m", "SPY_1m"]:
        t = load(tag)
        if t is not None:
            tabs[tag] = t
            print(f"{tag}: {len(t)} configs")
    if not tabs:
        print("no sweep files yet")
        return

    for tf in ["5m", "1m"]:
        a, b = tabs.get(f"QQQ_{tf}"), tabs.get(f"SPY_{tf}")
        if a is None or b is None:
            continue
        m = a.merge(b, on=KEY, suffixes=("_qqq", "_spy"))
        m["worst_oo_exp"] = m[["oo_exp_qqq", "oo_exp_spy"]].min(axis=1)
        m["avg_oo_exp"] = m[["oo_exp_qqq", "oo_exp_spy"]].mean(axis=1)
        m["min_oo_pf"] = m[["oo_pf_qqq", "oo_pf_spy"]].min(axis=1)
        m["min_oo_trades"] = m[["oo_trades_qqq", "oo_trades_spy"]].min(axis=1)
        m = m[m["min_oo_trades"] >= 20]

        print(f"\n================  {tf} : robust across QQQ + SPY  ================")
        cols = KEY + ["oo_trades_qqq", "oo_exp_qqq", "oo_pf_qqq", "oo_trades_spy",
                      "oo_exp_spy", "oo_pf_spy", "worst_oo_exp", "min_oo_pf"]
        print(m.sort_values("worst_oo_exp", ascending=False)[cols].head(12).to_string(index=False))

        # how much of the whole grid is profitable out of sample?
        for tag in ["QQQ", "SPY"]:
            allr = tabs[f"{tag}_{tf}"]
            col = "oo_exp"
            print(f"  {tag} {tf}: {(allr[col] > 0).mean()*100:.1f}% of all "
                  f"{len(allr)} grid cells have positive OOS expectancy | "
                  f"median OOS exp = {allr[col].median():+.3f}R | "
                  f"best = {allr[col].max():+.3f}R")

        m.sort_values("worst_oo_exp", ascending=False).head(40).to_csv(
            os.path.join(RESULTS, f"robust_{tf}.csv"), index=False)

    # neighbourhood stability around the top config of each timeframe
    print("\n================  neighbourhood stability (5m, QQQ)  ================")
    q5 = tabs["QQQ_5m"]
    for rr in [1.5, 2.0, 2.5, 3.0]:
        row = []
        for am in [1.5, 2.0, 2.5, 3.0]:
            sel = q5[(q5.rr == rr) & (q5.atr_stop_mult == am) & (q5.mom_strength_atr == 1.0)
                     & (q5.mom_slope_confirm == False) & (q5.entry_start_min == 585)
                     & (q5.min_minutes_to_flat == 45) & (q5.use_htf_filter == True)
                     & (q5.use_vwap_filter == True)]
            row.append(f"{sel['oo_exp'].iloc[0]:+.2f}" if len(sel) else "  -  ")
        print(f"  rr={rr:<4} atr stop mult 1.5/2.0/2.5/3.0 -> OOS exp: {row}")


if __name__ == "__main__":
    main()
