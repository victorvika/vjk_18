"""
Backtest + FTMO prop-firm simulator
===================================

Runs the exact same logic as tradingview/vwap_squeeze_propfirm_v6.pine and
simulates the FTMO 2-Step evaluation (and the funded account) on the curve:

  Phase 1 (Challenge)    : +10% target, 5% max DAILY loss (equity based),
                            10% max loss (static), min 4 trading days
  Phase 2 (Verification) : +5% target, same loss limits
  Funded account         : no target, same loss limits + Consistency rule
                            (best day <= 30% of total profit for a reward)

Assumptions (deliberately pessimistic, and matched to Pine):
  * signal on bar close -> fill at the NEXT bar's open
  * if a bar touches both stop and target, the STOP is filled first
  * slippage on every fill, no commission
  * no overnight positions (flattened before the close)
  * daily loss guard closes everything and stops trading for the rest of the day
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import asdict, replace

import numpy as np
import pandas as pd

from strategy import Config, prepare

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


# --------------------------------------------------------------------------- #
#  Data loading
# --------------------------------------------------------------------------- #
def load_symbol(symbol: str, data_dir: str = DATA_DIR) -> pd.DataFrame:
    path = os.path.join(data_dir, f"{symbol}_1min.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found - run:  bash backtest/fetch_data.sh"
        )
    df = pd.read_csv(path)
    df["ts"] = pd.to_datetime(df["date"], utc=True, format="mixed")
    df = df.sort_values("ts").reset_index(drop=True)
    df["ts"] = df["ts"].dt.tz_convert("America/New_York")
    df = df[["ts", "open", "high", "low", "close", "volume"]].reset_index(drop=True)
    df["volume"] = df["volume"].fillna(0.0)
    return df


def resample(df: pd.DataFrame, minutes: int) -> pd.DataFrame:
    """Aggregate 1-minute bars into N-minute bars (RTH sessions only)."""
    out = (
        df.set_index("ts")
        .resample(f"{minutes}min", label="left", closed="left")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
        .dropna()
        .reset_index()
    )
    return out


# --------------------------------------------------------------------------- #
#  Core simulator
# --------------------------------------------------------------------------- #
def run_backtest(df: pd.DataFrame, cfg: Config, ftmo_sim: bool = True,
                 skip_prepare: bool = False) -> dict:
    d = df if skip_prepare else prepare(df, cfg)

    o = d["open"].to_numpy()
    h = d["high"].to_numpy()
    lo = d["low"].to_numpy()
    c = d["close"].to_numpy()
    atr = d["atr"].to_numpy()
    mom = d["mom"].to_numpy()
    sig_l = d["raw_long"].to_numpy(dtype=bool)
    sig_s = d["raw_short"].to_numpy(dtype=bool)
    minute = d["minute_of_day"].to_numpy()
    # session window, evaluated on the SIGNAL bar (Pine parity: the order is
    # placed at the signal bar's close and filled at the next bar's open)
    session_ok = (
        (minute >= cfg.entry_start_min)
        & (minute <= cfg.entry_end_min)
        & ((cfg.flatten_min - minute) >= cfg.min_minutes_to_flat)
    )
    day = d["session_date"].to_numpy()
    ts = d["ts"].to_numpy()

    slip = cfg.slippage_ticks
    cash = cfg.account_size
    equity_curve = np.zeros(len(d))
    day_start_balance = np.zeros(len(d))
    day_blocked = np.zeros(len(d), dtype=bool)

    # position
    pos_side = 0
    pos_qty = 0.0
    pos_entry = 0.0
    pos_stop = 0.0
    pos_target = 0.0
    pos_day = None

    trades = []
    day_pnl = {}
    day_trade_count = {}
    current_day = None
    trades_today = 0
    blocked_today = False
    day_start_bal = cash

    # FTMO state
    ftmo = _FtmOState(cfg) if ftmo_sim else None
    stop_sim = False

    for i in range(len(d)):
        # ---------- new session ----------
        if day[i] != current_day:
            if pos_side != 0:                      # should not happen (flat by EOD)
                cash += pos_side * pos_qty * (c[i] - pos_entry)
                pos_side = 0
            current_day = day[i]
            day_start_bal = cash
            trades_today = 0
            blocked_today = False
            if ftmo:
                ftmo.new_day(cash, day[i])

        day_start_balance[i] = day_start_bal

        # ---------- 1) ENTRY at this bar's open, signal from previous bar ----
        if pos_side == 0 and i > 0 and not blocked_today and trades_today < cfg.max_trades_per_day:
            want = 0
            if sig_l[i - 1] and session_ok[i - 1]:
                want = 1
            elif sig_s[i - 1] and session_ok[i - 1]:
                want = -1
            if want != 0 and atr[i - 1] == atr[i - 1] and atr[i - 1] > 0:
                ref = c[i - 1]                      # signal-bar close (Pine parity)
                stop_d = atr[i - 1] * cfg.atr_stop_mult
                if stop_d > 0:
                    entry_px = o[i]
                    if want == 1:
                        stop_px = ref - stop_d
                        tgt_px = ref + stop_d * cfg.rr
                        ok = stop_px < entry_px < tgt_px
                    else:
                        stop_px = ref + stop_d
                        tgt_px = ref - stop_d * cfg.rr
                        ok = tgt_px < entry_px < stop_px
                    if ok:
                        risk = cash * cfg.risk_pct          # equity == cash while flat
                        qty = math.floor(risk / stop_d)
                        if qty >= 1:
                            pos_side = want
                            pos_qty = qty
                            pos_entry = entry_px
                            pos_stop = stop_px
                            pos_target = tgt_px
                            pos_day = current_day
                            trades_today += 1
                            day_trade_count[current_day] = day_trade_count.get(current_day, 0) + 1

        # ---------- 2) INTRABAR exits (stop first -> pessimistic, Pine-like) ----
        exit_px = None
        exit_reason = None
        if pos_side != 0:
            if pos_side == 1:
                if lo[i] <= pos_stop:
                    exit_px, exit_reason = pos_stop, "stop"
                elif h[i] >= pos_target:
                    exit_px, exit_reason = pos_target, "target"
            else:
                if h[i] >= pos_stop:
                    exit_px, exit_reason = pos_stop, "stop"
                elif lo[i] <= pos_target:
                    exit_px, exit_reason = pos_target, "target"

        if exit_px is not None:
            fill = exit_px + (-1 if pos_side == 1 else 1) * slip
            pnl = pos_side * pos_qty * (fill - pos_entry) - cfg.commission_per_unit * pos_qty
            cash += pnl
            trades.append(
                _trade(ts[i], day[i], pos_side, pos_qty, pos_entry, fill, pnl,
                       exit_reason, pos_stop, pos_target, atr[i - 1] if i > 0 else np.nan)
            )
            day_pnl[current_day] = day_pnl.get(current_day, 0.0) + pnl
            pos_side = 0

        # ---------- 3) worst intrabar equity (FTMO checks use intrabar equity) ----
        if pos_side != 0:
            worst = lo[i] if pos_side == 1 else h[i]
            unreal = pos_side * pos_qty * (worst - pos_entry)
        else:
            unreal = 0.0
        equity_intra = cash + unreal

        if ftmo:
            breach = ftmo.check(equity_intra, cash)
            if breach:
                # force-flat and stop this account
                if pos_side != 0:
                    fill = c[i] + (-1 if pos_side == 1 else 1) * slip
                    pnl = pos_side * pos_qty * (fill - pos_entry)
                    cash += pnl
                    day_pnl[current_day] = day_pnl.get(current_day, 0.0) + pnl
                    trades.append(
                        _trade(ts[i], day[i], pos_side, pos_qty, pos_entry, fill, pnl,
                               "breach", pos_stop, pos_target, atr[i - 1] if i > 0 else np.nan)
                    )
                    pos_side = 0
                ftmo.breached = True
                ftmo.breach_reason = breach
                ftmo.breach_day = current_day
                equity_intra = cash
                stop_sim = True

        # ---------- 4) daily-loss guard (own risk control) ----
        if pos_side == 0 and not blocked_today and cfg.daily_loss_stop_pct > 0:
            day_pnl_now = cash - day_start_bal
            if day_pnl_now <= -abs(cfg.daily_loss_stop_pct) * cfg.account_size:
                blocked_today = True
                day_blocked[i] = True
                if ftmo:
                    ftmo.blocked_days.append(current_day)

        # ---------- 5) flatten before the close ----------
        if pos_side != 0 and minute[i] >= cfg.flatten_min:
            fill = c[i] + (-1 if pos_side == 1 else 1) * slip
            pnl = pos_side * pos_qty * (fill - pos_entry)
            cash += pnl
            day_pnl[current_day] = day_pnl.get(current_day, 0.0) + pnl
            trades.append(
                _trade(ts[i], day[i], pos_side, pos_qty, pos_entry, fill, pnl,
                       "eod", pos_stop, pos_target, atr[i - 1] if i > 0 else np.nan)
            )
            pos_side = 0

        equity_curve[i] = cash + (pos_side * pos_qty * (c[i] - pos_entry) if pos_side else 0.0)

        if ftmo and not ftmo.done:
            ftmo.update_progress(cash, current_day, day_pnl.get(current_day, 0.0))

        if stop_sim:
            # the account is dead - stop the simulation at the breach point
            equity_curve[i:] = equity_curve[i]
            break

    # ---------------- assemble results ----------------
    tr = pd.DataFrame(trades)
    res = {
        "cash": cash,
        "equity": equity_curve,
        "trades_df": tr,
        "day_pnl": day_pnl,
        "day_trade_count": day_trade_count,
        "day_blocked": day_blocked,
    }
    res["stats"] = compute_stats(tr, equity_curve, cfg)
    if ftmo:
        res["ftmo"] = ftmo.report()
    return res


def _trade(ts, day, side, qty, entry, fill, pnl, reason, stop, target, atr):
    risk = abs(entry - stop) * qty
    r = pnl / risk if risk > 0 else np.nan
    return {
        "ts": ts, "day": day, "side": side, "qty": qty, "entry": entry, "exit": fill,
        "pnl": pnl, "r": r, "reason": reason, "stop": stop, "target": target, "atr": atr,
    }


# --------------------------------------------------------------------------- #
#  FTMO state machine
# --------------------------------------------------------------------------- #
class _FtmOState:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.initial = cfg.account_size
        self.daily_loss_amount = cfg.account_size * cfg.ftmo_daily_loss_pct
        self.max_loss_amount = cfg.account_size * cfg.ftmo_max_loss_pct
        self.phase = 1
        self.day_start_balance = cfg.account_size
        self.max_loss_floor = cfg.account_size - self.max_loss_amount
        self.daily_floor = cfg.account_size - self.daily_loss_amount
        self.trading_days = 0
        self.breached = False
        self.breach_reason = None
        self.breach_day = None
        self.blocked_days = []
        self.done = False
        self.phase1_pass_day = None
        self.phase2_pass_day = None
        self.p1_start_day = None
        self.p2_start_day = None
        self.funded_start_day = None
        self.total_profit = 0.0
        self.day_profits = {}
        self.best_day = 0.0

    def new_day(self, balance, day):
        self.day_start_balance = balance
        self.daily_floor = balance - self.daily_loss_amount
        self.trading_days = 0  # reset per phase, counted via day_profits
        if self.p1_start_day is None:
            self.p1_start_day = day
        if self.p2_start_day is None:
            self.p2_start_day = day

    def check(self, equity_intra, balance):
        if equity_intra < self.daily_floor:
            return f"DAILY_LOSS (equity {equity_intra:,.0f} < floor {self.daily_floor:,.0f})"
        if equity_intra < self.max_loss_floor:
            return f"MAX_LOSS (equity {equity_intra:,.0f} < floor {self.max_loss_floor:,.0f})"
        return None

    def update_progress(self, balance, day, day_pnl):
        if day is None:
            return
        self.day_profits[day] = self.day_profits.get(day, 0.0) + day_pnl
        self.total_profit = sum(self.day_profits.values())
        self.best_day = max(self.day_profits.values()) if self.day_profits else 0.0

        if self.phase == 1:
            days = len([d for d, v in self.day_profits.items() if v != 0])
            if balance >= self.initial * (1 + self.cfg.ftmo_target_pct) and days >= self.cfg.ftmo_min_days:
                self.phase = 2
                self.phase1_pass_day = day
                self.day_profits = {}
                self.total_profit = 0.0
                self.best_day = 0.0
                self.trading_days = 0
        elif self.phase == 2:
            days = len([d for d, v in self.day_profits.items() if v != 0])
            if balance >= self.initial * (1 + self.cfg.ftmo_target_pct_p2) and days >= self.cfg.ftmo_min_days:
                self.phase = 3
                self.phase2_pass_day = day
                self.funded_start_day = day
                self.day_profits = {}
                self.total_profit = 0.0
                self.best_day = 0.0

    def report(self):
        return {
            "phase": self.phase,
            "breached": self.breached,
            "breach_reason": self.breach_reason,
            "breach_day": str(self.breach_day) if self.breach_day else None,
            "phase1_pass_day": str(self.phase1_pass_day) if self.phase1_pass_day else None,
            "phase2_pass_day": str(self.phase2_pass_day) if self.phase2_pass_day else None,
            "phase1_days": self.phase1_pass_day,
            "max_loss_floor": self.max_loss_floor,
            "daily_loss_amount": self.daily_loss_amount,
            "blocked_days": [str(d) for d in self.blocked_days],
            "total_profit": self.total_profit,
            "best_day": self.best_day,
            "consistency_ratio": (self.best_day / self.total_profit) if self.total_profit > 0 else None,
        }


# --------------------------------------------------------------------------- #
#  Statistics
# --------------------------------------------------------------------------- #
def compute_stats(tr: pd.DataFrame, equity: np.ndarray, cfg: Config) -> dict:
    if tr is None or len(tr) == 0:
        eq = pd.Series(equity)
        return {"trades": 0, "win_rate": 0.0, "profit_factor": 0.0, "expectancy_r": 0.0,
                "avg_win_r": 0.0, "avg_loss_r": 0.0, "total_pnl": 0.0, "avg_trade_pnl": 0.0,
                "max_dd_pct": float((eq.cummax() - eq).max() / eq.cummax().max()) if len(eq) else 0.0,
                "max_dd_abs": 0.0, "max_win_streak_loss": 0, "exit_reasons": {},
                "avg_bars_held": 0.0}

    wins = tr[tr["pnl"] > 0]
    losses = tr[tr["pnl"] <= 0]
    gross_win = float(wins["pnl"].sum())
    gross_loss = float(-losses["pnl"].sum())
    rets = tr["r"].dropna()

    # max drawdown on the equity curve
    eq = pd.Series(equity)
    run_max = eq.cummax()
    dd = (run_max - eq) / run_max
    max_dd_pct = float(dd.max()) if len(dd) else 0.0
    max_dd_abs = float((run_max - eq).max()) if len(eq) else 0.0

    # longest losing streak
    streak = best = 0
    for p in tr["pnl"].to_numpy():
        if p <= 0:
            streak += 1
            best = max(best, streak)
        else:
            streak = 0

    return {
        "trades": int(len(tr)),
        "win_rate": float((tr["pnl"] > 0).mean()),
        "profit_factor": (gross_win / gross_loss) if gross_loss > 0 else float("inf"),
        "expectancy_r": float(rets.mean()) if len(rets) else 0.0,
        "avg_win_r": float(wins["r"].mean()) if len(wins) else 0.0,
        "avg_loss_r": float(losses["r"].mean()) if len(losses) else 0.0,
        "total_pnl": float(tr["pnl"].sum()),
        "avg_trade_pnl": float(tr["pnl"].mean()),
        "max_dd_pct": max_dd_pct,
        "max_dd_abs": max_dd_abs,
        "max_win_streak_loss": best,
        "exit_reasons": tr["reason"].value_counts().to_dict(),
        "avg_bars_held": float((tr["ts"].diff().dt.total_seconds().fillna(0) / 60).mean()) if len(tr) > 1 else 0.0,
    }


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="QQQ")
    ap.add_argument("--tf", type=int, default=5, help="bar size in minutes (1, 5, 15)")
    ap.add_argument("--risk", type=float, default=0.005)
    ap.add_argument("--atr-mult", type=float, default=1.5)   # shipped config
    ap.add_argument("--rr", type=float, default=3.0)          # shipped config
    ap.add_argument("--no-vwap", action="store_true")
    ap.add_argument("--no-htf", action="store_true")
    ap.add_argument("--max-trades", type=int, default=3)
    ap.add_argument("--daily-stop", type=float, default=0.02)
    ap.add_argument("--out", default=None)
    ap.add_argument("--save-trades", action="store_true")
    args = ap.parse_args()

    cfg = Config(
        risk_pct=args.risk,
        atr_stop_mult=args.atr_mult,
        rr=args.rr,
        use_vwap_filter=not args.no_vwap,
        use_htf_filter=not args.no_htf,
        max_trades_per_day=args.max_trades,
        daily_loss_stop_pct=args.daily_stop,
    )

    df = load_symbol(args.symbol)
    if args.tf > 1:
        df = resample(df, args.tf)
    res = run_backtest(df, cfg)

    st = res["stats"]
    print(f"\n=== {args.symbol} {args.tf}m | {cfg.label()} ===")
    print(f"trades        : {st['trades']}")
    print(f"win rate      : {st['win_rate']*100:.1f}%")
    print(f"profit factor : {st['profit_factor']:.2f}")
    print(f"expectancy    : {st['expectancy_r']:+.3f} R / trade")
    print(f"total P&L     : ${st['total_pnl']:,.0f}  ({st['total_pnl']/cfg.account_size*100:+.2f}%)")
    print(f"max DD        : {st['max_dd_pct']*100:.2f}%  (${st['max_dd_abs']:,.0f})")
    print(f"exit reasons  : {st['exit_reasons']}")
    if "ftmo" in res:
        f = res["ftmo"]
        print(f"FTMO phase    : {f['phase']}  breached={f['breached']} {f['breach_reason'] or ''}")
        print(f"phase1 pass   : {f['phase1_pass_day']} | phase2 pass: {f['phase2_pass_day']}")
        print(f"blocked days  : {len(f['blocked_days'])}")

    if args.out:
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        out = {
            "symbol": args.symbol, "tf": args.tf, "config": asdict(cfg),
            "stats": st, "ftmo": res.get("ftmo"),
            "day_pnl": {str(k): float(v) for k, v in res["day_pnl"].items()},
        }
        with open(args.out, "w") as f:
            json.dump(out, f, indent=2, default=str)
        print(f"saved -> {args.out}")
    if args.save_trades and len(res["trades_df"]):
        os.makedirs("../results", exist_ok=True)
        res["trades_df"].to_csv(f"../results/trades_{args.symbol}_{args.tf}m.csv", index=False)


if __name__ == "__main__":
    main()
