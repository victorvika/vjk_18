# 02 — Prop Firm Analysis: இந்த strategy prop firm-க்கு சரியா?

*இதுவே user-ன் இரண்டாவது கேள்விக்கு நேரடி விடை: "high win rate for prop firm trading ku velum nalla ah analysis panni sollu"*

**முருகு விடை:** இந்த setup **prop firm-க்கு சரியானது** — ஆனால் "high win rate" என்ற கோட்பாடு prop firm-ல் **தவறான metric**. Prop firm-ஐ pass பண்ணுவது win rate அல்ல; **drawdown-ஐ limit-உள்ள தூளத்தில் வைத்திருக்க முடித்ததும், target-ஐ hit பண்ணியதும்** ஆகும்.

இந்த doc-ல்: (1) prop firm rules என்ன, (2) அவற்றின் math, (3) என் simulation-ன் verdict, (4) practical checklist.

---

## 1) FTMO rules (official site-லிருந்து verify பண்ணியது — Oct 2026)

🔗 https://ftmo.com/en/trading-objectives/

| Rule | **2-Step** (Challenge → Verification) | **1-Step** |
|---|---|---|
| Phase 1 profit target | **+10%** ($100k → $110k) | **+10%** |
| Phase 2 profit target | **+5%** | — |
| Max daily loss | **5% of initial capital** ($5,000) | **3%** ($3,000) |
| Max loss (total) | **10% static** — floor permanently $90,000 | **10% end-of-day trailing** |
| Drawdown type | Static (நகராது) | EOD trailing (உயரும், குறையாது) |
| Min trading days | **4** per phase | — |
| Time limit | **இல்லை** (unlimited) | **இல்லை** |
| Consistency rule | Funded account-ல் reward-க்கு: **Best day ≤ 30% of total profit** | Challenge pass-க்கே: **Best day ≤ 50% of total profit** |
| Profit split | 80% → 90% (scaling) | 90% |

### ⚠️ அதிகம் மறக்கப்படும் 3 விஷயங்கள்

1. **Daily loss = EQUITY-ன் மீது, balance-ன் மீது அல்ல.** "Balance + open positions P/L ± swaps − commissions". உங்கள் position open-ல் இருந்து $3,000 float-ல் இருந்தால், day start balance-லிருந்து $5,000-ஐத் தொடர்ந்து குறைந்திருந்தால் — **balance-ல் நேரடாக loss இல்லாவிட்டாலும் account fail**. ஒரு tick-க்கு மட்டும் touch பண்ணால் போதும்.
2. **Daily floor தினமும் reset ஆகும்** — 00:00 CET-ல், **அன்றைய balance** மீது 5% கழிக்கப்பட்டு. அதாவதே நல்ல நாளில் floor உயரும்; மோசமான நாளில் அதே $5,000.
3. **Consistency rule (Best Day)** — ஒரே நாளில் அதிகம் profit பண்ணினால், மற்ற நாட்களில் profit சம்பாதித்து best day-ஐ share-ஐ குறைக்க வேண்டும். இது breach அல்ல, ஆனால் **payout-ஐ block செய்யும்**.

### மற்ற prop firms (ஒரே போல pattern)

| Firm | Daily loss | Max DD | Type | Target P1 |
|---|---|---|---|---|
| **FTMO 2-Step** | 5% | 10% | Static | 10% |
| **FundedNext Stellar 2-Step** | 5% | 10% | Static | 8% |
| **Topstep ($100K)** | $2,000 (2%) | $3,000 (3%) | Intraday trailing | $6,000 (6%) |
| **The5%ers** | 4% | 5% | Static | 6% |

📌 **Common theme:** எல்லாவற்றிலும் **daily loss + max drawdown** இரண்டும் இருக்கு. Topstep போன்ற trailing-DD firm-களில் limit **இன்னும் கடுமையாக** — அதனால் risk-ஐ குறைவாக வைக்க வேண்டும்.

---

## 2) The math — $100,000 account-ல் எவ்வளவு safe?

```
$100,000 account
 ├─ Daily loss limit   = $5,000 (5%)   ← ஒரே நாளில் இதற்கு மேல் = FAIL
 ├─ Max loss (static)  = $10,000 (10%) ← இதற்கு மேல் எந்த நாளிலும் = FAIL
 └─ Phase 1 target     = $10,000 (+10%)
```

**Risk per trade கணக்கிடும் வழி:**

```
Risk/trade = 0.5%  →  $500 per trade  →  10 losing trades in a row = −5% (daily limit-ஐத் தொடும்)
Risk/trade = 1.0%  →  $1,000 per trade →  5 losing trades  = −5%  ⇒ ஒரே நாளில் FAIL வாய்ப்பு
Risk/trade = 2.0%  →  $2,000 per trade →  2-3 losing trades = −5%  ⇒ நிச்சயம் FAIL
```

**எனவே prop firm-ல் "2% rule" கூட வரம்பு — 0.5%–0.75% உள்ளே இருக்க வேண்டும்.** இது என் simulation-லும் உறுதியாக வந்தது (கீழே பார்க்க).

**Target-க்கு எத்தனை trade வேண்டும்?**
- 3R target, 0.5% risk ⇒ ஒரு winning trade = +1.5% ($1,500)
- Phase 1 (+10%) ⇒ **~8-10 winning trade** தேவை (loss-களைவிட்டு)
- என் simulation-ல் ஒரு வருடத்தில் ~160 trade (5m chart) ⇒ இது realistic

---

## 3) என் FTMO simulation-ன் முடிவு

**Simulation:** `backtest/backtest.py` — 1-வருட real 1-minute data (99,300 bars), signal close-ல் → fill next bar open, stop-first assumption, 1-tick slippage, equity-ஐ மீது FTMO rules (daily floor, static max loss, min 4 days, phase transition, consistency).

### 5-minute chart (ship செய்த config, risk 0.5%)

| Symbol | Trades | Win% | PF | Expectancy | Total P&L | Max DD | **FTMO 2-Step verdict** |
|---|---|---|---|---|---|---|---|
| QQQ | 167 | 35.9% | 1.12 | +0.082R | **+$6,511** | 11.9% | ✅ Phase 1 pass → Phase 2 pass → **FUNDED** |
| SPY | 164 | 37.2% | 1.24 | +0.154R | **+$12,743** | 5.7% | ✅ Phase 1 pass → Phase 2 pass → **FUNDED** |

### 1-minute chart (அதே settings)

| Symbol | Trades | Win% | PF | Expectancy | Total P&L | Max DD | **FTMO verdict** |
|---|---|---|---|---|---|---|---|
| QQQ | 289 | 23.9% | 0.91 | −0.061R | −$9,936 | 12.1% | ❌ **FAILED — MAX_LOSS (2025-05-14)** |
| SPY | 289 | 24.2% | 0.91 | −0.070R | −$10,037 | 15.0% | ❌ **FAILED — MAX_LOSS (2025-05-15)** |

> 👉 **இதுவே prop firm-க்கான முக்கிய படிவு: timeframe-ஐ மாத்தினால் account fail ஆகிறது.** 5m-ல் 36% win rate, 1m-ல் 24% win rate — இரண்டும் "low win rate", ஆனால் 5m-ல் edge positive, 1m-ல் negative.

### 🎯 Risk sensitivity (QQQ, 5m) — ஒரே signal, வெவ்வேறு risk

| Risk/trade | Total P&L | Max DD | Daily locks | **FTMO verdict** |
|---|---|---|---|---|
| 0.25% | +$3,313 | 6.1% | 0 | Phase 1-ல் இருக்கிறது |
| **0.50%** | **+$6,511** | 11.9% | 0 | ✅ **PASSED → FUNDED** |
| 0.75% | +$9,537 | 17.4% | 2 | ✅ PASSED → FUNDED |
| 1.00% | −$9,955 | 10.6% | 0 | ❌ **FAILED — MAX_LOSS (2024-12-04)** |
| 2.00% | −$9,956 | 11.3% | 2 | ❌ **FAILED — MAX_LOSS (2024-11-15)** |
| 3.00% | −$10,175 | 12.1% | 6 | ❌ **FAILED — MAX_LOSS (2024-11-13)** |

> 👉 **Signal சரியாக இருந்தாலும், risk 1% ஆக ஒரே அளவுக்கு ஒரே signal-ல் account fail.** இதுவே prop firm trading-ல் #1 காரணம்: **"signal சரி, ஆனால் risk அதிகம்"**.

### 🔬 Filter ablation — எந்த guardrail எவ்வளவு worth

| Variant | Trades | Win% | PF | Expectancy | Max DD |
|---|---|---|---|---|---|
| **FULL (எல்லாம்)** | 167 | 35.9% | 1.12 | **+0.082R** | **11.9%** |
| − VWAP filter | 182 | 35.2% | 1.06 | +0.047R | 13.7% |
| − HTF trend filter | 256 | 32.8% | 1.02 | +0.017R | 18.9% |
| − இரண்டும் | 306 | 34.0% | 1.05 | +0.037R | 20.0% |
| **EOD flat இல்லை (overnight)** | 129 | 17.8% | 0.64 | **−0.295R** | 14.1% |

> 👉 **Day-இல் flat ஆக வேண்டும் — இது signal-லிருந்து கிடைக்கிற மிகப் பெரிய single improvement.** Overnight வைத்தால் edge +0.082R → −0.295R (flip ஆகிறது). Prop firm-க்கு overnight hold-ம் weekend/rollover risk + FTMO-ன் "trading day" definition-ன் காரணமாக double risk.

### 📊 Day distribution (QQQ 5m, 1 வருடம்)

| Metric | Value |
|---|---|
| Trading days | 148 |
| Win days / Loss days | 60 / 88 |
| Best day | **+$1,644** (+1.64%) |
| Worst day | **−$1,623** (−1.62%) |
| Average day | +$44 |
| Consistency (best day ÷ total profit) | 25.2% → FTMO funded rule (≤30%) ✅ |

> 👉 **Win rate 36% இருந்தாலும் profit வருகிறது** — ஏனென்றால் average winner ≈ 2× average loser (3R target). இதுவே prop firm-க்கான real metric: **expectancy, win rate அல்ல**.

---

## 4) "High win rate" prop firm-க்கு தேவையா?

**தேவையில்லை — அது தவறான frame.**

| Metric | Prop firm-க்கு முக்கியத்தும் | குறைவானது |
|---|---|---|
| **Expectancy (R per trade)** | ✅ மிக முக்கியம் | |
| **Max drawdown** | ✅ Account-ஐ kill பண்ணுவதே இது | |
| **Profit factor** | ✅ | |
| Win rate | | 🔸 30-45% உள்ள system-ம் PF > 1.2 ஆக profit பண்ணும் |

நமக்கு 36% win rate, PF 1.12-1.24 → net positive. ஆனால் 36% win rate + 1.5R target (RR 1.5) ⇒ **expectancy negative** ⇒ account நாளுக்கு நாள் கரைகிறது. **RR-ம் win rate-ம் இரண்டும் சேர்ந்து தான் வேலை செய்கிறது.**

---

## 5) Prop firm trader-க்கான practical checklist

### ✅ செய்ய வேண்டியவை

| # | Rule | ஏன் |
|---|---|---|
| 1 | **Risk/trade ≤ 0.5%** (max 0.75%) | 1%+ ⇒ simulation-ல் direct FAIL |
| 2 | **Max 3 trades/day** | Overtrading ⇒ daily loss limit hit |
| 3 | **Day P&L −2% ஆனதும் day close** | 5% daily limit-க்கு buffer |
| 4 | **Session-இல் flat (overnight வேண்டாம்)** | +0.082R → −0.295R ஆக flip |
| 5 | **5-minute chart** | 1m-ல் same settings fail ஆகும் |
| 6 | **Entry window 10:00–15:45**, close-க்கு 45 min முன் stop | Chop-ஐ avoid + target-க்கு runway |
| 7 | **Win rate-ஐ target செய்யாது — expectancy-ஐ target செய்யுங்க** | 36% WR + 3R = profit |
| 8 | **Consistency-ஐ track செய்யுங்க** (best day ÷ total profit ≤ 30%) | Payout block ஆகாது |
| 9 | **News / high-impact event-ல் size குறை** | Stop hunt → daily limit hit |
| 10 | **Demo-ல் 20-30 days forward test** | 1 வருட backtest = guarantee அல்ல |

### ❌ செய்யக்கூடாதவை

- ❌ Risk 1%+ (எந்த signal-லும்)
- ❌ "இன்று 2% loss ஆனதும் இரு நாள் அடுத்து அதிகம்" — daily limit **தினமும் reset** ஆகும், ஆனால் **max loss reset ஆகாது**
- ❌ Overnight position (weekend risk + drawdown)
- ❌ Indicator-ஐ வாங்கி, அதன் settings-ஐ மாற்றாமல் பயன்படுத்துவது — சொந்த risk-ஐ define பண்ணுங்க
- ❌ Win rate 70%+ "AI indicator"-ஐ நம்புவது (விளக்கம் இல்லாத backtest = marketing)

---

## 6) இந்த setup-ன் real weaknesses (சொல்ல வேண்டியவை)

1. ⚠️ **Statistically proven edge அல்ல.** Bootstrap 95% CI: QQQ `[−0.15R, +0.32R]`, SPY `[−0.08R, +0.40R]` — zero உள்ளது. இது "thin but plausible" edge.
2. ⚠️ **1 வருடம், 2 US ETF, RTH only.** Forex/gold/crypto-ல் வேறு result வரும். Prop firm-ல் forex trade செய்யும் நீங்கள் → அதே instrument-ல் forward test பண்ணுங்க.
3. ⚠️ **Instrument-specific:** 5m grid-ல் positive OOS cells — QQQ **54%**, SPY **15%**. SPY-ல் edge மிக thin.
4. ⚠️ **Regime-dependent:** QQQ-ன் best quarter `+0.703R`, worst `−0.337R`. ஒரு range-bound market-ல் இது flat/negative ஆகும்.
5. ⚠️ **1-minute-ல் "amazing" வரும் config ஒரு knife-edge:** `momK=1.0` → −0.18R, `1.5` → +0.69R, `2.0` → **zero trades**. அது 28 trades/வருடம் மட்டும். Ship செய்ததோ **5-minute + 160+ trades/வருடம்** version.

---

## 7) TL;DR

| கேள்வி | விடை |
|---|---|
| Intraday-க்கு best TradingView indicator? | **Squeeze Momentum [LazyBear]** (+ VWAP + HTF filter + ATR risk) |
| அது legitimate ஆ? | ✅ ஆம் — open-source, 2014, 117K likes, repaint இல்லை, source code public |
| Prop firm-க்கு சரியா? | ✅ **ஆம்** — 5m chart, 0.5% risk, day lock, EOD flat ⇒ simulation-ல் இரு phase pass |
| High win rate தேவையா? | ❌ தேவையில்லை — **expectancy + drawdown control** தான் prop firm-ஐ pass பண்ணும் |
| 1-minute-ல்? | ⚠️ 5m-ஐ விட அதிக return, ஆனால் sample சிறு; 5m-ல் சிறப்பாக stable |
| மிகப் பெரிய risk? | 🚫 **1%+ = FAIL** (simulation-ல் நேரடி ஆ) |

📄 அடுத்து: `03-backtest-methodology.md` (data + assumptions + limitations) · `04-tradingview-setup.md` (பயன்படுத்தும் விதி)
