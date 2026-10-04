# PHASE 1 — INTERPRETATION OF THE TRADING METHODOLOGY

## 1.1 What the model actually is

The reference setup is a **reversal model that trades a failed raid on Higher-Timeframe liquidity**. It is not a
pattern scan and not a generic "SMC" indicator. Its premise is:

> Smart money needs resting orders. Those orders sit above **external** buy-side liquidity or below **external**
> sell-side liquidity. Price is driven into that liquidity (the *raid*), the move is rejected at a
> Higher-Timeframe imbalance (Fair Value Gap), and only then does the Lower Timeframe roll over. The roll-over
> (Market Structure Shift) leaves behind a failed order block — the **breaker** — which is the actual entry.

Therefore the trade is never taken at the sweep, never at the FVG, and never at the MSS. It is taken on the
**retracement into the breaker/mitigation zone** with a limit order, with the stop beyond the raid extreme and
the target at the *opposing* liquidity.

The single most important structural fact about this model is that **it is a chain, not a checklist**. A sweep
without a relevant HTF FVG is noise. An FVG without a sweep is an unfilled gap. An MSS without a preceding
sweep is an ordinary pullback. The signal only exists when the whole chain exists.

## 1.2 The causal chain (SELL model)

```
EXTERNAL BUY-SIDE LIQUIDITY
  (HTF swing high / HTF range high / equal HTF highs — a level that has NOT been traded through)
        │
        ▼
PRICE RALLIES INTO IT
        │
        ▼
SWEEP  (high trades through the level, price rejects / closes back inside)
        │
        ▼
HTF FAIR VALUE GAP  (bearish 3-candle imbalance, relevant to the sweep: the sweep happens into/near it)
        │
        ▼
LTF MARKET STRUCTURE SHIFT  (meaningful LTF high made after the sweep → protected low is broken with displacement)
        │
        ▼
BEARISH BREAKER  (the last bullish candle of the failed rally becomes resistance)
        │
        ▼
SELL LIMIT  (retracement into the breaker / mitigation zone)
        │
        ▼
SL  beyond the sweep high (or the post-sweep swing high, whichever is wider)
        │
        ▼
TP  at the next sell-side liquidity, then the next major sell-side liquidity
```

The BUY model is the exact mirror.

## 1.3 The five "traps" the model avoids (and therefore the indicator must avoid)

| Trap | Why it happens | How this implementation prevents it |
|---|---|---|
| Every high/low treated as liquidity | Most levels are internal noise | Liquidity is built from confirmed **HTF** swing points, HTF range extremes and equal-high/low clusters; internal LTF swings are used only for the MSS and the first target |
| Every FVG treated as a setup | FVGs are everywhere | The FVG must be **relevant**: linked to the sweep candle, or the sweep traded into it, or it is within a configurable sweep→FVG distance |
| Every BOS treated as MSS | Structure breaks happen constantly | MSS requires (a) a post-sweep LTF swing, (b) a break of the swing that this new swing protects, (c) the break must be later than the sweep, and (d) displacement |
| Signal without a liquidity sweep | The sweep is the *reason* for the trade | The sweep is a mandatory state-machine step; no sweep → no zone → no signal |
| Entry at the MSS | The MSS is the confirmation, not the entry | The MSS only **arms** the setup; entry is a limit order at the retracement into the breaker |

## 1.4 Timeframe architecture as demonstrated

The reference material uses a fixed HTF → LTF relationship:

| Higher Timeframe (context) | Entry timeframe (trigger) | Ratio |
|---|---|---|
| 1H | 5M | 12× |
| 4H | 15M | 16× |
| 15M | 1M | 15× |

**Rule implemented:** the HTF must be at least two "timeframe levels" above the entry timeframe
(enforced through the *HTF/LTF ratio* input, default 4×, with a chart warning when violated).
The HTF is always *auto-resolved* from the chart timeframe unless the user selects it manually:

| Chart TF | Auto HTF |
|---|---|
| 1M | 15M |
| 5M | 1H |
| 15M | 4H |
| 30M | 4H |
| 1H | 1D |
| 4H | 1D |
| 1D | 1W |

HTF data is always read from **real HTF candles** via `request.security()` — HTF candles are never
reconstructed from lower-timeframe data.

## 1.5 Why the HTF level is "external" and the LTF level is "internal"

Two independent structure engines run at the same time and are **never mixed**:

| Engine | Where it lives | Used for |
|---|---|---|
| **Major / Swing structure** | HTF (via `request.security`) + LTF major pivots | External liquidity, HTF structure, major targets, invalidation |
| **Internal structure** | LTF only | MSS, displacement, breaker leg, entry |

A sweep of an *internal* LTF low is not a setup; it is at most a step inside an ongoing leg.
The primary setup requires **external** liquidity unless the user disables that filter (input 04).

## 1.6 What the reversal "looks like" on the chart

```
                                   ┌─ HTF FVG (bearish)
   BSL ────────┐                   │
               │  ← sweep (wick     │
               │     through)  ┌────┴────┐
               ▼               │  raid   │
   ────────────┴───────────────┘         │
                                         │   ← LTF MSS (protected low broken with displacement)
                          ┌──────────────┘
                          │  BREAKER (last bullish candle of the failed rally)
                          ▼
                    ──────────────  ← SELL LIMIT (retracement into the breaker)
                          │
        SL above the raid │
                          ▼
                    ──────────────  ← TP1 internal SSL, TP2 external SSL
```

Everything above is drawn by the indicator, in order, with labels
`BSL → SWEEP → HTF FVG → MSS → BREAKER → SELL LIMIT → SL → TP1/TP2`.

## 1.7 Explicit interpretation decisions

The methodology is visually obvious but not always mathematically defined. Every such point was converted into
an **explicit, configurable input** instead of a hidden assumption:

| Visually obvious but undefined | Implemented as | Default |
|---|---|---|
| "meaningful" external level | confirmed HTF pivot (`L/R` bars), HTF range extreme, or equal-high/low cluster within N×HTF-ATR | HTF pivots 3/3, ATR tolerance 0.10 |
| "the sweep rejected" | sweep mode: wick / rejection close / strict rejection (next candle confirms) | Rejection Close |
| "the FVG is relevant to the sweep" | linked source candle, or sweep inside the zone, or within N×HTF-ATR | 1.0 × HTF ATR |
| "meaningful LTF high before the MSS" | post-sweep confirmed internal swing (`internal L/R` bars) | 3/3 |
| "displacement" | body ≥ N × ATR on the breaking leg, optional N consecutive candles | 1.0 × ATR |
| "the relevant bullish candle" (breaker) | last opposite-colour candle between the post-sweep swing and the break bar | "Most recent" |
| "mitigation block" | last same-side candle between the sweep and the break bar | enabled |
| minimum acceptable trade | minimum R:R gate | 2.0 |
| stop distance beyond the swing | ATR / ticks / percent buffer | 0.25 × ATR |
