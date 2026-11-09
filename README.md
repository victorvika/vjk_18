# vjk_18 — LSMS TradingView Indicators

Pine Script (v5) Smart Money Concepts indicators for intraday FX (EURUSD / GBPUSD).

## Files

| File | What it is |
|---|---|
| `indicators/LSMS_v4_Pro.pine` | **Current version.** LSMS v3 engine + Premium/Discount filter, displacement Order Blocks, internal CHoCH/CHoCH+ confirmation, and a 0–100 Confluence Score gate (signals need ≥ 70 by default, A+ at 85+). |
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
