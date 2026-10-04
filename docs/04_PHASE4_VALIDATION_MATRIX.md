# PHASE 4 — SIGNAL VALIDATION MATRIX

The primary signal exists **only** when every mandatory condition is satisfied. Each row below names the
condition, the exact test in the code and the rejection reason produced when it fails.

## 4.1 SELL model

| # | Condition | Required | Code test | Rejection reason |
|---|---|---|---|---|
| 1 | External Buy-Side Liquidity | YES (`i_reqExternal`) | confirmed HTF pivot high / HTF range high / equal highs, not already raided, not stale | candidate never created — no alert |
| 2 | Relevant HTF FVG (bearish) | YES | 3-candle imbalance on closed HTF candles, `dir = −1`, unmitigated, and `linked OR inside OR near` | `HTF FVG mitigated/invalidated before the entry zone` |
| 3 | BSL Sweep | YES | `H > level + pen` and the rejection rule of the selected sweep mode | setup waits at phase 3, then `external liquidity was not swept inside the validity window` |
| 4 | Sweep ↔ MSS causality | YES | `bar(MSS) > bar(PH) > sweepBar` and `bar(MSS) − sweepBar ≤ i_maxSweepMss` | `no MSS inside the Sweep -> MSS window (N LTF bars)` |
| 5 | Post-sweep LTF swing high | YES (`i_mssReqSwing`) | most recent confirmed internal swing high after the sweep | MSS not returned → setup keeps waiting |
| 6 | Bearish MSS (protected low broken) | YES | earliest logged internal CHoCH−/BOS− with `level ≤ protSwing` after `PH` | idem |
| 7 | Displacement | YES (`i_dispATR ≥ 0`) | `maxBody(leg) ≥ i_dispATR × ATR`, optional consecutive candles | break skipped (`minMssBar = bar+1`), no MSS |
| 8 | Sweep rejection guard | YES | `H ≤ sweepExt + i_mssMaxExt × ATR` until the MSS | `price extended beyond the sweep high by more than N ATR (sweep failed to reject)` |
| 9 | Bearish Breaker / Mitigation / FVG zone | YES | `fFindBreaker` in `[bar(PH) … bar(MSS)−1]`, zone low above the protected low; mitigation = last down candle in `[sweep…MSS]`; FVG = setup FVG | `no valid Breaker only zone after the MSS`, `no valid Breaker -> Mitigation -> FVG zone after the MSS`, `Confluence required: breaker and HTF FVG do not overlap` |
| 10 | Zone geometry | YES | `top > bot` | `invalid zone geometry` |
| 11 | Valid retracement | YES | `zone.bot − close > 0` and `≤ i_brkMaxDist × ATR` | `price already beyond the entry zone (no valid retracement)`, `entry zone too far from price (> N ATR)` |
| 12 | Valid SL | YES | reference = sweep high (or post-sweep swing / wider of both) + buffer, `SL > entry` | `invalid stop loss (below the sell entry)`, `stop-loss reference unavailable` |
| 13 | Opposing liquidity target | YES (`i_reqTp`) | nearest sell-side liquidity below the entry respecting the hierarchy | `no valid opposing liquidity target` |
| 14 | Minimum R:R | YES (`i_reqRR`) | `R:R ≥ i_minRR` (default 2.0) | `R:R 1.42 below minimum 2.00` |

## 4.2 BUY model

| # | Condition | Required | Code test | Rejection reason |
|---|---|---|---|---|
| 1 | External Sell-Side Liquidity | YES | mirrored | — |
| 2 | Relevant HTF FVG (bullish) | YES | mirrored | `HTF FVG mitigated/invalidated before the entry zone` |
| 3 | SSL Sweep | YES | `L < level − pen` + rejection rule | `external liquidity was not swept inside the validity window` |
| 4 | Sweep ↔ MSS causality | YES | `bar(MSS) − sweepBar ≤ i_maxSweepMss` | `no MSS inside the Sweep -> MSS window` |
| 5 | Post-sweep LTF swing low | YES | mirrored | — |
| 6 | Bullish MSS (protected high broken) | YES | earliest CHoCH+/BOS+ with `level ≥ protSwing` | — |
| 7 | Displacement | YES | mirrored | — |
| 8 | Sweep rejection guard | YES | `L ≥ sweepExt − i_mssMaxExt × ATR` | `price extended beyond the sweep low ...` |
| 9 | Bullish Breaker / Mitigation / FVG | YES | mirrored | `no valid ... zone after the MSS` |
| 10 | Zone geometry | YES | `top > bot` | `invalid zone geometry` |
| 11 | Valid retracement | YES | `close − zone.top > 0` and `≤ i_brkMaxDist × ATR` | `price already beyond the entry zone` |
| 12 | Valid SL | YES | reference − buffer, `SL < entry` | `invalid stop loss (above the buy entry)` |
| 13 | Opposing liquidity target | YES | nearest buy-side liquidity above the entry | `no valid opposing liquidity target` |
| 14 | Minimum R:R | YES | `R:R ≥ i_minRR` | `R:R x.xx below minimum y.yy` |

## 4.3 Rejections vs. invalidations

* A **rejection** happens at zone construction: the setup existed (sweep + MSS were real) but the trade did not
  satisfy the matrix. It fires the `reject` event (alert input 16: "Setup rejected by the validation matrix"),
  stores the reason in `setup.reject` and moves the setup to `SETUP_INVALIDATED`.
* An **invalidation** happens later (zone broken, stop taken before entry, retracement expired, FVG dead).
  It fires the `invalid` event.
* Neither can be revived. A rejected/invalidated setup never produces a later signal.

## 4.4 Explicit "do not" audit

| Must not | Implementation guarantee |
|---|---|
| treat every high/low as liquidity | liquidity only from HTF pivots / HTF range extremes / equal clusters (+ optional LTF-major fallback); internal LTF swings are never liquidity |
| treat every FVG as a setup | relevance filter (linked / inside / max distance) is mandatory by default |
| treat every BOS as MSS | MSS requires a post-sweep swing, the protected swing break, causality in time and displacement |
| generate a signal without a liquidity sweep | the sweep is a state transition; phases 3 → 4 → 5 cannot be skipped |
| generate a primary signal from the LTF MSS alone | the MSS is followed by `fBuildEntry()` whose gates include the FVG, the zone, the target and the R:R |
| enter immediately after the MSS | the limit is armed and can only fill from the next bar onward (except an explicitly enabled market entry) |
| use arbitrary fixed pip targets | every target is a liquidity level (internal → external → HTF) |
| use future candles | closed-bar gating + `lookahead_off` + confirmed pivots only |
| repaint historical signals | all state changes happen on `barstate.isconfirmed`; no `lookahead_on`; no negative offsets |
| create random order blocks | breakers/mitigation blocks are constrained to the leg between the post-sweep swing and the MSS break and validated against the protected swing |
| draw hundreds of irrelevant zones | bounded object lifecycle: ≤ 3 setups/direction, `i_maxZones` mental budget, zone box reused per setup, finished setups pruned |
| mix HTF and LTF structure states | three separate engines with separate arrays, never merged |
