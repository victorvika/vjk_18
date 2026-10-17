"""
Strategy engine — PINE-PARITY with tradingview/vwap_squeeze_propfirm_v6.pine
=========================================================================

Signal stack (all three layers are non-repainting, computed on bar close):

  L1  Squeeze Momentum (LazyBear / John Carter "TTM Squeeze")
        Bollinger(20, 2.0) inside Keltner(20, 1.5)  -> squeeze ON
        Bollinger outside Keltner                    -> squeeze RELEASE
        Momentum = ta.linreg(close - avg(avg(highest(high,20), lowest(low,20)),
                                         sma(close,20)), 20, 0)
        Entry fires on the FIRST bar of a squeeze release, in the direction
        of the momentum value.

  L2  Session VWAP bias (institutional filter)
        long only if close > session VWAP, short only if close < session VWAP.

  L3  Higher timeframe trend filter
        15m EMA50 slope (rising = longs only, falling = shorts only).
        The 15m bar is always the LAST COMPLETED 15m bar (no lookahead).

  Risk layer
        ATR(14) stop (Wilder RMA, same as ta.atr) + R-multiple take profit.

Every value here is deliberately written to mirror the Pine v6 source line by
line so that a TradingView backtest and this engine must agree.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np
import pandas as pd


# --------------------------------------------------------------------------- #
#  Configuration
# --------------------------------------------------------------------------- #
@dataclass
class Config:
    # ---- squeeze momentum (LazyBear defaults) ----
    bb_len: int = 20
    bb_mult: float = 2.0
    kc_len: int = 20
    kc_mult: float = 1.5

    # ---- filters ----
    use_vwap_filter: bool = True
    vwap_anchor: str = "session"          # "session" (resets each RTH day)
    htf_ema_len: int = 50
    htf_minutes: int = 15
    use_htf_filter: bool = True

    # ---- session filter (exchange local time, minutes from midnight) ----
    entry_start_min: int = 9 * 60 + 45     # 09:45
    entry_end_min: int = 15 * 60 + 45      # 15:45  (no new entries after)
    flatten_min: int = 15 * 60 + 55       # 15:55  (flat before the bell)
    min_minutes_to_flat: int = 0          # do not open a trade with less runway
    mom_slope_confirm: bool = False       # long needs mom > mom[1] (rising momentum)
    mom_strength_atr: float = 0.0         # |momentum| >= k * ATR  (k = 0 -> off)

    # ---- risk ----
    atr_len: int = 14
    atr_stop_mult: float = 2.0            # stop = 2.0 * ATR
    rr: float = 2.0                       # take profit = 2R
    risk_pct: float = 0.005               # 0.5% of equity per trade
    max_trades_per_day: int = 3
    daily_loss_stop_pct: float = 0.02     # stop trading the day at -2% of START balance
    trail_stop: bool = False              # optional ATR trail (off = reproducible)

    # ---- execution ----
    slippage_ticks: float = 0.01          # per side, in price units
    tick_size: float = 0.01
    commission_per_unit: float = 0.0

    # ---- prop-firm simulation ----
    account_size: float = 100_000.0
    ftmo_daily_loss_pct: float = 0.05     # FTMO 2-step
    ftmo_max_loss_pct: float = 0.10       # FTMO 2-step (static)
    ftmo_target_pct: float = 0.10         # phase 1
    ftmo_target_pct_p2: float = 0.05      # phase 2
    ftmo_min_days: int = 4
    consistency_reward_pct: float = 0.30  # FTMO account: best day <= 30% of total profit

    def label(self) -> str:
        return (f"atr{self.atr_stop_mult:g}x_rr{self.rr:g}_risk{self.risk_pct*100:g}%_"
                f"vwap{int(self.use_vwap_filter)}_htf{int(self.use_htf_filter)}")


# --------------------------------------------------------------------------- #
#  Helpers that reproduce Pine built-ins exactly
# --------------------------------------------------------------------------- #
def rma(series: pd.Series, length: int) -> pd.Series:
    """ta.rma / Wilder smoothing (alpha = 1/length), same seed as Pine."""
    return series.ewm(alpha=1.0 / length, adjust=False, min_periods=length).mean()


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr


def pine_stdev(series: pd.Series, length: int) -> pd.Series:
    """ta.stdev -> population stdev (biased, ddof=0), as used by LazyBear's code."""
    return series.rolling(length).std(ddof=0)


def pine_linreg_value(y: pd.Series, length: int) -> pd.Series:
    """
    ta.linreg(source, length, 0) -> the value of the OLS line at the CURRENT bar
    (offset = 0), i.e. a + b*(n-1) where the regression uses x = 0..n-1.

    Computed with rolling sums so it is O(n) instead of O(n*window).
    """
    n = length
    s1 = y.rolling(n).sum()
    idx = pd.Series(np.arange(len(y), dtype="float64"), index=y.index)
    sxy = (idx * y).rolling(n).sum()

    sum_x = n * (n - 1) / 2.0
    sum_x2 = (n - 1) * n * (2 * n - 1) / 6.0

    # relative x inside the window: x_rel_i = abs_index_i - (t - n + 1)
    start = idx - (n - 1)
    sxy_rel = sxy - start * s1

    denom = n * sum_x2 - sum_x**2
    b = (n * sxy_rel - sum_x * s1) / denom
    a = s1 / n - b * (sum_x / n)
    return a + b * (n - 1)


def session_vwap(df: pd.DataFrame, day_col: pd.Series) -> pd.Series:
    """Session-anchored VWAP on typical price, reset every session."""
    tp = (df["high"] + df["low"] + df["close"]) / 3.0
    pv = tp * df["volume"]
    g_pv = pv.groupby(day_col).cumsum()
    g_v = df["volume"].groupby(day_col).cumsum()
    return g_pv / g_v.replace(0, np.nan)


def rolling_slope(series: pd.Series, length: int, lookback: int) -> pd.Series:
    """slope of an EMA: ema[t] - ema[t-lookback] (positive => trending up)."""
    return series - series.shift(lookback)


# --------------------------------------------------------------------------- #
#  Indicator assembly
# --------------------------------------------------------------------------- #
def prepare(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """
    df must contain: ts (tz-aware datetime), open, high, low, close, volume
    and be sorted by ts, one row per bar, regular session bars.
    """
    d = df.copy()

    # ---- session bookkeeping (exchange local time) ----
    d["session_date"] = d["ts"].dt.date
    d["minute_of_day"] = d["ts"].dt.hour * 60 + d["ts"].dt.minute

    # ---- L1: squeeze momentum (LazyBear, fixed source) ----
    n, nn = cfg.bb_len, cfg.kc_len
    c = d["close"]
    basis = c.rolling(n).mean()
    dev = cfg.bb_mult * pine_stdev(c, n)
    upper_bb, lower_bb = basis + dev, basis - dev

    ma = c.rolling(nn).mean()
    rng = true_range(d).rolling(nn).mean()
    upper_kc = ma + rng * cfg.kc_mult
    lower_kc = ma - rng * cfg.kc_mult

    d["sqz_on"] = (lower_bb > lower_kc) & (upper_bb < upper_kc)
    d["sqz_off"] = (lower_bb < lower_kc) & (upper_bb > upper_kc)
    d["no_sqz"] = ~d["sqz_on"] & ~d["sqz_off"]

    hh = d["high"].rolling(nn).max()
    ll = d["low"].rolling(nn).min()
    mid = c.rolling(nn).mean()
    d["mom"] = pine_linreg_value(c - ((hh + ll) / 2.0 + mid) / 2.0, nn)

    # FIRST bar of a squeeze release (grey cross right after a black cross)
    d["squeeze_release"] = d["sqz_off"] & d["sqz_on"].shift(1).fillna(False)

    # ---- L2: VWAP bias ----
    d["vwap"] = session_vwap(d, d["session_date"]) if cfg.use_vwap_filter else np.nan

    # ---- L3: higher timeframe trend ----
    if cfg.use_htf_filter:
        d["htf_trend"] = _htf_trend(d, cfg)
    else:
        d["htf_trend"] = 0.0

    # ---- risk ----
    d["atr"] = rma(true_range(d), cfg.atr_len)

    # ---- final signals (bar-close, no lookahead) ----
    long_raw = d["squeeze_release"] & (d["mom"] > 0)
    short_raw = d["squeeze_release"] & (d["mom"] < 0)

    if cfg.use_vwap_filter:
        long_raw &= d["close"] > d["vwap"]
        short_raw &= d["close"] < d["vwap"]

    if cfg.use_htf_filter:
        long_raw &= d["htf_trend"] > 0
        short_raw &= d["htf_trend"] < 0

    # momentum-slope confirmation (LazyBear's "momentum is increasing" idea)
    if cfg.mom_slope_confirm:
        long_raw &= d["mom"] > d["mom"].shift(1)
        short_raw &= d["mom"] < d["mom"].shift(1)

    # momentum strength filter, normalised by ATR so it is scale free
    if cfg.mom_strength_atr > 0:
        strong = d["mom"].abs() >= cfg.mom_strength_atr * d["atr"]
        long_raw &= strong
        short_raw &= strong

    # NOTE: the session window is NOT applied here - it is applied per-bar in the
    # simulator (backtest.py) so that parameter sweeps cannot cache a stale
    # session filter. `raw_*` are pure signal conditions.
    d["raw_long"] = long_raw
    d["raw_short"] = short_raw
    d["sig_long"] = long_raw
    d["sig_short"] = short_raw
    return d


def _htf_trend(d: pd.DataFrame, cfg: Config) -> pd.Series:
    """
    Trend of the LAST COMPLETED higher-timeframe EMA.

    Built on the 1-minute frame, the HTF bar is resampled, the EMA is computed
    on closed HTF bars only, then mapped back to the 1-minute frame with a
    one-period shift (so the value used at minute t was fully known at t).
    """
    tf = f"{cfg.htf_minutes}min"
    base = d.set_index("ts")[["close"]]
    htf = base["close"].resample(tf, label="left", closed="left").last().dropna()
    ema = htf.ewm(span=cfg.htf_ema_len, adjust=False).mean()
    slope = ema - ema.shift(1)          # rising / falling of the HTF EMA
    # sign.shift(1) indexed at bucket-start B holds the slope of the HTF bar
    # that CLOSED at B -> fully known at minute B, so there is no lookahead.
    lag_sign = np.sign(slope).shift(1)

    idx = d["ts"]
    mapped = lag_sign.reindex(idx.dt.floor(tf)).values
    return pd.Series(mapped, index=d.index)

