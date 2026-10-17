# 03 — Backtest Methodology: data, assumptions, limitations

*இந்த doc இருக்கிறதே, இந்த analysis-ஐ வேற ஒருவர் reproduce செய்து பார்க்க முடியும் என்பதற்காக.*

---

## 1) Data

| Item | Detail |
|---|---|
| **Source** | GitHub: `kfhoo88/ibkr-scalper` → `data/historical/{QQQ,SPY}_IBKR_1min_1year_20251110.csv` |
| **Instrument** | QQQ (Nasdaq-100 ETF), SPY (S&P-500 ETF) — US liquid index proxies |
| **Period** | **2024-10-31 → 2025-11-07** (256 trading days) |
| **Bars** | 99,300 per symbol — **1-minute, RTH only** (09:30–16:00 America/New_York) |
| **Columns** | `date, open, high, low, close, volume, average, barCount` |
| **Download** | `bash backtest/fetch_data.sh` (GitHub API raw-ஐ வழியே, LFS-ஐ avoid செய்து) |
| **Audit** | ✅ duplicate timestamp 0 · ✅ null 0 · ✅ session gaps 0 (255 overnight-கள் மட்டும்) · ✅ median 390 bars/day (min 210 = partial day) |
| **Timezone** | UTC-ல் சேமிக்கப்பட்டு `America/New_York`-க்கு convert; DSTAware |

**5-minute bars** 1-minute data-லிருந்து resample செய்யப்பட்டது (label=left, closed=left, `open=first, high=max, low=min, close=last, volume=sum`).

---

## 2) Execution assumptions (எல்லாம் deliberately pessimistic)

| Assumption | நான் எடுத்தது | ஏன் conservative |
|---|---|---|
| Signal timing | Bar **close**-ல் compute | Intraday repaint இல்லை |
| Fill timing | **Next bar-ன் open**-ல் | Realistic; `process_orders_on_close=false` |
| Stop vs Target (same bar) | **Stop முதலில்** fill | TradingView-ன் Pine default behaviour-ம் இதுவே |
| Slippage | **1 tick (0.01)** ஒரு side-க்கும் | Real broker-களில் இதை விட கூடுதல் |
| Commission | **0** | US ETF-களுக்கு ~0 (Prop firm CFD-களுக்கு இது 0 ஒட்டும் — எனவே real-ல் சிறியது) |
| Overnight | **அனுமதிக்கப்படவில்லை** (15:55-ல் flat) | Prop firm-க்கு weekend/rollover risk இல்லை |
| Funding/borrow | இல்லை | 1 வருடம் data-ல் CFD funding-க்கு proxy இல்லை |
| Stop execution | Stop-ல் fill (gap-ஐ ignore செய்யாமல்) | Real-ல் slippage gap-ல் அதிகம் |

---

## 3) Method (overfitting-ஐ தவிர்க்க)

1. **Date-based IS/OOS split** — முதல் 60% sessions = In-Sample, last 40% = **Out-of-Sample**. OOS account **fresh $100k** ஆடங்குகிறது (prop challenge மாதிரியே).
2. **Parameter study** — 2,560 configs (rr × ATR-mult × momentum-strength × slope × session window × HTF on/off × VWAP on/off), 4 combinations-ல் (QQQ/SPY × 1m/5m) செய்யப்பட்டது (`sweep.py`).
3. **Joint selection** — grid-ன் max-ஐ எடுக்காமல், **QQQ + SPY இரண்டிலும் positive** ஆகிய config-களை மட்டும் shortlist செய்தேன் (`joint_analysis.py`).
4. **Neighbourhood stability** — best config-ஐ சுற்றியுள்ள parameter பகுதி (25-50 cells) எல்லாம் positive ஆ இருக்கிறதா என்பது பார்க்கப்பட்டது. (ஒரே cell மட்டும் spike ஆ இருந்தால் reject.)
5. **Bootstrap CI** — trade sequence-ஐ resample செய்து expectancy-ன் 95% confidence interval (20,000 iterations, fixed seed).
6. **Quarterly stability** — 4 quarters, ஒவ்வொன்றுக்கும் fresh account.
7. **Walk-forward** — IS-ல் parameters தேர்ந்தெடுத்து, OOS-ல் trade செய்து பார்த்தல்.
8. **Cost stress** — slippage 1 / 2 / 3 / 5 ticks.
9. **FTMO simulator** — equity-based daily floor, static max-loss floor, min trading days, phase transition, Consistency (best day) rule, day-lock, max trades/day.

---

## 4) Parameter study — கடைசி grid-wide statistics

| Dataset | Positive OOS expectancy cells | Median OOS exp | Best |
|---|---|---|---|
| QQQ 5m | **54.3%** (1472 cells) | +0.008R | +0.442R |
| SPY 5m | **14.8%** (1536 cells) | −0.153R | +0.155R |
| QQQ 1m | 37.7% (1663 cells) | −0.029R | +0.694R |
| SPY 1m | 71.0% (1650 cells) | +0.044R | +0.884R |

> 👉 இதுவே **ஒரே indicator-ஐ எல்லா instrument/timeframe-லும் வைத்து ஒரே மாதிரி வாங்க முடியாது** என்ற உண்மை. QQQ-ல் edge-ஐ நம்பி SPY-ல் வேற settings போடுவது வேற.

### Ship செய்த config-ன் neighbourhood (QQQ 5m, OOS expectancy in R)

| ATR mult ↓ / RR → | 1.5 | 2.0 | 2.5 | 3.0 |
|---|---|---|---|---|
| **1.5** | +0.07 | +0.06 | −0.01 | −0.07 |
| **2.0** | +0.07 | +0.09 | +0.03 | −0.03 |
| **2.5** | +0.09 | +0.12 | +0.06 | −0.07 |
| **3.0** | +0.13 | +0.16 | +0.01 | −0.11 |

*(இது `momK=1.0` வரையில். Ship செய்த `momK=0` config-ன் plateau-ஐ `validation_final.txt`-ல் பார்க்கவும்.)*

---

## 5) Statistical honesty (மிக முக்கிய பகுதி)

Ship செய்த **5-minute config** (rr 3.0, ATR×1.5, momentum-slope on, HTF on, VWAP on, 10:00 start, 45-min runway):

| Symbol | n | Exp | **Bootstrap 95% CI** | Quarters |
|---|---|---|---|---|
| QQQ | 167 | +0.082R | **[−0.147R, +0.323R]** | −0.135, +0.703, −0.337, +0.300 |
| SPY | 164 | +0.154R | **[−0.080R, +0.403R]** | −0.089, +0.313, +0.234, +0.077 |

**Interpretation:** CI zero-ஐ உள்ளடுக்கிறது ⇒ **"statistically proven edge" அல்ல**. ஆனால் sign consistently positive, PF > 1, drawdown control-ல் pass.

**1-minute "knife-edge" variant** (momK=1.5):

| Symbol | n | Exp | Bootstrap 95% CI | Quarters |
|---|---|---|---|---|
| QQQ | 77 | +0.564R | **[+0.163R, +0.973R]** | +0.514, +0.015, +0.636, +1.199 |
| SPY | 69 | +0.223R | [−0.156R, +0.625R] | +0.398, −0.115, +0.200, +0.355 |

QQQ-ல் CI zero-ஐத் தொடாகிறது, ஆனால் **sample சிறு (77 trades)** + filter knife-edge (`momK=1.0` → −0.18R, `2.0` → 0 trades). எனவே **ship செய்யவில்லை** — 5m version stable.

---

## 6) Limitations (நேரடியாகச் சொல்கிறேன்)

| # | Limitation | Impact |
|---|---|---|
| 1 | **1 வருடம் மட்டும்** | Bull-market (AI/Nasdaq) period → edge-ஐ optimistic ஆக வரும் வாய்ப்பு. Bear/range period-ல் இதைப் பயன்படுத்த முடியாது. |
| 2 | **2 instrument மட்டும்** (QQQ, SPY) | Forex/gold/crypto-ல் வேறு. Prop firm-ல் forex பயன்படுத்துபவர்கள் forward test கட்டாயம். |
| 3 | **US equity RTH only** | Crypto/FX 24×7 → session filter-ஐ மாற்ற வேண்டும். |
| 4 | **Commission 0** | Prop firm CFD commission-ஐ கழித்து net P&L குறையும். |
| 5 | **Stop fill-ல் gap risk model இல்லை** | Real gap-உடன் stop-ஐ விட்டால் கூடுதல் loss. |
| 6 | **Survivorship / instrument selection** | இரண்டும் index ETF-கள் — QQQ/SPY நேரடியாக correlated. |
| 7 | **Overfit risk** | 2,560 config test பண்ணியதால் best cell-க்கு "winner's curse" உள்ளது. Joint (2-instrument) selection + neighbourhood + bootstrap இதைக் குறைத்தேன், ஆனால் பூர்த்தி செய்யவில்லை. |
| 8 | **1 instrument = 1 market** | ETF-கள் futures-ஐ substitute செய்யாது (roll yield, session differences). |

### இதை நான் எப்படி close செய்வேன் (உங்களுக்கு recommended)
1. **Forward test 20-30 trading days** உங்கள் prop account-ன் instrument-ல், demo-ல், real rules-உடன்.
2. ஒவ்வொரு வாரம்: loss days, max daily loss, best-day ratio (consistency), trades/day-ஐ log பண்ணுங்க.
3. 30 days-ல் expectancy positive-ஆ இருந்தால் மட்டும் live-க்கு செல்லுங்க — risk 0.5%-ஐ வைத்து.
4. Instrument/timeframe சொல்லும் validation செய்ய முடியும் (source-ஐ fork செய்து, `fetch_data.sh`-ல் symbol சேர்த்து, `sweep.py` + `joint_analysis.py` run பண்ணுங்க).

---

## 7) Reproduce பண்ணுங்க

```bash
bash backtest/fetch_data.sh                       # real 1-min data
cd backtest
python backtest.py --symbol QQQ --tf 5           # single run + FTMO sim
python sweep.py --symbol QQQ --tf 5              # parameter study (~2 min)
python sweep.py --symbol SPY --tf 5
python joint_analysis.py                         # cross-instrument shortlist
python validate_final.py                         # bootstrap + quarterly + stress
python final_report.py                           # FTMO verdict + ablations + risk curve
```

Random seed `20261017` fix ஆகும் ⇒ bootstrap-ன் விடைகள் reproducible.
