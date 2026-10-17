# 04 — TradingView-ல் setup பண்ணும் விதி + Prop firm daily routine

---

## A. TradingView-ல் install பண்ணுங்க

1. [tradingview.com](https://www.tradingview.com) → login → chart ஒன்று open.
2. கீழே **Pine Editor** tab-ல் click → existing code-ஐ select செய்து **Ctrl+A → Delete** (அல்லது "Open" → New blank).
3. `tradingview/vwap_squeeze_propfirm_v6.pine` file-இன் முழு code-ஐ copy செய்து paste.
4. **Save** (Ctrl+S) → **Add to chart**.
5. Chart-ல் indicator add ஆனதும் **Strategy Tester** tab-ல் சொல்லுங்க: *"VWAP + Squeeze Momentum [Prop-Firm Intraday]"*.

### ⚠️ Strategy Tester-ல் இந்த settings-ஐ மாத்த்து இடவும்
| Setting | Value | ஏன் |
|---|---|---|
| **Initial capital** | 100000 | Prop firm account size |
| **Commission** | 0 (CFD) / 0.01% (ETF) | Realistic |
| **Slippage** | **1** (tick) | என் backtest-உடன் match |
| **Fill type** | `Strategy equity` / default | — |
| **Recalculate on every tick** | **OFF** | Intrabar noise சேர்த்து backtest-ஐ துல்லியமாக்காது |
| **Deep backtesting** | ON (வேண்டுமென்றால்) | 1m-ல் chart-ல் limit இருக்கும் |

> 🔎 உங்கள் TradingView-இன் backtest-ஐ என் Python result-உடன் **compare பண்ணுங்க** — close values சிறிய வேறுபாடு இருக்கலாம் (என் simulator-ல் 1-tick slippage, stop-first assumption, RTH-only data). பெரிய வேறுபாடு இருந்தால் session window-ஐ check பண்ணுங்க.

---

## B. Settings — ஒவ்வொரு instrument-க்கும்

### US index ETF (QQQ / SPY) — 5-minute chart ✅ (இதுவே validate பண்ணியது)

| Setting | Value |
|---|---|
| Timeframe | **5 分钟 / 5m** |
| Bollinger length / mult | 20 / 2.0 |
| Keltner length / mult | 20 / 1.5 |
| Session | `0930-1600` (exchange TZ = America/New_York) |
| Session (non-US exchange-ல்) | `0930-1600:America/New_York` |
| HTF filter | ON, 15m, EMA 50 |
| Momentum strength | **0 (off)** |
| Require rising momentum | **ON** |
| ATR length / stop multiple | 14 / **1.5** |
| Take profit (R) | **3.0** |
| Risk per trade | **0.5%** |
| Max trades/day | **3** |
| Daily loss lock | **2.0%** |
| Account size / max loss lock | 100000 / 10% |
| Entry start / end | **600 (10:00)** / 945 (15:45) |
| Flatten all | **955 (15:55)** |
| Min minutes left to open | **45** |

### Forex / Gold (XAUUSD, EURUSD போன்றவை) — 5-minute chart
Signal-ன் அதே logic, ஆனால் **session-ஐ மாற்ற வேண்டும்**:

| Setting | Value (London/NY overlap) | Value (Asian) |
|---|---|---|
| Session | `0700-1600` (London) | `0000-0900` |
| Entry start / end | **420 (07:00)** / 960 (16:00) | **0** / 540 (09:00) |
| Flatten all | **960 (16:00)** | **540 (09:00)** |
| Min runway | 45 | 45 |

> ⚠️ Forex-ல் commission/spread பெரியது. என் backtest commission 0-ஐ assume பண்ணது → real-ல் expectancy குறையும். **Risk-ஐ 0.5%**-ல் வைத்து, 30 days forward test பண்ணுங்க.

### 1-minute chart (இருக்கலாம், ஆனால் கவனமாக)
| Setting | Value | குறிப்பு |
|---|---|---|
| Momentum strength | **1.5** (ON!) | Ship செய்த 5m config 1m-ல் **FAIL** ஆகிறது |
| ATR multiple | 2.5 | |
| R multiple | 3.0 | |
| HTF filter | **OFF** | 1m-ல் HTF filter lag செய்கிறது |
| VWAP filter | OFF (default-இல் ON ஆகும்) | |
| Trades/வருடம் | ~28-77 | **Sample சிறு** — முன்னேயே கூறியபடி knife-edge |

---

## C. Live trading-எ எப்படி இந்த setup-ஐ பயன்படுத்துங்க

### 1) Alert மூலம் (semi-auto — prop firm-க்கு இதுவே recommend)
- TradingView-ல் indicator-க்கு **Alert** create செய்யுங்க: condition `VWAP-Squeeze LONG` / `VWAP-Squeeze SHORT`.
- **"Once Per Bar Close"** ஆகவும் வையுங்க (repaint இல்லை என்ற assurance).
- **Webhook → your broker/EA** (இது Pine-ஐ *indicator* மாதிரி; auto-trade-க்கு broker-ன் own rules-ஐ check பண்ணுங்க).
- Alert-ஐ நீங்களே execute பண்ணுங்க: order-ஐ place செய்யும்போது **entry, stop, target-ஐ Pine-ல் காட்டியபடி** வையுங்க (stop = signal bar close ∓ 1.5×ATR).

### 2) Pine-ஐ indicator (உங்கள் order logic-ஐ TradingView-ல் நீங்களே எழுதி வைத்திருந்தால்)
- `strategy.*` calls-ஐ `alert()` + `strategy.entry` காட்டுங்க; risk sizing உங்கள் platform-ல்.

### 3) Order-ஐ place செய்யும்போது
| அங்கம் | வழி |
|---|---|
| **Entry** | Alert-ல் காட்டிய next-bar open (அல்லது market + small slippage) |
| **Stop loss** | `signal close ∓ 1.5 × ATR(14)` — Pine-ல் காட்டியபடி |
| **Target** | `signal close ± 3 × stop distance` |
| **Size** | `0.5% × equity ÷ stop distance` — உங்கள் prop account size-க்கு ஏற்ப |
| **Close** | 15:55-ல் எல்லாவற்றையும் close (overnight வேண்டாம்) |

---

## D. Prop firm daily routine (checklist)

### 🌅 Session open (09:30-10:00 ET)
- [ ] Chart-ல் indicator ஒன்று, 5m timeframe, **"Once per bar close"** alerts.
- [ ] Account-ன் day-start balance-ஐ note பண்ணுங்க; **day lock = −2%**; **max loss floor = 90%**.
- [ ] இன்டேயின் news calendar check (high-impact news-ல் size 0.5×).
- [ ] 10:00-க்கு மட்டும் trade entry (10:00-ஐ target செய்யாது).

### 🕙 Trading window (10:00-15:45 ET)
- [ ] Long என்றால்: price **VWAP-க்கு மேல்** + 15m EMA rising ஆ இருக்க வேண்டும்.
- [ ] Stop = 1.5 × ATR(14, 5m). Size = 0.5% / stop distance.
- [ ] Target = 3R. **RR-ஐ குறைக்காது** (3R-ஐ 1.5R ஆக மாத்தினால் expectancy negative ஆகிறது).
- [ ] Day-க்கு max **3 trades** மட்டும்.
- [ ] Day P&L **−2%** ஆனால் → எல்லாவற்றையும் close, அந்த நாள் trade வேண்டாம்.

### 🌇 Close (15:45-15:55 ET)
- [ ] 15:45-ல் entry stop; **15:55-ல் position இல்லை** என்று confirm.
- [ ] Day-இன் P&L, trades count, best-day ratio log பண்ணுங்க.

### 📅 Weekly
- [ ] Consistency check: `best day ÷ total profit` — FTMO funded rule **≤30%** (1-Step challenge-ல் ≤50%).
- [ ] Total profit, max DD, win days vs loss days track.
- [ ] Risk per trade **0.5%**-ஐ விட கூடுதலாக ஒரு week-உம் trade செய்யவில்லை (அதனால் drawdown வராது).

---

## E. இந்த setup-ன் "கெடுத்தல்" (kill switch) rules

| Trigger | Action |
|---|---|
| Day P&L ≤ −2% | அந்த நாள் trading stop |
| Total DD ≥ 6% (funding-க்கு முன்) | Risk → 0.25% ஆக குறை, அல்லது stop |
| 5 consecutive losses | அந்த நாள் stop, chart-ஐ மூடு |
| 30 days-ல் net negative | Strategy-ஐ மாற்று / forward test-ஐ மீண்டும் |
| Win rate target-ஐ மறந்து நடந்தாலும் | **தொடரவும்** — expectancy-ஐதான் பாருங்க |

---

## F. கேள்விகளுக்கான prepared answers

**"Win rate 36% கொடுத்து prop firm-ல் pass ஆகுமா?"**
ஆம், ஆனால் **RR 3R + PF 1.12-1.24** இருந்தால். 36% win rate-ல் 3R target-ஐ அடையாது. என் simulation-ல் இரண்டும் pass ஆனது.

**"ஒரே indicator-ஐ எல்லா instrument-ல் பயன்படுத்தலாமா?"**
இந்த signal-ஐ பயன்படுத்தலாம், ஆனால் **session window-ஐ instrument-க்கு ஏற்ப மாற்ற வேண்டும்** (FX-ல் London session). Parameters-ஐ (ATR mult, R) instrument-க்கு re-validate பண்ணுங்க (`sweep.py`).

**"Free plan-ல் போதுமா?"**
Pine script strategy **free plan-லே** செயல்படும் (indicator slot limit-ஐ விட strategy-க்கு limit இல்லை). Built-in VWAP/Supertrend/RSI-யும் free. Paid indicator தேவையில்லை.

**"Repaint ஆ இருக்கா?"**
இந்த strategy-க்கு இல்லை — எல்லா signal closed-bar values-ல். "Once per bar close" alert + Bar Replay test செய்து confirm பண்ணுங்க.

**"எப்படி auto-trade பண்ண?"**
Pine-ல் `strategy.*` orders உள்ளன — TradingView → "Paper Trading" / third-party bridge (கவனம்: prop firm-இன் ToS-ல் auto-trading-ஐ allow பண்ணியிருக்கா என்பதை check பண்ணுங்க; என் analysis-ல் human execution assume பண்ணியிருக்கிறது).
