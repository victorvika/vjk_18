# TradingView Indicator Building Essentials

A home for the fundamentals and reusable resources used to build TradingView
indicators with Pine Script.

```
tradingview-indicator-building-essentials/
├── README.md                          <- you are here
├── Arena_AI_ICT_Sequence_Model.pine   <- the indicator (Pine Script v6)
└── tools/
    ├── pine_check.py                  <- static sanity checker for Pine sources
    └── simulate_model.py              <- reference simulation + self tests
```

---

# Arena AI - ICT Sequence Model

A Pine Script v6 indicator that reproduces **one complete institutional
sequence** instead of firing isolated signals:

```
EXTERNAL RANGE LIQUIDITY
  -> LIQUIDITY SWEEP
    -> HTF FAIR VALUE GAP            (context)
      -> LTF MARKET STRUCTURE SHIFT  (with displacement)
        -> BREAKER BLOCK             (primary POI)
          -> LIMIT ENTRY             (retracement into the breaker)
            -> STOP LOSS             (beyond the sweep extreme)
              -> OPPOSITE-SIDE LIQUIDITY TARGET
```

No RSI, no MACD, no stochastic, no moving averages and no generic "smart money"
features. A `BUY LIMIT` / `SELL LIMIT` label is printed only when **every** link
of the chain above is confirmed, in order.

## Quick start

1. Open TradingView → **Pine Editor** → *Open* → **New indicator**.
2. Delete the template, paste the contents of `Arena_AI_ICT_Sequence_Model.pine`.
3. **Save**, then **Add to chart**.
4. Keep the chart on the **LTF** of the mapping you selected (default `1H -> 5M`,
   so run it on a 5-minute chart).
5. Open *Settings → 1 - General* and turn on the dashboard to watch the chain
   build in real time.

> The script never repaints. While a bar is still forming, the dashboard shows
> the *developing* state; every drawn signal is confirmed on bar close and is
> never moved or deleted afterwards.

## Timeframe framework

| Preset        | HTF (context)      | LTF (execution)     |
| ------------- | ------------------ | ------------------- |
| `1H -> 5M`    | 1 hour             | 5 minutes (default) |
| `4H -> 15M`   | 4 hours            | 15 minutes          |
| `15M -> 1M`   | 15 minutes         | 1 minute            |
| `Custom`      | any input          | any input           |

* The **HTF** supplies the external range/liquidity context and the HTF Fair
  Value Gap.
* The **LTF** supplies the sweep, structure, MSS, breaker, entry, stop and
  target.
* HTF values are read through `request.security(..., lookahead = barmerge.lookahead_off)`
  with `[1]` / `[3]` offsets, so only **closed** HTF candles are ever used.
  There is no future leakage.
* The banner in the dashboard turns orange if the chart timeframe does not match
  the configured LTF, or if the HTF/LTF pair is inverted.

## How a setup is built

| # | Stage                    | What must happen                                                                 |
|---|--------------------------|----------------------------------------------------------------------------------|
| 1 | External liquidity       | A major swing high/low (pivot strength 20 by default) becomes BSL/SSL           |
| 2 | HTF context              | An unmitigated HTF FVG in the same direction sits near that liquidity            |
| 3 | Sweep                    | Price wicks through the level and closes back inside it                          |
| 4 | Reclaim                  | Price reclaims the swept level within the reclaim window                         |
| 5 | LTF MSS                  | Price closes beyond the protected structure level with displacement               |
| 6 | Breaker                  | The last opposite candle of the displacement leg becomes the POI                 |
| 7 | Entry / SL / TP / RR     | Entry at the breaker midpoint, SL beyond the sweep extreme, TP at opposite liquidity, RR ≥ minimum |
| 8 | Retracement              | Price returns into the breaker → the limit is filled                            |
| 9 | Management               | Runs to TP1 / TP / invalidation                                                  |

Equal highs and equal lows are merged into a single liquidity pool using a
configurable price tolerance, and are labelled `EQH` / `EQL` on the chart.

## State machine

The model is a deterministic state machine, not a pile of independent
conditions. It only ever moves forward when the required event occurs:

```
IDLE
 └─ EXTERNAL_LIQUIDITY_FOUND
     └─ HTF_CONTEXT_CONFIRMED
         └─ WAITING_FOR_SWEEP
             └─ LIQUIDITY_SWEPT
                 └─ WAITING_FOR_LTF_MSS
                     └─ MSS_CONFIRMED
                         └─ BREAKER_CREATED
                             └─ ENTRY_ARMED
                                 └─ WAITING_FOR_RETRACEMENT
                                     └─ LIMIT_ENTRY_TRIGGERED
                                         └─ TRADE_ACTIVE
                                             ├─ TARGET_REACHED
                                             └─ STOP_HIT

any state -> SETUP_INVALIDATED | SETUP_EXPIRED
```

Invalidation covers: sweep not reclaimed in time, sweep → MSS window expired,
HTF context missing at the MSS, no breaker found, stop loss on the wrong side of
entry, RR below minimum, breaker invalidated before entry, entry window expired
and setup exceeded the maximum bars. The reason is always recorded and shown in
the dashboard and in debug mode.

## Inputs (21 groups)

| Group | Highlights |
|---|---|
| 1 - General | Dashboard on/off, signal labels, liquidity age limit |
| 2 - Timeframes | Mapping preset, custom HTF/LTF, require HTF context |
| 3 - Market Structure | Swing length, internal structure, HH/HL/LH/LL labels, close confirmation, lookback |
| 4 - External Liquidity | Pivot sensitivity, range lookback, max levels, external-only setups |
| 5 - Equal Highs / Lows | Tolerance mode (ATR / ticks / percent), minimum bars between points |
| 6 - Liquidity Sweep | Confirmation mode, minimum penetration, reclaim window, strict rejection strength, sweep → MSS window |
| 7 - HTF FVG | Detection, zones kept, minimum gap size, sweep ↔ FVG distance in HTF ATR |
| 8 - LTF MSS | Close vs wick confirmation, minimum break distance in ATR |
| 9 - Displacement | Body/range ratio, minimum range and body in ATR, valid window |
| 10 - Breaker Block | Primary POI toggle, search lookback, fill opacity |
| 11 - LTF FVG | Optional secondary confirmation and distance filter |
| 12 - Entry | 50% midpoint / proximal / distal / custom %, limit vs immediate model |
| 13 - Stop Loss | Sweep extreme / breaker distal / LTF swing, ATR and tick buffers |
| 14 - Take Profit | Nearest liquidity / furthest liquidity / fixed RR multiple, TP1 display |
| 15 - Risk / Reward | Minimum RR (1.0 – 20.0) |
| 16 - Setup Expiry | Sweep → entry bars, armed → entry bars, finished-setup retention |
| 17 - Visuals | Bull/bear/HTF colours, label size, line width |
| 18 - Dashboard | Position and text size |
| 19 - Alerts | Per-event alert toggles |
| 20 - Debug | Debug mode and full-chain table |

### Sweep confirmation modes

| Mode | Rule |
|---|---|
| Wick penetration | The wick trades beyond the level at all |
| **Wick + close back inside** (default) | The wick trades beyond it **and** the candle closes back inside |
| Strict rejection | As above, plus the rejection wick must be ≥ the configured ATR multiple |

### Displacement

`Body / range ≥ 0.50`, `range ≥ 0.80 × ATR` and `body ≥ 0.30 × ATR`. An MSS only
counts if a displacement candle occurred within the last 5 bars. Practical, not
punishing — tighten the ratio if you want fewer, higher-quality shifts.

## Visual hierarchy

Deliberately restrained: thin dotted liquidity lines with small `BSL` / `SSL`
labels, compact `SSL SWEEP` / `BSL SWEEP` and `MSS` labels, one translucent
breaker rectangle, subtle HTF FVG zones, and `BUY LIMIT` / `SELL LIMIT` only at
the moment the setup arms. Entry, stop, TP1 and TP are drawn as line-break plots
that exist only while a setup is live.

## Alerts

Thirteen `alertcondition()` events, all fired on confirmed bar close:

external liquidity detected · SSL sweep · BSL sweep · bullish MSS · bearish MSS ·
bullish breaker · bearish breaker · BUY LIMIT armed · SELL LIMIT armed ·
entry triggered · TP1 hit · target hit · stop loss hit · setup invalidated.

Create them from *Alert → Condition → Arena AI SMC*.

## Non-repainting guarantees

* Every state transition is gated by `barstate.isconfirmed`.
* HTF data uses `lookahead_off` plus `[1]`/`[3]` offsets — only closed HTF
  candles are read.
* Structure pivots come from `ta.pivothigh()` / `ta.pivotlow()`, which are
  confirmed-only by construction.
* Printed signals are never moved, deleted or repainted.
* Developing conditions (the live chain in the dashboard) are clearly separate
  from confirmed ones (labels, alerts and plots).

## Verifying the model

Pine cannot be executed outside TradingView, so this directory ships two tools
that check the logic before you paste it:

```bash
python3 tools/pine_check.py Arena_AI_ICT_Sequence_Model.pine
python3 tools/simulate_model.py
```

`pine_check.py` catches unbalanced brackets, bad indentation, locals escaping
their scope, duplicate declarations and calls made before a declaration.

`simulate_model.py` re-implements the model in Python and runs four tests:

1. a textbook bullish sequence must walk the whole chain in order and finish at
   the target (`rr 4.25` on the sample data);
2. the mirrored bearish sequence must walk the same chain on the sell side;
3. a sweep **without** an MSS must never arm or print a signal;
4. a setup under the minimum RR must be rejected for that reason.

Keep both files in sync if you change the Pine logic.

## Tuning notes

* **Too few setups?** Lower *External swing strength* (e.g. 20 → 12), widen the
  *sweep ↔ HTF FVG distance*, or raise *Max bars sweep → MSS*.
* **Too many setups?** Raise *External swing strength*, require HTF context,
  turn on displacement, or raise the *minimum RR*.
* **Signals that arm but never fill:** the entry is the breaker midpoint by
  default — switch to *Proximal edge* for shallower retracements.
* **Running on a different chart timeframe** than the configured LTF is allowed
  but the dashboard warns you; the LTF logic always assumes the chart *is* the
  execution timeframe.

## Known limitations

* One live setup per direction at a time (a bull and a bear setup can coexist).
* Trade management is bar-based: entry, TP1 and TP are evaluated on highs/lows
  of closed bars, so intrabar sequencing between SL and TP is approximated.
* The HTF FVG is used as a closeness filter around the liquidity event, not as a
  full multi-timeframe FVG inventory.
* The indicator is an analysis tool, not a strategy: it prints the plan and the
  RR, it does not simulate fills or position sizing.
