# GoldPulse — Install Guide

## Download

**Direct APK:** https://github.com/victorvika/vjk_18/releases/download/goldpulse-v1.0.16/GoldPulse.apk

Release page: https://github.com/victorvika/vjk_18/releases/tag/goldpulse-v1.0.16

| | |
|---|---|
| Size | 9.6 MB |
| Package | `com.vjk.goldpulse` |
| Version | 1.0.0 (versionCode 1) |
| Min Android | 7.0 (API 24) |
| Target | Android 15 (API 35) |
| Signature | APK Signature Scheme v2 ✅ |
| Permissions | INTERNET, ACCESS_NETWORK_STATE only |

## Steps

1. Open the link on the phone.
2. Download `GoldPulse.apk`.
3. Android will warn "unknown app" — tap **Settings** → allow **Install unknown apps**
   for Chrome (or your file manager) → **Install anyway**.
4. Open **GoldPulse**. It loads `MGC=F` automatically.
5. If Play Protect warns, choose **Install anyway** — this is a self-signed debug build,
   which is normal for sideloaded APKs.

## First run

- The header shows the instrument toggle: **MGC** (default) or **GC**.
- Tap a timeframe: `1m 5m 15m 30m 1H 1D`.
- **REFRESH** re-pulls data. **AUTO 60s** toggles the timer.

## What you are looking at

```
GOLDPULSE
FundedNext · Rapid Daily 50K          [MGC] [GC]

2,701.30   +0.42%              UPTREND
MGC=F · MGC contract · delayed ~10m

┌──────────────────────────────────┐
│  candlestick chart               │  ← liquidity levels drawn as lines,
│  PDH / PDL / Asia H / Asia L     │    key levels labelled
└──────────────────────────────────┘
[1m][5m][15m][30m][1H][1D]

● CLEAR TO TRADE / STAND DOWN      ← prop-firm guard

RISK                    $250 / trade · 0.5%
[CONTRACTS 5] [STOP 3.5pt] [LOSSES LEFT 8]
ENTRY 2701.30  STOP 2697.80  TP1 2715.00  TP2 2711.80
LONG · swing low sweep · RR 2.9

SIGNAL CHECKLIST
· Sweep           12 detected
· Structure break  Bullish MSS
· HTF bias         bullish (4H)
· Setup            RR 2.9

RISK PER TRADE   [0.25%] [0.5%] [0.75%] [1%]

FUNDEDNEXT SESSION
Opens 5:00 PM CT · flat by 3:10 PM CT
```

### Reading the risk panel

- **CONTRACTS** — how many contracts the setup allows at your risk %. Computed from
  the stop distance and the instrument's point value (GC = $100/pt, MGC = $10/pt).
  If GC rounds to **0**, a gold hint appears telling you the MGC equivalent.
- **STOP** — stop distance in points and the dollar risk.
- **LOSSES LEFT** — `max loss limit ÷ risk per trade`. At 0.5% on a 50K account that
  is 8. This is the number that keeps the account alive.
- **STAND DOWN** — the guard has tripped (loss count, daily limit or max loss limit).
  No new setups are shown until the next session.

## Colour legend

| Colour | Meaning |
|---|---|
| 🟡 Gold dashed line | Last close |
| 🟡 Gold solid line | PDH (previous day high), buy-side liquidity |
| 🔵 Blue line | PDL (previous day low), sell-side liquidity |
| 🟡 / 🔵 thinner | Swing highs / lows |
| 🟢 Green candles | Bullish |
| 🔴 Red candles | Bearish |
| Green shaded band | Reward zone between entry and TP2 |

## Known behaviour

**It can show no setups for a long time — that is correct.**
The engine needs five things in order: a liquidity sweep, a structure break within 15
bars, an FVG, HTF alignment, and a kill-zone time window. Gold on a 15m chart often
goes hours without all five. The checklist at the bottom tells you which condition is
missing.

**Data is delayed ~10 minutes.**
Phase 1 uses Yahoo Finance. This is fine for planning and sizing, not for scalping.
Real-time comes with the Tradovate feed in Phase 2.

**"MGC feed empty — showing GC=F prices"**
Yahoo's micro-gold feed is thin. The app falls back to the full contract for the chart
but keeps using MGC maths for sizing, so your contract count stays correct.

**Market closed**
Gold runs Sun 5:00 PM – Fri 4:00 PM CT. Outside that, candles stop updating. Yahoo may
also return a short series, in which case the app says so rather than drawing a
misleading chart.

## What this app does NOT do

- **No order placement.** Execution stays on Tradovate. FundedNext permits EAs and
  bots, but this app is deliberately analysis-only so nothing can fire an order you did
  not place.
- **No copy trading.** Prohibited by FundedNext unless it is your own accounts.
- **No account login.** Phase 1 has no credentials and no backend.

## Troubleshooting

| Symptom | Cause |
|---|---|
| Stuck on "Loading MGC=F…" | Market closed, or no network |
| "Market data unavailable" | Yahoo rate-limited you; wait a minute and refresh |
| Chart looks flat | Fewer than 20 bars returned |
| Contract count always 0 | You are on GC at a risk % that cannot buy one contract — switch to MGC |
| App closes on launch | Send me the phone model and Android version |

## Rebuild it yourself

The APK is built in GitHub Actions from this repo:

```
Actions → "Build GoldPulse APK" → Run workflow
```

Every push that touches `app/**` also triggers a build. Artifacts live under the
Actions run, and the release is tagged `goldpulse-v1.0.<run number>`.

## Roadmap after this build

| Phase | What |
|---|---|
| 1 ✅ | Chart, LSMS engine, sizing, guard, Yahoo data |
| 2 | Tradovate auth + real-time WebSocket + `/md/getChart` |
| 2.5 | Alerts (price cross, new setup) via notifications |
| 3 | Journal, backtest, multi-timeframe, remote rule config |
