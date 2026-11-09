# vjk_18 — LSMS TradingView Indicators

Pine Script (v5) Smart Money Concepts indicators for intraday FX (EURUSD / GBPUSD).

## Files

| File | What it is |
|---|---|
| `indicators/LSMS_v5_Gold_Pro.pine` | **Current version — for XAUUSD (Gold).** Same engine as v4, but all stop/risk logic is ATR-based (the old pip logic silently blocked every Gold setup), Premium/Discount uses a rolling lookback range (no more "113%"), and Gold lot size is auto-detected. Guide: `docs/LSMS_v5_GOLD_GUIDE.md`. |
| `indicators/LSMS_v4_Pro.pine` | LSMS v3 engine + Premium/Discount filter, displacement Order Blocks, internal CHoCH/CHoCH+ confirmation, and a 0–100 Confluence Score gate (signals need ≥ 70 by default, A+ at 85+). Best for EURUSD/GBPUSD. |
| `indicators/LSMS_v3.txt` | Previous version, kept as the untouched baseline/reference. Core flow: liquidity map → sweep/grab → MSS (close beyond swing) → FVG entry → nearest liquidity target, with kill zones, HTF bias, pip-aware SL/TP, risk/loss guard and simulated outcome tracking. |
| `docs/LSMS_v4_GUIDE.md` | Full v4 user guide: install steps, score breakdown, component modes, suggested configs, validation checklist. |

## Quick start

1. TradingView → Pine Editor → paste `indicators/LSMS_v4_Pro.pine` → Add to chart.
2. Start on EURUSD/GBPUSD, 5m/15m, default settings.
3. Read `docs/LSMS_v4_GUIDE.md` before changing thresholds.

## Notes

- Indicators only — no order execution, no Strategy Tester backtest (a strategy conversion is the planned next step).
- All events are evaluated on confirmed bars (no repainting by design).
- Not financial advice. Validate on demo / with proper backtesting before risking capital.
