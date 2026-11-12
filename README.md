# GoldPulse

Android analysis app for **GC / MGC gold futures** on **FundedNext Futures**.

Built to replace a TradingView subscription for the parts that matter on a prop
account: the chart, the liquidity map, and — most importantly — the position sizing
and the drawdown guard.

**Download:** https://github.com/victorvika/vjk_18/releases/download/goldpulse-v1.0.16/GoldPulse.apk
**Install guide:** [INSTALL.md](INSTALL.md)

## What it does

- Candlestick chart for GC / MGC, 1m to 1D, with liquidity levels drawn on the price
- **LSMS engine** — liquidity sweep → market structure break → fair value gap entry →
  liquidity target, ported from a Pine Script indicator and retuned for gold futures
- **Contract sizing** for GC ($100/point) and MGC ($10/point), with an automatic
  micro fallback when the mini rounds to zero
- **Prop-firm guard** — daily loss limit, EOD-trailing max loss limit, losing-trade stop
- **"Losses left"** — `max loss limit ÷ risk per trade`, the number that keeps an
  account alive
- Session awareness for FundedNext: 5:00 PM CT open, flat by 3:10 PM CT

## What it does not do

It never places an order. Execution stays on Tradovate. The app shows the setup the
rules produce and the size your risk plan allows.

## Build

Built by GitHub Actions on every push to `app/**`:

```
Actions → "Build GoldPulse APK" → Run workflow
```

APK output: `app/build/outputs/apk/debug/app-debug.apk` (debug-signed, sideloadable).

Local build requires JDK 17 + Android SDK 35:

```bash
gradle :app:assembleDebug
```

## Documentation

| File | Contents |
|---|---|
| [BLUEPRINT.md](BLUEPRINT.md) | Full product blueprint — data sources, features, FundedNext rules, roadmap |
| [LSMS_PORT_NOTES.md](LSMS_PORT_NOTES.md) | Pine → Kotlin port audit: what changed, what was fixed, what was measured |
| [INSTALL.md](INSTALL.md) | Sideload instructions, UI guide, troubleshooting |

## Tests

| Suite | Count | What it covers |
|---|---|---|
| `SeriesParityTest` | 15 | Pine-exact SMA/EMA/RMA/RSI/ATR/pivots against golden vectors |
| `LsmsEngineTest` | 14 | End-to-end engine, tick grid, guard, session clock, sizing |

Plus offline references runnable without a JVM:

```bash
python3 validation/parity_check.py   # 14/14 Pine maths checks
python3 validation/engine_spec.py    # 21/21 behavioural rules
python3 validation/engine_smoke.py   # 11/11 structural invariants, 2000 bars
```

## Data

Phase 1 uses Yahoo Finance (`GC=F` / `MGC=F`, ~10 min delayed) — no API key, no login,
no backend. Phase 2 moves to the Tradovate API for real-time CME data from the
FundedNext account.

## Status

Phase 1 shipped. See [ROADMAP.md](ROADMAP.md) if present, or the roadmap section of
INSTALL.md.
