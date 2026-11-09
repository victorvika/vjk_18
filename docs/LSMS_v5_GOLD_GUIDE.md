# LSMS v5 Gold Pro — XAUUSD Guide

**File:** `indicators/LSMS_v5_Gold_Pro.pine` · **Chart:** XAUUSD, 5m (15m = fewer, cleaner signals)

> Honest note first: no indicator can guarantee income or fix a financial problem by itself, and Gold is leveraged and violent — a few bad trades can grow a debt instead of clearing it. Use this **on demo first**, risk money you can afford to lose, never borrowed/essential money. The indicator's job is only to give you disciplined, identical-quality setups; the result still depends on testing + your execution.

## Why v5 (what was broken on Gold in v3/v4)

1. **Pip logic removed.** v3/v4 measured SL in pips (max 25 pips). A normal Gold stop is $3–$10 = thousands of pips, so *every* Gold setup was silently rejected ("SL too wide"). v5 measures everything in **ATR**: valid SL = **0.3–3.0 × ATR**.
2. **Premium 113% fixed.** The v4 dealing range came from slow pivots, so price could print "Premium 113%". v5 uses a rolling 100-bar dealing range — always a real 0–100% value.
3. **Gold lot size auto.** Contract auto-detects XAUUSD = 100 oz (XAG = 5000); the lot printed on the signal label is the risk-based size for your account settings.

Everything else is the v4 engine: liquidity sweep → MSS displacement → FVG entry → nearest liquidity target, kill zones, HTF bias, Order Blocks, CHoCH+, Confluence Score (70+ to signal, 85+ = A+), risk/loss guard.

## Exact starting settings (XAUUSD)

Change **only these**; leave all other defaults:

| Setting | Value |
|---|---|
| Account size | Your *real* account size (demo = demo size) |
| Risk per trade | **0.5%** max (0.25% while learning) |
| Spread + slippage | **0.30** (Gold typical; check your broker) |
| HTF bias | **ON** (4H EMA) — in your older screenshot this was OFF; keep it ON |
| Min Score | **70** |
| Max signals per day | **2** |
| Chart indicators | **LSMS v5 only** — remove LuxAlgo + SR-IFVG3 (3 suites = clutter + wrong conclusions) |

Trade windows are the London (02:00–05:00 NY) and New York (07:00–10:00 NY) kill zones — roughly **12:30–15:30 IST** and **17:30–20:30 IST** (shifts 1 hr with US daylight saving). Outside these, the indicator blocks signals by design.

## How to build real confidence (2–4 weeks, no real money)

1. **Demo account**, XAUUSD 5m, settings above.
2. Take **only A (70+) and A+ (85+)** signals. No manual extra trades.
3. Journal every signal (even skipped ones you liked): date, score, session, result in R.
4. After **30+ trades**, check: win-rate, average R, worst losing streak. Average R above ~+0.2R after spread = promising; below 0 = do not go live, change nothing emotionally — bring the numbers back and we tune or drop it.
5. Only if demo is positive: start real with the **smallest lot (0.01)**, same rules, for another 30 trades.

**Hard safety rules:** stop for the day after 2 losses (the indicator's guard does this); never increase lot to "recover"; never trade news spikes (CPI/NFP/FOMC minutes Gold can jump $20+ through stops).

## If it still shows no signals on Gold

Check in order: (1) Are you inside a kill zone? (2) Dashboard *Last skip* row tells the exact blocker — e.g. `SL too wide 3.4 ATR` means skip was correct on a wild candle. (3) *HTF bias* must not say `off`. (4) *Score* shows `-` until the first sweep→MSS attempt happens — on 5m that can take hours; that patience is the system working, not broken.
