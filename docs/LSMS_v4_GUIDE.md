# LSMS v4 Pro — User Guide

## What is this?

**LSMS v4 Pro** (`indicators/LSMS_v4_Pro.pine`) is the merged version of the LSMS v3 engine:

- **Brain (from LSMS v3, unchanged):** Liquidity map → Liquidity grab (sweep) → MSS/BOS → FVG entry → nearest-liquidity target, with kill zones, HTF bias, pip-aware SL/TP, lot sizing, risk/loss guard and the simulated outcome tracker.
- **Eyes (new in v4, original implementation of the concepts):**
  1. **Premium / Discount** dealing-range filter
  2. **Displacement Order Blocks** with volume-relative labelling
  3. **Internal CHoCH / CHoCH+** confirmation
  4. **Confluence Score (0–100)** — only setups that score at least *Min Score* can fire

`indicators/LSMS_v3.txt` is kept untouched as the reference/baseline version.

> This is an indicator, not a strategy and not financial advice. It does not place orders and its simulated tracker is only a rough filter — validate everything with the future strategy/backtest version (Option B) and on demo before risking capital.

---

## Install (TradingView)

1. Open TradingView → **Pine Editor** (bottom panel).
2. Delete the default template, paste the full contents of `indicators/LSMS_v4_Pro.pine`.
3. Click **Save** → **Add to chart**.
4. Recommended starting point: **EURUSD / GBPUSD, 5m or 15m** chart, defaults untouched.

To compare against v3: add v3 on a second chart layout (do not stack v3 + v4 + other heavy SMC suites on one chart — each uses up to 500 drawing objects and the chart will clutter/hit limits).

---

## The Confluence Score (max 100)

Computed on every sweep → MSS/BOS setup, **before** the signal fires:

| Component | Max | How points are earned (Long example; Short is mirrored) |
|---|---:|---|
| Liquidity sweep | 25 | Sweep of a key level (PDH/PDL, Asia H/L, EQH/EQL, RSI OB/OS swing) = 25; plain swing sweep = 12 |
| MSS displacement | 15 | MSS candle body ≥ 1.2 ATR = 15, ≥ 0.8 ATR = 12, ≥ 0.5 ATR = 8, else 5. A BOS instead of MSS earns 60% of that |
| FVG entry zone | 15 | FVG after the sweep ≥ 0.25 ATR = 15; smaller FVG = 10; no FVG = 0 |
| HTF bias | 10 | Aligned with HTF bias (or bias filter off) = 10; against = 0 |
| Premium/Discount | 8 | Entry in Discount (≤ 50% of dealing range) = 8; ≤ 61.8% = 4; in Premium = 0 |
| Order Block | 7 | Sweep tapped a live OB **or** the entry FVG overlaps an OB = 7 |
| Kill zone | 10 | Inside London/NY kill zone (or KZ filter off) = 10 |
| CHoCH / CHoCH+ | 10 | CHoCH+ after the sweep = 10; plain CHoCH = 5; none = 0 |

**Grades:** `85+ = A+` · `70–84 = A` · `55–69 = B` · `< 55 = C`

Default gate: **Min Score 70** (`Confluence Score (v4)` settings). Skipped setups show the reason in the dashboard's *Last skip* row, e.g. `Long: score 62 < 70`.

**Component modes** (each of Premium/Discount, Order Blocks, CHoCH+):

- `Off` — component ignored; it awards full points so the total stays comparable.
- `Score only` *(default)* — component only adds/removes points.
- `Hard filter` — setup is blocked unless the component confirms (e.g. Hard PD blocks longs in Premium even with a 90 score).

---

## New v4 modules in detail

### Premium / Discount
- Dealing range = last confirmed swing high/low from `Dealing-range pivot length` (default 50) pivots.
- Dashed **Equilibrium** line (50%) is drawn by default; full Premium/Discount shaded zones are optional (`Show Premium / Discount zones`).
- Dashboard row **Prem/Disc** shows current position, e.g. `Discount 34%`.
- Note: with a 50-pivot range the range updates slowly — that is intentional (it is a dealing range, not a session range).

### Order Blocks
- When structure breaks, the extreme candle of the breaking leg (searched up to `OB origin search` bars back, default 15) becomes an OB.
- A bullish OB lives until price **closes below** it; bearish until a close above (mitigation).
- Box label shows relative volume (e.g. `OB 1.8x` = OB candle volume vs its 20-period average) when the feed provides volume. On FX this is broker tick-volume — treat it as a hint, not truth.
- `Body-only OB zone` switches the zone from full candle to candle body.
- Confluence for a setup = the sweep tapped a live OB, or the entry FVG overlaps an OB on the trade side.

### Internal CHoCH / CHoCH+
- Internal pivots (default length 5) track the minor trend separately from the swing structure.
- **CHoCH** = internal trend flip. **CHoCH+** = stronger flip: bullish flip where the latest internal low is already *higher* than the previous low (bearish: latest internal high already *lower*).
- Scoring counts only a CHoCH/CHoCH+ that printed **after the sweep** and on/before the MSS bar.
- `Label internal CHoCH / CHoCH+` draws the internal labels (off by default to keep the chart clean). Dashboard row **Internal (v4)** always shows the last internal event.
- Dedicated alerts: `LSMS v4 Bullish CHoCH+` / `LSMS v4 Bearish CHoCH+`.

### Dashboard (new rows)
`Score (v4)` (last evaluated setup score + grade), `Prem/Disc`, `OB zones (v4)` (live counts + tap status), `Internal (v4)`.

### Alerts (10 total)
All 6 v3 alerts, plus: `LSMS v4 A+ Long (score >= 85)`, `LSMS v4 A+ Short (score >= 85)`, and the two CHoCH+ alerts above. LONG/SHORT signal labels also print `Score NN GRADE` and `| OB` / `| CHoCH+` tags when present.

---

## Suggested configurations

**Default / balanced (start here):** everything as shipped — Min Score 70, all three components on `Score only`, kill zones + HTF bias on, `Require an FVG` on.

**Strict (prop-firm style, fewer but cleaner signals):**
- Min Score **80**
- Premium/Discount → `Hard filter`
- CHoCH+ → `Hard filter`
- Max signals per day **1**, Risk per trade **0.25–0.5%**

**Loose (more signals, for studying/ journaling):**
- Min Score **55**, or untick `Only signal when score >= Min Score`
- `Setup trigger` → `MSS + BOS`

**v3-equivalence check:** set Min Score gate off (`Only signal...` unticked) and all three modes to `Score only` → v4 must produce the **same signals as v3** on the same chart. Use this to verify the merge didn't change the core engine.

---

## Validation checklist (do this before trusting it)

1. Paste into Pine Editor — it must compile with no errors.
2. Same chart/symbol/TF: run the v3-equivalence check above against `LSMS_v3.txt`.
3. Bar Replay through 2–3 weeks: watch that (a) equilibrium line tracks swing range, (b) OB boxes appear on breaks and die on close-through, (c) dashboard Score updates on each setup attempt, (d) `Last skip` explains blocked setups.
4. Journal at least 30–50 simulated outcomes per symbol/TF bucket before changing thresholds — the dashboard's simulated buckets (session / level kind) help here.
5. Only then consider the backtest/strategy conversion (Option B) for real statistics (win rate, profit factor, drawdown). The built-in simulated tracker assumes fixed +3R/−1R and cannot replace it.

## Known limitations

- Indicator only — no real orders, no Strategy Tester results.
- FX volume = tick volume; OB volume labels are indicative only.
- Dealing range (50 pivots) and internal pivots (5) are confirmed-pivot based, so they lag by design — no repainting, but no instant reaction either.
- Very early chart history (before enough pivots exist) scores Premium/Discount neutrally (4/8).
- Defaults are tuned for EURUSD/GBPUSD intraday; other symbols/timeframes need their own validation.
