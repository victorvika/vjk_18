# LSMS v3 — Pine to Kotlin Port Notes

Your indicator: **Liquidity Sweep + Market Structure Engine v3 "FX"** (798 lines, Pine v5).
Ported to Kotlin for **GC / MGC gold futures** on FundedNext Futures.

---

## 1. What The Indicator Actually Does

It is not a plot — it is a **complete trade-finding engine** with five stages:

```
1. Liquidity map      swing highs/lows, EQH/EQL, PDH/PDL, Asian range
2. Liquidity sweep    wick through a level, close back inside (grab)
3. Structure break    close beyond the last swing (BOS, or MSS = reversal)
4. FVG entry          enter at the fair value gap midpoint created by displacement
5. Liquidity target   nearest opposing pool as TP1, fixed R multiple as TP2
```

Plus four things that make it more than an indicator:

| Feature | What it does |
|---|---|
| **Kill-zone filter** | Only signals inside London (02:00–05:00) / New York (07:00–10:00) ET |
| **HTF bias filter** | Longs only above the 4H EMA50, shorts only below |
| **Risk guard** | Blocks signals after N losses or when the daily/max loss limit is near |
| **Simulated outcome tracker** | Every signal is auto-tracked to win/loss, bucketed by session and level type, and can block historically losing buckets |

That last one is unusual — it is a walk-forward self-audit inside the indicator. **Keep
it.** It is the most valuable part for a prop-firm account, and it maps directly onto
the drawdown meter the app already needs.

---

## 2. Why The Defaults Are Wrong For Gold

The script is explicitly FX-tuned ("v3 FX (EURUSD / GBPUSD)"). Six things break:

| # | Pine code | Problem on GC/MGC | Fix in the port |
|---|---|---|---|
| 1 | `contract = 100000` | That is a 100k FX lot. Gold is 100 oz (GC) / 10 oz (MGC). Using 100000 sizes **0.01 contracts** — a 1000× understatement. | `Instrument.pointValue`: GC = $100/pt, MGC = $10/pt. Sizing via `risk$ / (points × pointValue)`. |
| 2 | `pipSz` = 0.0001 | Gold has no "pip". Its tick is **0.10**. Stops measured in pips are meaningless. | All distances in **ticks/points**; `Instrument.tickSize = 0.10`. |
| 3 | `spreadPips = 1.0`, `spr = 1 pip` | 1 pip on gold ≈ 0.0001 = **$0.01**, i.e. free. Real GC spread is ~1 tick plus slippage. Cost was effectively zero. | `costTicks = 2.0` → $20 round trip on GC. Materially changes RR. |
| 4 | `minRiskPips = 4`, `maxRiskPips = 25` | 4 pips ≈ nothing on gold. Gold's 1m ATR is ~2–4 points and swings are 5–20 points. | `minStopPoints = 1.5`, `maxStopPoints = 15.0`. |
| 5 | `dayofmonth(time + 25200000, "America/New_York")` | Fixed 7-hour offset. Correct in summer (EDT), **wrong in winter** (EST) — the day rolls at 02:00 instead of 17:00. | Real timezone via `NewYorkClock`, so the reset is 17:00 ET year-round. |
| 6 | `acctSize = 10000`, `dailyLim = 5%`, `maxLim = 10%` | Generic. FundedNext Rapid Daily 50K is **$1,000 daily / $2,000 max = 2% / 4%**. At 10% the guard never fires before the account is dead. | `accountSize = 50000`, `dailyLossLimitPercent = 2.0`, `maxLossLimitPercent = 4.0`. |

### Also changed: session windows

Pine assumed an FX day (17:00 New York roll, 24×5 forex hours). Gold futures differ:

| | Pine (FX) | Gold futures (this port) |
|---|---|---|
| Exchange session | 24×5 | 18:00–17:00 ET, Sun–Fri |
| Prop flat-by | none | **15:10 ET — FundedNext auto-closes** |
| Asian range | 20:00–00:00 | kept, it is valid for gold |
| Kill zones | 02:00–05:00, 07:00–10:00 | kept (London / NY opens drive gold) |

`NewYorkClock.minutesUntilFlatBy()` gives the app a countdown to the 15:10 cutoff.

---

## 3. Proof: The Maths Matches Pine

`validation/parity_check.py` re-implements the Pine recurrences independently and
verifies 14 properties. All pass:

- `ta.rma` matches an exact recursion to 1e-12 and equals `ema(2N-1)` asymptotically
- `ta.rma` **differs** from a naive `ewm(adjust=True)` — proving the recursive form is required
- `ta.rsi` gives 100 / 0 / 50 on monotonic up / down / flat series
- `ta.rsi` reproduces Wilder's published first value (~70.5 on the textbook series)
- `ta.atr` is finite and positive after warm-up
- `ta.pivothigh` is confirmation-delayed by exactly `right` bars
- GC sizing: $500 risk ÷ 5-point stop = 1 contract; MGC = 10 contracts
- Tick values: GC $10, MGC $1

`validation/engine_spec.py` pins 21 behavioural rules (sweep detection, grab expiry,
guard timing, MLL trailing and lock, session minutes, GC/MGC sizing, the 0-contract
trap). All pass.

`validation/engine_smoke.py` is a line-for-line Python mirror of `LsmsEngine.kt`. It
runs 2,000 synthetic gold bars and asserts structural invariants: stops and targets on
the correct side, every price on the 0.10 tick grid, risk inside the min/max bounds,
contracts inside the cap, accepted setups clearing the min RR. 11/11 pass.

The generated `validation/golden_vectors.json` is asserted directly by
`SeriesParityTest.kt`, so the Kotlin series are checked against the Python reference
in CI.

---

## 4. Bugs Found And Fixed During The Port

Three real logic bugs, not just cosmetic:

**1. Sweep leaked into the next level's classification.** The original loop kept a
`bearGrab` flag outside the per-level scope, so once any level was grabbed, *every*
subsequent level in the same bar inherited `bearKey = true`. Rewritten so each level
is answered independently and removals are collected then applied.

**2. Sweep was consumed even when no setup fired.** Pine clears `bullSwpBar := na` only
inside the `if longOK` block. Clearing it unconditionally means a sweep that breaks
structure as a BOS (not MSS) can never produce a later MSS — signals silently vanish
in `"MSS only"` mode. Fixed to clear only when the trigger was actually evaluated.

**3. The nearest-liquidity search had no direction.** `nearestLvl(side, px)` in Pine
takes the price and filters correctly, but the first Kotlin draft picked the nearest
level regardless of whether it sat above or below the entry — producing negative
reward. Now `nearestAbove()` for longs and `nearestBelow()` for shorts.

Plus one timezone bug (§2.5) and one performance bug (`indexOfFirst` inside the bar
loop was O(n²) on the HTF series; now a binary search).

---

## 5. Not Ported (and why)

| Pine construct | Status | Reason |
|---|---|---|
| `table.new` dashboard | Partial | App renders its own Compose UI; the data (`LsmsResult`) is exposed instead |
| `line.new` / `label.new` / `box.new` | Out of scope here | These are draw calls — the Compose chart layer consumes `LsmResult.levels` / `.setups` / `.fvg` |
| `alertcondition` | Replaced | App-side `AlertEngine` fires on new `Setup` entries |
| `learnOn` / `bucketNeg` | Wired but off | Stats are computed; the blocking gate defaults to off until you have ≥25 trades per bucket |
| `request.security` for HTF zones | Partial | `HtfBias` covers the bias EMA; HTF FVG zone resampling is stubbed for Phase 2 |

---

## 6. Recommended Settings For FundedNext Rapid Daily 50K

```
Account size              50,000
Risk per trade            0.5%   ($250 → 8 losses of room against a $2,000 MLL)
Daily loss limit          2.0%   ($1,000 — matches the firm's soft breach)
Max loss limit            4.0%   ($2,000 — matches the EOD trailing MLL)
Max losses per day        2      (prop-appropriate; the Pine default of 2 is right)
Max contracts             4      (Rapid Daily 50K = 4 mini / 40 micro)
Cost per round trip       2 ticks ($20 on GC, $2 on MGC)
Min stop                  1.5 points
Max stop                  15 points
Target                   3.0 R
Min RR to liquidity       2.5 R
Setup window              15 bars
Kill zones                ON  (02:00–05:00 and 07:00–10:00 ET)
HTF bias                  ON  (4H EMA50)
Require FVG               ON
Min displacement          0.8 × ATR
Max signals per day       2
```

### Sizing reality check — measured, not assumed

The smoke test produced a real setup on synthetic gold data: **0 contracts**.

```
bar 1205 SHORT entry 2720.20 stop 2723.50 tp2 2709.70
risk 3.50pt  0 contracts  RR 4.97  [Swing High]
```

Verified across the matrix:

| Instrument | Risk | 3.5pt stop | 5pt stop | 10pt stop |
|---|---|---|---|---|
| GC | 0.5% ($250) | 0 | **0** | 0 |
| GC | 1.0% ($500) | 1 | 1 | 0 |
| MGC | 0.5% ($250) | 7 → capped 4 | 5 → capped 4 | 2 |
| MGC | 1.0% ($500) | 14 → capped 4 | 10 → capped 4 | 5 → capped 4 |

Two conclusions:

1. **At 0.5% risk on 50K, GC is unusable.** Every mini signal reads "0 contracts".
   The size is arithmetically right but practically useless.
2. **MGC is the workhorse at this risk level**, and it hits the 40-micro cap rather
   than running out of room.

So `Sizing.kt` was added: when the primary instrument rounds to zero it returns the
**micro-equivalent** with a plain-language hint, instead of a bare "0".

This is exactly the trade-off discussed for account size: **the 50K plan exists so you
can trade micros with room, not so you can trade minis recklessly.**

---

## 7. Files

| Path | Purpose |
|---|---|
| `strategy/lsms/Instrument.kt` | GC/MGC contract specs, tick maths |
| `strategy/lsms/LsmsConfig.kt` | All tunables + `validate()` |
| `strategy/lsms/Series.kt` | Pine-exact SMA/EMA/RMA/RSI/ATR/pivots |
| `strategy/lsms/Model.kt` | Bar, levels, setups, results |
| `strategy/lsms/LsmsEngine.kt` | The five-stage engine |
| `strategy/lsms/HtfBias.kt` | `request.security(close[1])` equivalent |
| `strategy/lsms/NewYorkClock.kt` | DST-safe session and day-roll maths |
| `strategy/lsms/Sizing.kt` | Contract sizing + micro fallback + losses-remaining |
| `validation/parity_check.py` | Pine maths parity, generates golden vectors |
| `validation/engine_spec.py` | 18 behavioural rules |
| `app/src/test/.../SeriesParityTest.kt` | JUnit asserts against the golden vectors |

---

## 8. Open Question For You

The FX version sizes in **lots**; gold sizes in **contracts**. The port outputs an
integer contract count. Two decisions I need from you:

1. **Do you trade GC, MGC, or both?** If both, the app should show the MGC-equivalent
   when GC rounds down to 0 — otherwise at 0.5% risk every GC signal will read
   "0 contracts" and look broken. `Sizing.suggest()` already does this; the question
   is which instrument the chart defaults to on a 50K account.
2. **Should the guard count simulated losses, real Tradovate fills, or both?** Pine
   uses its own simulated tracker (`autoGuard`). Once the Tradovate `user/syncRequest`
   read-only feed is wired in Phase 2, real fills are more accurate — but the trader
   may also be taking trades the app never saw.
