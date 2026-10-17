# Intraday TradingView Strategy + Prop Firm Analysis (Tamil)

**கேள்வி:** "Intraday ku best TradingView strategy/indicator எது? அது online-ல legitimate ஆ இருக்கா? Prop firm trading-க்கு use பண்ணலாமா?"

**விடை (ஒரு வாக்கையில்):**

> **Signal engine → [Squeeze Momentum Indicator [LazyBear]](https://www.tradingview.com/script/nqQ1DT5a-Squeeze-Momentum-Indicator-LazyBear/)** (திறந்த மூலம் / open-source, 2014, 117K likes, repaint இல்லை)
> **+ Filters → Session VWAP bias + 15m EMA trend**
> **+ Risk layer → ATR stop, 0.5% risk per trade, day lock, close-இல் flat**
>
> இதை 5-minute chart-ல், `tradingview/vwap_squeeze_propfirm_v6.pine` என்ற ready-made strategy ஆ எழுதியிருக்கிறேன்.
> 1 ஆண்டு real 1-minute data-வில் backtest + FTMO rule simulation செய்து verify பண்ணியிருக்கிறேன்.

---

## இந்த repo-வில் என்ன இருக்கு

| Path | என்ன |
|---|---|
| `tradingview/vwap_squeeze_propfirm_v6.pine` | **Pine Script v6 strategy** — TradingView-ல் copy-paste பண்ணி உடனே backtest பண்ணலாம் |
| `backtest/strategy.py` | Signal logic (Pine-க்கு line-by-line ஒத்தது) |
| `backtest/backtest.py` | Simulator + **FTMO 2-Step / 1-Step rule simulation** |
| `backtest/sweep.py` | 2,560-config parameter study (IS/OOS split உடன்) |
| `backtest/validate_final.py` | Bootstrap confidence interval + quarterly stability + cost stress |
| `backtest/fetch_data.sh` | Real 1-minute QQQ/SPY data download (99,300 bars) |
| `docs/01-indicator-selection.md` | எந்த indicator, legitimacy proof, comparison table |
| `docs/02-prop-firm-analysis.md` | Prop firm rules + math + simulation verdict |
| `docs/03-backtest-methodology.md` | Data, assumptions, limitations (நேரடியாக சொல்லும் பகுதி) |
| `docs/04-tradingview-setup.md` | TradingView-ல் எப்படி set up பண்ணுவது, prop rules checklist |
| `results/` | எல்லா backtest output-க்கும் raw numbers |

---

## சுருக்கமான முடிவுகள் (1 ஆண்டு real data, 2024-10-31 → 2025-11-07)

**Ship செய்த config (5-minute chart, risk 0.5%/trade):**

| Symbol | Trades | Win% | PF | Expectancy | Total P&L | Max DD | FTMO 2-Step verdict |
|---|---|---|---|---|---|---|---|
| QQQ | 167 | 35.9% | 1.12 | +0.082R | +$6,511 | 11.9% | ✅ இரு phase-ம் pass → FUNDED |
| SPY | 164 | 37.2% | 1.24 | +0.154R | +$12,743 | 5.7% | ✅ இரு phase-ம் pass → FUNDED |

**ஆனால் நேரடியாகச் சொல்ல வேண்டியது:**

1. ⚠️ **Indicator-ன் edge நம்பகமானதாக இல்லை.** Bootstrap 95% CI: QQQ `[−0.15R, +0.32R]`, SPY `[−0.08R, +0.40R]` — zero-ஐ உள்ளடுக்கிறது. அதாவது இது "statistically proven edge" அல்ல; **thin, real-ஆ இருக்க有可能 edge** மட்டும்.
2. ⚠️ **Raw indicator (filters இல்லாமல) break-even-க்கு close.** Signal-ஐ வேறு instrument-ல், வேறு timeframe-ல் run பண்ணினால் edge இல்லாமல் போகிறது (5m-ல் grid-ல் positive OOS cells: QQQ 54%, SPY 15%).
3. ✅ **Prop firm-ஐ pass பண்ணியது risk management-ன் காரணம், signal-ன் காரணமல்ல.** Per-trade risk 1% ஆக ஒரே அளவுக்கு ஒரே signal-ல் → **MAX_LOSS breach** (fail). 0.5%-ல் → pass.
4. ✅ **Day-இல் flat ஆக வேண்டும்.** Overnight வைத்தால் expectancy `+0.082R` → **`−0.295R`** (edge முற்றிலும் போகிறது).
5. ✅ **1-minute-ல் backtest-ஆ மிகவும் attractive, ஆனால் risky.** `momK=1.5` filter-ல் OOS PF 2.04 வரும் — ஆனால் அது **28 trades/வருடம்** மட்டுமே + filter-உடைய knife-edge. முன்பகுதி "அழகிய" backtest, ஆனால் 1m-ஐ 5m settings-ல் போட்டால் **fail** ஆகிறது.

நிறுவனம்/ட்ரேடிங் ஒழுங்குபடுத்தல் என்பது நீங்கள் கேட்பதற்கான முக்கிய பகுதி — அதனால் `docs/02-prop-firm-analysis.md` ஐ முதலில் படிங்க.

---

## சுருக்கமாக execute பண்ண

```bash
# 1) real data download (ஏற்கனவே இருந்தால் skip)
bash backtest/fetch_data.sh

# 2) backtest + FTMO simulation run
cd backtest
python backtest.py --symbol QQQ --tf 5 --save-trades

# 3) parameter study (நேரம் ஆகும், ~10 min)
python sweep.py --symbol QQQ --tf 5
python joint_analysis.py
python validate_final.py
```

TradingView-ல்: `tradingview/vwap_squeeze_propfirm_v6.pine` ஐ copy → **Pine Editor** → paste → **Add to chart** → **Strategy Tester**-ல் "Overfit" / commission / slippage செலுத்தி check பண்ணுங்க.

---

## முக்கிய எச்சரிக்கை

- இங்குள்ள எல்லா backtest முடிவுகளும் **2024-10-31 → 2025-11-07** என்ற ஒரு வருடத்தின் **QQQ/SPY US-equity RTH** data-வில் மட்டும். அதே period-ல் நடந்த market regime-ஐ mirror பண்ணும்.
- 1 வருடம், 2 instrument → **"guarantee" அல்ல**. Forward test (demo) 20-30 trading days ஆனால் பார்த்து, பிறகு live போகவும்.
- இந்த analysis-இல் எந்த broker/firm-ஐயும் endorse பண்ணவில்லை. Prop firm-ல் உண்மையில் pass பண்ணுவது trader-ன் discipline-ன் மேலே, indicator-ன் மேலே உள்ளது.
- TradingView இல்லாமல் இதே logic Pine Script-ஐ நீங்களே எழுதி பயன்படுத்த முடியும் — அதன் source code இங்கே முழுமையாக உள்ளது.
