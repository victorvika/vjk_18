# PHASE 3 — STATE-MACHINE ARCHITECTURE

## 3.1 Design

Every candidate trade is an **object** (`Setup`) with its own phase, its own liquidity reference, its own FVG,
its own MSS, its own zone and its own trade levels. The engine walks each setup through its phases once per
**closed** bar. This gives:

* complete traceability — each signal carries the liquidity → sweep → FVG → MSS → breaker → entry chain;
* no shared mutable "current setup" state, therefore the SELL and BUY machines can never contaminate each other;
* a bounded number of live objects (default 1 active setup per direction, configurable 1–3) and a bounded
  number of chart objects (zone box, entry/SL/TP lines, step labels) that are recycled when the setup ends.

Requested phase names and the internal phase ids:

| Spec state name | Internal | Meaning |
|---|---|---|
| `IDLE` | 0 | nothing tracked for this direction |
| `FIND_EXTERNAL_BSL` / `FIND_EXTERNAL_SSL` | 1 | scanning (implicit — runs whenever an HTF candle closes or a slot is free) |
| `BSL_IDENTIFIED` / `SSL_IDENTIFIED` | 2 | not a stored phase: it is the moment a setup object is created |
| `WAIT_FOR_HTF_FVG` | 2 | *(alias of the line above when the sweep has not happened yet)* |
| `HTF_FVG_ACTIVE` | 3 | external level + relevant HTF FVG known, waiting for the sweep |
| `WAIT_FOR_BSL_SWEEP` / `WAIT_FOR_SSL_SWEEP` | 3 | *(same phase — the wait is for the sweep of the tracked level)* |
| `BSL_SWEPT` / `SSL_SWEPT` | 4 | sweep recorded (`sweepBar`, `sweepExt`), waiting for the LTF MSS |
| `WAIT_FOR_LTF_MSS` | 4 | *(same phase)* |
| `BEARISH_MSS_CONFIRMED` / `BULLISH_MSS_CONFIRMED` | 5 | transient — the zone is built on the same bar |
| `CREATE_BEARISH_BREAKER` / `CREATE_BULLISH_BREAKER` | 5 | transient — `fBuildEntry()` runs immediately |
| `ENTRY_ZONE_ACTIVE` | 6 | limit order armed, zone drawn, waiting for the retracement |
| `WAIT_FOR_RETRACE` | 6 | *(same phase)* |
| `SELL_LIMIT_TRIGGERED` / `BUY_LIMIT_TRIGGERED` | 7 | limit filled, trade live |
| `SL / TP ACTIVE` | 7 | *(same phase, SL/TP monitored each bar)* |
| `TARGET_REACHED` / `STOP_HIT` / `SETUP_INVALIDATED` | 8 | terminal |

## 3.2 SELL state machine

```
                         ┌──────────────────────────────────────────────┐
                         │ IDLE  (no active bearish setup)              │
                         └───────────────┬──────────────────────────────┘
          external buy-side liquidity + relevant bearish HTF FVG available
                                         │  (also entered by the
                                         │   "sweep happened first" route)
                                         ▼
                 ┌───────────────────────────────────────────┐
                 │ HTF_FVG_ACTIVE  (phase 3)                 │
                 │  liquidation.isSwept == false             │
                 └───────┬───────────────────────────┬───────┘
        external BSL swept│                           │age > i_defSweepAge
        (per sweep mode)  │                           │or HTF FVG mitigated/invalidated
                          ▼                           ▼
        ┌──────────────────────────────┐        ┌───────────────────┐
        │ SWEPT (phase 4)              │        │ SETUP_INVALIDATED │
        │  sweepBar / sweepExt stored  │        └───────────────────┘
        └───────┬───────────┬──────────┘
   MSS found w/ │           │ price > sweepExt + i_mssMaxExt*ATR
   displacement │           │ or bars(sweep→MSS) > i_maxSweepMss
                ▼           ▼
        ┌──────────────────────────────┐   ┌───────────────────┐
        │ MSS_CONFIRMED (phase 5)      │──▶│ SETUP_INVALIDATED │  (zone build failed a
        │  protSwing / swingPost saved │   └───────────────────┘   mandatory gate)
        └───────────────┬──────────────┘
                        │ fBuildEntry(): breaker → mitigation → FVG (+ validation matrix)
                        ▼
        ┌──────────────────────────────────────────┐
        │ ENTRY_ZONE_ACTIVE / WAIT_FOR_RETRACE(6)  │
        │  limit armed, zone + entry/SL/TP drawn   │
        └───────┬─────────────┬────────────────────┘
   H ≥ entry    │             │ close > zone.top  (zone broken)
                ▼             │ age > i_maxRetrace
        ┌───────────────┐     │ SL touched before fill
        │ TRADE (7)     │     ▼
        │  entry/SL/TP  │  ┌───────────────────┐
        └──┬────────┬───┘  │ SETUP_INVALIDATED │
   L ≤ TP2 │        │ H ≥ SL└───────────────────┘
           ▼        ▼
   TARGET_REACHED  STOP_HIT
```

## 3.3 BUY state machine

Exactly mirrored: `SSL_IDENTIFIED → HTF_FVG_ACTIVE → WAIT_FOR_SSL_SWEEP → SSL_SWEPT → WAIT_FOR_LTF_MSS →
BULLISH_MSS_CONFIRMED → CREATE_BULLISH_BREAKER → ENTRY_ZONE_ACTIVE → WAIT_FOR_RETRACE → BUY_LIMIT_TRIGGERED →
SL / TP ACTIVE → TARGET_REACHED | STOP_HIT | SETUP_INVALIDATED`.

Because the machine is driven by `s.side` and mirrored comparisons, there is only **one** implementation of
each rule — the buy and sell logic cannot drift apart.

## 3.4 Two entry routes into the machine

**Route B (spec order, primary)**

```
liquidity identified  →  relevant HTF FVG appears  →  setup created at phase 3
                      →  sweep  →  MSS  →  breaker  →  limit  →  fill
```

**Route A (live accommodation, switchable)**

In live markets the sweep often happens **before** the third FVG candle has closed. With
`i_allowSwFirst = true` (default) the sweep is parked in a pending-sweep buffer for
`i_swFirstWin` HTF candles. If the relevant FVG then appears inside that window, the setup is created
directly at phase 4 with the original sweep bar and extreme preserved. Nothing is retro-fitted and no signal
is generated before the FVG actually exists — the flag only decides whether a sweep that already happened may
still be used, and the discovery window is finite.

## 3.5 Invalidation rules (identical for both directions)

**Before the MSS**

| Trigger | Reason string |
|---|---|
| The setup's HTF FVG becomes mitigated or invalidated | `HTF FVG mitigated/invalidated before the MSS` |
| The external level is not swept in time (`i_defSweepAge` LTF bars) | `external liquidity was not swept inside the validity window` |
| Price extends more than `i_mssMaxExt × ATR` beyond the sweep extreme | `price extended beyond the sweep high/low ... (sweep failed to reject)` |
| No MSS inside `i_maxSweepMss` LTF bars | `no MSS inside the Sweep -> MSS window` |
| The zone could not be built (any mandatory gate fails) | the specific gate reason (e.g. `R:R 1.42 below minimum 2.00`) |

**After the MSS, before the fill**

| Trigger | Reason string |
|---|---|
| Close beyond the far edge of the zone | `close above the bearish breaker zone` / `close below the bullish breaker zone` |
| Stop level traded before the entry filled | `stop level taken before the entry filled` |
| Retracement age > `i_maxRetrace` LTF bars | `maximum retracement age expired` |

**After the fill**

| Trigger | Outcome |
|---|---|
| Stop hit (checked before TP inside a bar — pessimistic) | `STOP_HIT` |
| TP1 hit | TP1 alert (trade stays live for TP2) |
| TP2 hit (or TP1 when TP2 is empty) | `TARGET_REACHED` |

An invalidated setup is **never reused**: the liquidity object is already `isSwept`, the setup object is
terminal, and the search for the next setup restarts from fresh liquidity. A released slot can be taken by a
new opportunity on the next HTF close, sweep or completion event.

## 3.6 One active setup per direction (anti-spam)

```
fActiveCount(side) < (side == BUY ? i_maxBull : i_maxBear)     // default 1 each
fSetupOnLiq(price, side) == false                              // one setup per liquidity level
```

Completed setups are kept on the chart for `i_keepDone` occurrences per direction (default 2, `0` removes them
immediately) and are then pruned together with their chart objects.
