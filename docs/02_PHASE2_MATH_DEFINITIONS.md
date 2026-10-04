# PHASE 2 — EXACT MATHEMATICAL DEFINITIONS

Notation: `H`, `L`, `O`, `C` are the current bar's high, low, open, close. `HTF_H`, `HTF_L`, `HTF_O`, `HTF_C`
are the last **closed** HTF candle's values obtained with `request.security(..., lookahead_off)` and a `[1]`
offset. `ATR` = `ta.atr(14)` on the entry timeframe, `HTF_ATR` = Wilder ATR(14) computed on the closed HTF
candle series. `T = syminfo.mintick`.

---

## 2.1 Swing points (confirmed pivots)

A bar `p` is a **swing high** (LTF internal, using `li`, `ri`):

```
H[p] > H[p-k]   for all k = 1..li          (strictly higher than the left neighbours)
H[p] >= H[p+k]  for all k = 1..ri          (at least as high as the right neighbours)
```

A bar `p` is a **swing low** with the mirrored inequalities. The pivot only becomes **known** at bar
`p + ri`, i.e. after `ri` bars have closed — never earlier, so historical points never move.

* LTF internal pivots: `li = i_intLeft` (3), `ri = i_intRight` (3)
* LTF major pivots: `li = i_majLeft` (10), `ri = i_majRight` (10)
* HTF pivots: `i_htfMajLeft` / `i_htfMajRight` (3/3) evaluated on the closed HTF series

**Classification** (per engine, independent):

```
newHigh > previousHigh  →  HH      newHigh < previousHigh  →  LH
newLow  < previousLow   →  LL      newLow  > previousLow   →  HL
```

Each swing is stored as an object with a unique creation timestamp/bar, its price, its direction and its
label. The engines are stored separately (`majHiLst/majLoLst`, `intHiLst/intLoLst`) and are never combined.

## 2.2 Structure state, BOS and CHoCH

State `s ∈ {+1 bullish, −1 bearish, 0 neutral}`. The engine keeps the *latest confirmed* swing high `lastH`
and swing low `lastL`, plus the latches `hb`, `lb` ("this level has already been broken") that are reset when
a new pivot is confirmed.

Break test (with `i_breakConf`):

```
brkH = (Close mode)  C  > lastH        (Wick mode)  H > lastH
brkL = (Close mode)  C  < lastL        (Wick mode)  L < lastL
```

Transition (first matching wins; `bp` = the broken level):

```
if  brkH and not hb and lastH is not na:
        event = (s == +1) ? BOS  : CHoCH        ; s = +1 ; hb = true ; bp = lastH
if  brkL and not lb and lastL is not na:
        event = (s == −1) ? BOS : CHoCH         ; s = −1 ; lb = true ; bp = lastL
```

* **BOS** = a break *in the direction of the current state* (continuation).
* **CHoCH** = a break *against the current state* (protected swing broken).
* Every LTF internal event is appended to the event log `(bar, type, brokenLevel)` used later by the MSS
  scanner. The log is bounded to 250 entries.

## 2.3 External liquidity

A level is **external liquidity** when it satisfies all of:

1. **Origin** — it is one of
   * an HTF confirmed swing high/low (`i_htfMajLeft/Right`), or
   * the HTF range extreme over `i_htfRangeLb` closed HTF candles (a *new* extreme only, so it is
     registered once, not every HTF bar), or
   * (fallback, only if `i_ltfExtFall`) an LTF **major** swing,
   * "Equal highs / lows" clusters are merged into a single level: two levels of the same side less than
     `i_eqTol × HTF_ATR` apart collapse into one level whose price is the extreme of the cluster.
2. **Not already raided** — no closed HTF candle *after the bar that formed the level* has traded through it:

```
taken(level, side) = ∃ i > p_form :  (side = +1 and HTF_H[i] > level + T)
                                   or (side = −1 and HTF_L[i] < level − T)
```

   A level that is already `taken` is stored with `isSwept = true` and **can never produce a sweep event**
   (this is what prevents hindsight "sweeps" of levels that were already traded through before the indicator
   could know about them).
3. **Not stale** — its age must be ≤ `i_liqMaxAge` HTF candles (0 = infinite).

Each liquidity object records: `price, side(±1), kind, formation HTF time, isSwept, sweptBar, sweptPrice`.

*Internal liquidity* is deliberately **not** registered here: LTF internal swings live in a separate engine and
are used only for the MSS, the breaker leg and the first target.

## 2.4 Liquidity sweep

With `pen = i_sweepPen × ATR`:

```
touch(BSL)  = H > level + pen          touch(SSL)  = L < level − pen
```

Mode behaviour (input 05):

| Mode | Condition to mark `isSwept = true` |
|---|---|
| **Wick** | `touch` |
| **Rejection Close** (default) | `touch` AND `C < level` (BSL) / `C > level` (SSL) |
| **Strict** | the rejection close above **and** the *next* candle confirms: `C[1] < level` and (optionally) `H[1] ≤ sweepHigh` |

On a confirmed sweep the object records `sweptBar = bar_index` and `sweptPrice = H` (BSL) / `L` (SSL).
`isSwept = true` is terminal: a level can never be swept twice, so a single liquidity pool produces at most
one sweep event and therefore at most one setup.

When `i_sweepTf = "HTF (confirmed)"` the sweep is instead detected on the closed HTF candle
(`HTF_H > level + pen` and `HTF_C < level`), which is slower but stricter.

## 2.5 HTF Fair Value Gap

Three consecutive **closed** HTF candles (`n−2, n−1, n`):

```
Bullish FVG :  HTF_L[n] > HTF_H[n−2]      zone = [ HTF_H[n−2] , HTF_L[n] ]
Bearish FVG :  HTF_H[n] < HTF_L[n−2]      zone = [ HTF_H[n] , HTF_L[n−2] ]

top = upper bound, bot = lower bound, mid = (top + bot) / 2
size filter:  (top − bot) ≥ i_fvgMinATR × HTF_ATR
```

Stored per FVG: `top, bot, mid, direction, creation HTF time, mitigation state, penetration, paired sweep`.

**Lifecycle** (evaluated only when an HTF candle closes, so a sweep wick into the zone does not consume it):

```
pen (bullish) = clamp( (top − HTF_L) / (top − bot) , 0 … 1 )
pen (bearish) = clamp( (HTF_H − bot) / (top − bot) , 0 … 1 )

Fresh                → pen = 0
Touched              → pen > 0
Partially mitigated  → pen ≥ 0.5
Fully mitigated      → pen ≥ 1
Invalidated          → close through the zone (only reachable with the "Close" rule)
```

The FVG stops being usable (`mitigated = true`) when the selected rule triggers:

| Rule | Bullish condition | Bearish condition |
|---|---|---|
| Touch | `HTF_L < top` | `HTF_H > bot` |
| 50 % fill (default) | `HTF_L ≤ mid` | `HTF_H ≥ mid` |
| Full | `HTF_L ≤ bot` | `HTF_H ≥ top` |
| Close | `HTF_C < bot` → **invalidated** | `HTF_C > top` → **invalidated** |

**Relevance filter** (input 06) — an FVG only qualifies when at least one holds:

```
linked  : the FVG was created by the displacement candle of that very sweep (source linkage), or
inside  : sweepPrice ∈ [bot, top], or
near    : distance(sweepPrice, zone) ≤ maxD
          maxD = i_fvgDistATR × HTF_ATR   (ATR mode, default 1.0)
          maxD = sweepPrice × i_fvgDistPct / 100   (percent mode, default 0.5 %)
```

## 2.6 LTF Market Structure Shift (MSS)

For a **SELL** setup, given the sweep bar `S` and sweep extreme `E`:

```
1. post-sweep swing high :  PH = the most recent confirmed internal swing high with bar > S
                            (exists ⇒ "price created a meaningful LTF high after the sweep")
2. protected low         :  PL = the most recent confirmed internal swing low with bar < bar(PH)
3. structure break       :  the earliest logged internal event with
                              bar(event) > max(bar(PH), minMssBar)   and
                              type(event) ∈ {CHoCH−, BOS−}            and
                              brokenLevel(event) ≤ PL
4. displacement          :  maxBody(leg) ≥ i_dispATR × ATR  AND
                            ( i_dispConsec = 0  OR  consecutiveDirectional ≥ i_dispConsec )
                            leg = bars from bar(PH) to bar(event)
                            "Break candle" mode measures only the break candle's body
5. causal window         :  bar(MSS) − S ≤ i_maxSweepMss  (60 LTF bars)
6. failure guard         :  H > E + i_mssMaxExt × ATR  before the MSS ⇒ invalidate
                            ("price extended beyond the sweep extreme")
```

If the earliest qualifying break has no displacement, it is **skipped** (`minMssBar = bar + 1`) and the
scanner looks for a later break — a small break is never promoted to an MSS.

The BUY model mirrors every comparison (`PH` = post-sweep low, `PL` = protected high, bullish event
types, `brokenLevel ≥ PL`, `L < E + i_mssMaxExt × ATR` guard).

**MSS is the arming event, never the entry.**

## 2.7 Breaker block

Bearish breaker (sell model), searched in the window `[bar(PH) … bar(MSS) − 1]`:

```
candidate = a candle with C > O                       ("the bullish candle that produced the failed rally")
selection = the most recent such candle                (or the one with the highest H if "Highest traded")
pre-filter = candidate must be inside the last i_brkLookback bars
zone       = [L , H]        (Full range, default)
             [min(O,C) , max(O,C)]                       (Body)
             [min(O,C) , H]                              (Wick to body)
validation = zone low > PL        (input 08: "Breaker must hold above the protected low")
```

A bullish breaker (buy model) is the mirror: the most recent bearish candle in the window, zone validated
against the protected high, `zone top < PL`.

The breaker is **structurally linked to the MSS** by construction: it can only come from the leg between the
post-sweep swing and the break bar. Arbitrary order blocks are never drawn.

## 2.8 Mitigation block

Sell model: the **last down candle** (`C < O`) between the sweep bar (`sweepBar` or `sweepBar+1`, configurable)
and the MSS bar — the failed attempt to continue lower, which price retests from below after the break.
Buy model: the last up candle in the same window. Zone shape follows input 09 and is validated with the same
protected-swing rule as the breaker.

## 2.9 Entry zone selection and entry price

Priority (input 10): `1 Breaker`, `2 Mitigation`, `3 FVG`, **`4 Chain`** (default), `5 Confluence`.
(Those are the exact strings shown in the *Entry zone priority* input.)

```
5 Confluence : zone = [ max(bot), min(top) ] of breaker ∩ FVG ; requires min(top) > max(bot)
zone validation     : top > bot
                      near edge on the correct side of price:
                         sell :  near = zone.bot , dist = near − C > 0
                         buy  :  near = zone.top , dist = C − near > 0
                      dist ≤ i_brkMaxDist × ATR
                      dist ≤ 0 ⇒ "already beyond the zone" ⇒ market entry (if enabled) or invalidation
```

Entry price (input 10/20):

| Model | Sell | Buy |
|---|---|---|
| 50 % of zone (default) | `(top + bot)/2` | `(top + bot)/2` |
| Zone candle open | `O[candidate]` | `O[candidate]` |
| FVG midpoint | `mid` of the setup's HTF FVG | idem |
| Full zone | `bot` | `top` |
| Custom % | `top − pct×(top−bot)` | `bot + pct×(top−bot)` |

Trigger (input 10): **`Touch`** — a sell limit at `E` fills when `H ≥ E` (buy: `L ≤ E`), or
`Close beyond` — `C ≥ E` (buy: `C ≤ E`). Fills can only occur **from the bar after the zone became
active**, so no intra-bar hindsight fill is ever assumed (the only exception is an explicitly enabled
market entry, which fills at the close of the bar that created the zone).

## 2.10 Stop loss

```
reference (sell) =  E? sweepExt        (Sweep extreme)
                    swingPost          (Post-sweep swing, LTF)
                    max(sweepExt, swingPost)     (Wider of both, default)
reference (buy)  =  min(sweepExt, swingPost)     for "Wider of both"

buffer = i_slBufATR × ATR      (ATR, default 0.25)
       = i_slBufTicks × T      (Ticks)
       = C × i_slBufPct / 100  (Percent)

SL(sell) = reference + buffer      must satisfy  SL > entry      else the setup is rejected
SL(buy)  = reference − buffer      must satisfy  SL < entry      else the setup is rejected
```

## 2.11 Targets and R:R

Candidate liquidity for a sell = every level below the entry with `entry − level ≥ i_tpMinDist × ATR`:

| Tier | Source |
|---|---|
| 1 internal | LTF internal swing lows/highs (`intLoLst`, `intHiLst`) |
| 2 external | LTF **major** swing lows/highs (`majLoLst`, `majHiLst`) and non-HTF liquidity objects |
| 3 HTF | HTF-sourced liquidity objects (`kind` starts with "HTF" or "Equal") |

Already swept levels are excluded when `i_tpSkipSwpt` is on; stale levels are always excluded.

```
TP1 = nearest candidate of the first tier (in the configured hierarchy order) that can satisfy
      |entry − TP| ≥ i_minRR × risk      (only when the R:R gate applies to TP1)
TP2 = next candidate beyond TP1 ("Next nearest", any tier) or beyond TP1 in a higher tier ("Next tier up")
risk   = |entry − SL|
reward = |entry − TP|
R:R    = reward / risk
gate   = if i_reqRR and i_reqTp: reject the setup when the configured R:R target < i_minRR
```

## 2.12 Hard gates (a setup only exists when every one of these is true)

```
External liquidity exists (external filter ON unless disabled)
Relevant HTF FVG active          (not mitigated, not invalidated)
Liquidity swept                  (recorded sweep bar + extreme)
LTF MSS confirmed with displacement, after the sweep, inside the window
Entry zone (breaker / mitigation / FVG per priority) valid and on the correct side of price
Valid stop loss (correct side of the entry, tied to the sweep extreme)
Opposing liquidity target exists
R:R ≥ i_minRR
```

If any line fails, the candidate is rejected with an explicit reason string; no primary signal is produced.
