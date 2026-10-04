# PHASE 6 — COMPILE / ERROR REVIEW · PHASE 7 — RULE-BY-RULE AUDIT

File: `pine/VJK18_ICT_Model.pine` · Pine Script **v6** · 2 160 lines · 58 user functions · 4 user types
(`Liq`, `Fvg`, `Sw`, `Setup`) · 115 inputs in 17 groups · 18 alert event kinds.

There is no Pine compiler available in this repository, so the review was done with a purpose-built static
analyzer (`tools/pine_check.py`) plus a manual read-through of the whole file. Everything the analyzer can
prove is listed below; everything it cannot prove is listed in `§6.3` so you know exactly what to confirm on
the first load.

## 6.1 What the static analyzer proves (final run: 0 errors, 0 warnings)

```
$ python3 tools/pine_check.py pine/VJK18_ICT_Model.pine
file: pine/VJK18_ICT_Model.pine
lines: 2161   user functions: 58   user types: 4
ERRORS: none
WARNINGS: none
```

| # | Check | Why it matters for Pine |
|---|---|---|
| 1 | balanced `()`, `[]`, `{}` and quotes per logical line | syntax errors |
| 2 | no tab characters, every indentation a multiple of 4 | "mismatched input" / "unexpected indent" |
| 3 | every called function is either a declared user function, a built-in or a namespace member | "Undeclared identifier" |
| 4 | argument count of every user-function call **and every `Type.new()` constructor call** equals the declared parameter/field count (Liq 14, Fvg 12, Sw 4, Setup 45) | "Wrong number of arguments" |
| 5 | every `object.field` access exists in that type's field list | "Cannot find field" |
| 6 | no `lookahead_on`, no negative history offsets, no history operator on a `request.security` result or an object | repainting / illegal indexing |
| 7 | no global scalar is reassigned with `:=` from inside a user function (arrays and object fields are mutated instead, which is legal) | "Cannot modify global variable" |
| 8 | no function is called before its definition | "Undeclared identifier" |
| 9 | no function body references a global declared *below* it | "Undeclared identifier" |
| 10 | no leftover tokens after a constructor call | type errors |

Additional structural guarantees checked manually across the file:

* every loop over an array is wrapped in an `if arr.size() > 0` (or `if from <= size - 1`) guard — **44 loops**.
  This is essential in Pine: `for i = 0 to n - 1` **counts downwards** when `n = 0`, which would index
  `array.get(0)`/`array.get(-1)` on an empty array and abort the script at runtime.
* all `ta.*` calls (`ta.atr`, `ta.pivothigh`, `ta.pivotlow`) are executed unconditionally on every bar;
  only the state machine is gated behind `barstate.isconfirmed`.
* every chart object that is created has a delete path: liquidity lines/labels are released on sweep, on
  staling, and when the oldest object is dropped from the rolling array; FVG boxes follow `i_fvgMaxBox`;
  zone/breaker/mitigation boxes and step labels are deleted when a finished setup is pruned.

## 6.2 Section-by-section compliance (your §1 – §40)

| § | Requirement | Where it is implemented | Status |
|---|---|---|---|
| 1 | Core reversal model, SELL + BUY step lists | entire engine (`fCreateSetups` → `fAdvance`) | ✅ |
| 2 | MTF architecture 1H↔5M, 4H↔15M, 15M↔1M; auto + manual; warning if too close; HTF from `request.security` | group 01, `autoHtf()`, `tfTooClose`, dashboard row 17 + on-chart warning table | ✅ |
| 3 | External vs internal liquidity, external required by default | group 04, `fRegisterLiq` (HTF pivots / HTF range extremes / equal clusters), `i_reqExternal` | ✅ |
| 4 | Two separate structure engines, never mixed | `majHiLst/majLoLst` vs `intHiLst/intLoLst`, HTF engine separate | ✅ |
| 5 | Confirmed pivots only, configurable left/right bars, no future data | groups 02/03, `ta.pivothigh/pivotlow`, HTF pivot confirmation loop | ✅ |
| 6 | HH/HL/LH/LL classification, per timeframe, no repeated labels | `Sw` objects with a `label` field, `i_showMajSw`/`i_showIntSw` default **off** | ✅ |
| 7 | BOS / CHoCH with close confirmation, optional wick mode | `fStruct()`, `i_breakConf` (default Close) | ✅ |
| 8 | Liquidity sweep with full event record | `Liq` fields: price, kind, formation time, sweptBar, sweptPrice, isSwept | ✅ |
| 9 | 3 sweep modes, no double sweeps on one level | group 05, `fDetectSweeps` + `fMarkSwept` (isSwept is terminal) | ✅ |
| 10 | True 3-candle HTF FVG with stored lifecycle data | `fDetectHtfFvg`, `Fvg` object (top/bot/mid/dir/time/state/penetration/link) | ✅ |
| 11 | Sweep ↔ FVG relevance with a maximum distance (ATR or %) | `fFvgRelevant`, `i_fvgRequire`, `i_fvgDistMode/ATR/Pct` | ✅ |
| 12 | FVG lifecycle Fresh→Touched→Partial→Full→Invalidated, selectable rule | `fUpdateFvgLifecycle`, `i_fvgMitRule`, `f.lcState` | ✅ |
| 13 | LTF confirms the HTF setup, it does not search its own | LTF internal engine only feeds the MSS/breaker of an existing setup | ✅ |
| 14 | MSS definition (post-sweep swing, protected swing break, displacement) | `fMssScan` + `fDisplacement` | ✅ |
| 15 | MSS causality: `MSS bar > sweep bar`, max sweep→MSS bars | `sweepBar`/`mssBar`, `i_maxSweepMss`, event scan `> max(postBar, minMssBar)` | ✅ |
| 16 | Displacement filter (body/ATR, consecutive candles) | group 07, `i_dispSource`, `i_dispATR`, `i_dispConsec` | ✅ |
| 17 | Breaker block engine linked to the MSS, no arbitrary OBs | `fFindBreaker` (window = post-sweep swing → break bar, protected-swing validation) | ✅ |
| 18 | Mitigation block stored separately + entry-zone priority options | `fFindMitigation`, `i_zonePrio` (5 options incl. Confluence required) | ✅ |
| 19 | MSS arms, retracement enters (limit by default) | phase 6 `WAIT_FOR_RETRACE`, `fTryFill`, `i_entryTrig` | ✅ |
| 20 | Entry price models A–E + exact entry price displayed | group 10, `i_entryModel`, `i_entryPct`, entry label + dashboard | ✅ |
| 21 | SL tied to the sweep/swing extreme with ATR/ticks/% buffer | group 11, `i_slRef`, `i_slBufMode` | ✅ |
| 22 | Targets = liquidity, hierarchy internal → external → HTF | group 12, `fFindTargets` (3 tiers) | ✅ |
| 23 | R:R computation and minimum-R:R gate | group 13, `i_minRR` (2.0), `i_rrTarget`, rejection reason | ✅ |
| 24 | SELL state machine, exact sequence | `fAdvance` (+ `docs/03_PHASE3_STATE_MACHINE.md`) | ✅ |
| 25 | BUY state machine | same function, mirrored by `s.side` | ✅ |
| 26 | Invalidation rules before/after MSS and after entry | `fKillSetup` call sites, reasons table in docs/03 §3.5 | ✅ |
| 27 | One active setup per direction, configurable | `i_maxBull` / `i_maxBear`, `fActiveCount`, `fSetupOnLiq` | ✅ |
| 28 | No repainting | see §6.4 below | ✅ |
| 29 | Visual output for HTF / LTF / trade layers | liquidity lines, FVG boxes, MSS + sweep markers, breaker/mitigation boxes, entry zone, entry/SL/TP lines | ✅ |
| 30 | Minimal labels, only the allowed set | `BSL/SSL/PIV/RNG/LTF`, `SWEEP`, `HTF FVG`, `MSS`, `BREAKER`, `MITIGATION`, `SELL/BUY LIMIT`, `SL`, `TP1`, `TP2` | ✅ |
| 31 | Visual flow tells the story | every stage is labelled in causal order at the bar where it happened | ✅ |
| 32 | Dashboard with all required fields | group 15, 18-row table + TF warning row | ✅ |
| 33 | 15 alert conditions with full context in the message | group 16, `fire()` + `alertOn()` dispatch (18 kinds) | ✅ |
| 34 | Debug mode with the 8-step pipeline + `INVALIDATED: reason` | group 17, decision table + on-chart numbered steps + event log | ✅ |
| 35 | 17 input groups | groups 01–17 exactly as specified | ✅ |
| 36 | Performance: bounded loops, bounded objects, no per-bar heavy scans | engine gating (`scanNow`), rolling arrays with caps, ≤3 setups/direction, `max_*_count` limits | ✅ |
| 37 | "Do not" list | audited in `docs/04_PHASE4_VALIDATION_MATRIX.md` §4.4 | ✅ |
| 38 | Signal validation matrix (all-mandatory) | `fBuildEntry` gates, docs/04 | ✅ |
| 39 | Development process phases 1–7 | `docs/01…05` | ✅ |
| 40 | Final objective: traceable causal chain | every alert/log/reason string carries the chain | ✅ |

## 6.3 What the static analyzer cannot prove (verify on first load)

These are the only remaining unknowns; none of them can be checked without TradingView's own compiler:

1. **Built-in signatures.** `box.new`, `label.new`, `line.new`, `table.cell`, `table.merge_cells`,
   `str.format`, `alert()` are used with the documented v6 parameter order/names. If TradingView reports a
   signature error, it will name the exact line and parameter — the pattern used is the documented one.
2. **Runtime limits.** `max_bars_back = 500` is declared; the deepest history lookups are clamped to 490 bars
   (`fDisplacement`, `fFindBreaker`, `fFindMitigation`). If TradingView asks for a larger
   `max_bars_back`, raise it in the `indicator()` call.
3. **Execution time.** The heavy search (`fCreateSetups`) runs only when an HTF candle closes, a sweep
   happens or a setup slot is released — not on every bar. If you use very long histories, reduce
   `Maximum liquidity levels tracked` (04), `Maximum FVGs tracked` (06) or `HTF candle history depth` (01).
4. **Semantic subtleties** (tuple destructuring into fresh variables, object mutation inside functions,
   `array<label>`/`array<line>` fields inside a type, `switch` on a string) are all documented v5/v6 features
   and were written in the most conservative form available (no omitted constructor arguments anywhere —
   every `Type.new()` passes **all** fields explicitly).

**Before trusting any signal, do this check:** enable *Debug Mode* and confirm that on your instrument the
pipeline table walks `1 → 8` for at least one setup, and that every `INVALIDATED:` entry names a rule from
`docs/03 §3.5`. The reasons are the audit trail of the algorithm.

## 6.4 Non-repainting audit

| Risk | Mitigation in the code |
|---|---|
| future data in pivots | `ta.pivothigh/pivotlow` (confirmed after `right` closed bars) and HTF pivots that require `right` closed HTF candles |
| HTF data leaking | `request.security(syminfo.tickerid, htfTf, [high[1], low[1], open[1], close[1], time[1]], barmerge.gaps_off, barmerge.lookahead_off)` — the `[1]` plus `lookahead_off` means only *closed* HTF candles are used |
| intra-bar state changes | the whole engine is inside `if barOK` where `barOK = barstate.isconfirmed`; the HTF counters/ATR update under `htfNew and barstate.isconfirmed` |
| optimistic fills | a limit can only fill on a bar **after** the zone was created (`bar_index > s.zoneSetBar`), except an explicitly enabled market entry (which fills at the close) |
| same-bar SL/TP ambiguity | the stop is checked **before** the target inside a bar (pessimistic, never optimistic) |
| history rewriting | no `varip`, no `request.security_lower_tf`, no negative offsets, no `lookahead_on`; all object state transitions are latched (`isSwept`, `phase == PH_DONE`) |

## 6.5 Known design decisions & limitations (documented, not hidden)

1. **Fill deferral.** If the MSS bar itself already traded into the entry zone, the fill is *not* assumed on
   that bar; the setup waits for the next bar. Conservative by design.
2. **HTF sweep mode.** With `Sweep detection timeframe = HTF (confirmed)` the recorded sweep bar is the LTF
   bar where the HTF candle closed (the HTF high itself is exact). Use the default LTF mode if you need the
   exact sweep candle.
3. **Pending sweeps.** At most the last 20 sweeps without a matching FVG are buffered, and only the first
   sweep inside a given HTF candle is linked as the FVG's source.
4. **Gap handling.** One closed HTF candle is processed per chart bar. Keep the HTF/LTF ratio at 4× or more
   (the warning row tells you when you are below it).
5. **Mitigation block definition.** Since the reference material shows the zone visually but does not define
   it mathematically, the "failing candle" definition from docs/02 §2.8 is used and is exposed through
   input group 09 (enable/disable, window, zone shape). Change it there, not in the code.
6. **Confluence rule.** "Confluence required" intersects the breaker with the HTF FVG; if they do not overlap
   the setup is rejected with an explicit reason instead of silently falling back to one of them.
