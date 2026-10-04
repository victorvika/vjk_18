# VJK-18 — ICT External-Liquidity Sweep → HTF FVG → LTF MSS → Breaker Model

A deterministic, **non-repainting** TradingView (Pine Script v6) implementation of the reversal model
demonstrated in the reference video:

```
EXTERNAL LIQUIDITY  →  gets SWEPT  →  price interacts with an HTF FVG  →  LTF produces an MSS
                   →  MSS creates a BREAKER / MITIGATION ZONE  →  price retraces into the zone
                   →  LIMIT ENTRY  →  SL beyond the sweep/swing extreme  →  TP at OPPOSING LIQUIDITY
```

The indicator does not just print "BUY"/"SELL". It **explains why the setup exists**: every signal is
traceable through liquidity → sweep → FVG → MSS → breaker → entry → SL → liquidity target, and any setup
that fails one of the mandatory conditions is rejected with the exact reason.

---

## Files

| Path | Content |
|---|---|
| `pine/VJK18_ICT_Model.pine` | the indicator (Pine v6, 2 160 lines, 115 inputs, 18 alert events) |
| `docs/01_PHASE1_METHODOLOGY.md` | interpretation of the trading model, causal chain, TF architecture |
| `docs/02_PHASE2_MATH_DEFINITIONS.md` | exact mathematical definition of every component |
| `docs/03_PHASE3_STATE_MACHINE.md` | state machine, transitions, invalidation rules |
| `docs/04_PHASE4_VALIDATION_MATRIX.md` | signal validation matrix + "do not" audit |
| `docs/05_PHASE6_7_COMPILE_REVIEW.md` | compile review, §1–40 compliance audit, known limitations |
| `tools/pine_check.py` | static analyzer used for the compile review (0 errors / 0 warnings) |

## Install

1. TradingView → *Pine Editor* → *Open* → *New indicator*.
2. Paste the whole content of `pine/VJK18_ICT_Model.pine`.
3. *Save* → *Add to chart*.
4. Load `5M` (or `1M` / `15M`) and leave **HTF Resolution = Auto**: the script picks `1H` for a 5M chart,
   `4H` for a 15M chart and `15M` for a 1M chart, exactly like the reference model. Manual override is
   available, and a warning appears if the chosen HTF is less than ~4× the chart timeframe.

## Alerts

TradingView cannot build dynamic messages with `alertcondition()`, so every event is dispatched through
`alert()` with a fully descriptive message (symbol, HTF, LTF, direction, liquidity, sweep price, MSS price,
entry, SL, TP1/TP2, R:R).

Create **one** alert per symbol with:

* Condition: **VJK-18 ICT Model** → *Any alert() function call*
* Then enable/disable the 11 event categories in input group **16 — Alerts**.

Event categories: external liquidity identified · BSL sweep · SSL sweep · HTF FVG confirmed · bullish MSS ·
bearish MSS · breaker created · BUY/SELL LIMIT activated · entry triggered · SL hit · TP1/TP2 hit ·
setup invalidated · setup rejected by the validation matrix.

## Recommended first run

1. Turn on **17 — Debug → Debug Mode**.
2. The *decision pipeline* table shows `1 … 8` for the tracked setup, and the event log lists the audit trail.
3. Open a historical setup on the chart and check that the boxes and labels tell the story in order:
   `BSL/SSL` level → `SWEEP` → `HTF FVG` → `MSS` → `BREAKER` → `SELL/BUY LIMIT` → `SL` → `TP1/TP2`.
4. Any rejection reads as `INVALIDATED: <reason>`; every reason maps to a rule in
   `docs/03_PHASE3_STATE_MACHINE.md` §3.5.

## Defaults that matter most

| Input | Default | Effect |
|---|---|---|
| HTF Resolution | Auto | 1M→15M, 5M→1H, 15M→4H, 1H→1D |
| Sweep mode | Rejection Close | penetrates the level **and** closes back inside |
| FVG mitigation rule | 50 % fill | an FVG is consumed once the HTF candle fills half of it |
| Sweep ↔ FVG relevance | required, ≤ 1 × HTF ATR | unrelated FVGs are rejected |
| Displacement | body ≥ 1 × ATR | small breaks are never promoted to an MSS |
| Maximum Sweep → MSS | 60 LTF bars | the MSS must be causally connected |
| Entry zone priority | Breaker → Mitigation → FVG | |
| Entry price | 50 % of the breaker zone | limit entry, touch fill |
| Stop loss | wider of sweep high / post-sweep swing + 0.25 × ATR | |
| Targets | internal → external → HTF liquidity | |
| Minimum R:R | 2.0 | setups below it are rejected |
| Active setups | max 1 BUY + 1 SELL | no chart spam |

## Honest scope notes

* The repository did not contain the reference video, so the implementation follows the written
  specification literally; every point where the methodology is visually obvious but not mathematically
  defined (breaker definition, mitigation block, displacement size, sweep/FVG distance, "meaningful" swing)
  is exposed as an **input**, documented in `docs/01 §1.7` and `docs/02`.
* No Pine compiler is available outside TradingView, so `docs/05_PHASE6_7_COMPILE_REVIEW.md` §6.3 lists the
  handful of things to confirm on the first load (built-in signatures, `max_bars_back`, execution time on very
  long histories). Everything the static analyzer can prove — brackets, indentation, undeclared identifiers,
  argument counts for every function **and every type constructor**, field existence, function/global
  declaration order, lookahead misuse, loops over empty arrays, object leaks — is verified and clean.
* A permanent trading edge is not claimed. The value of this repository is a faithful, auditable and
  reproducible encoding of the model, plus the tooling to keep it that way.
