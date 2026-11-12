# Gold Futures Trading App — Blueprint
### CME Data vachu TradingView illama oru Android App
### Prop Firm: FundedNext Futures (Tradovate)

> **Goal:** FundedNext Futures-la Gold Futures (GC / MGC) trade panna, TradingView subscription kekama, nammale oru Android app build panni live chart, indicators, alerts, risk management ellame orey idathula vechukoalam.
>
> **Update (Nov 2026):** Prop firm = **FundedNext Futures** nu confirm aayiduchu. Adhukku etha maari blueprint update panniten — Tradovate API dhaan namma real-time data source.

---

## 1. Reality Check — Mudiyuma? Kandippa Mudiyum, Aana Oru Condition Irukku

| Question | Answer |
|---|---|
| CME data vachu app build panna mudiyuma? | **Yes.** Aana CME real-time data-ku license / subscription thevai. Free-a kedakkura data delayed-a irukkum. |
| TradingView-ku alternative-a? | **Yes.** Yahoo Finance, Stooq, prop firm-oda own feed (Tradovate) vachu chart build panna mudiyum. |
| App-laye trade panna mudiyuma? | **Direct-a mudiyadhu.** CME-la trade panna FCM / broker account venum. FundedNext Futures Tradovate vazhiya dhaan execution nadakkum. App = analysis + alerts + risk manager. Execution = Tradovate platform. |
| FundedNext Futures-la automated trading mudiyuma? | **Aam, allowed.** FundedNext Futures EAs/bots-a Challenge-layum FundedNext Account-layum allow pannudhu (official help center). Aana support illa, and HFT / order-flooding / grid prohibited. **Semi-auto (alerts + one-tap order) dhaan sensible design.** |
| Personal use-ku ok-va? | **Yes.** Unakku mattum use panna, free / delayed data vachu start panna mudiyum. Paid real-time venumna prop firm feed use pannalam. |

**Bottom line:** App namma build pannalam. Data source-a poruthu real-time vs delayed decide aagum. Adhu dhaan indha blueprint-oda base.

---

## 2. Data Sources — Ena Data Use Pannalam?

Gold Futures symbols:
- **GC** = COMEX Gold Futures (100 troy oz) — per 1 point move = **$100**, tick 0.10 = **$10**
- **MGC** = Micro Gold Futures (10 troy oz) — per 1 point move = **$10**, tick 0.10 = **$1**
- Trading hours (CME Globex): **Sun 5:00 PM – Fri 4:00 PM CT** (daily 4:00–5:00 PM CT halt)

| Source | Real-time? | Cost | Use Case | Notes |
|---|---|---|---|---|
| **Yahoo Finance (GC=F)** | ~15 min delayed | Free, no API key | **MVP / Phase 1** | 1m, 5m, 15m, 1h, 1d candles kedakkum. Chart-ku podhum. |
| **Stooq (GC.F)** | Delayed | Free CSV | Backup / daily data | Simple CSV download. |
| **CME Group official** | Real-time | Paid license (~$50–$200+/mo + redistribution rules) | Professional | cmegroup.com market data. Redistribution strict rules irukku. |
| **Tradovate API** | Real-time CME | FundedNext account irundha free (data fee firm absorb pannum) | **Phase 2 — FundedNext-ku idhu dhaan** | REST + WebSocket. Level 1 + Level 2 data. |
| **Rithmic API** | Real-time CME | Prop firm account irundha free/low | Apex/Topstep-ku | FundedNext Futures-la primary illa, Tradovate dhaan. |
| **Polygon / TwelveData / Finnhub** | Real-time (paid plan) | $29–$99/mo | Alternative vendor | Futures support check pannanum. |
| **DXtrade / cTrader API** | Real-time | Prop firm account | Prop firm poruthu | Some prop firms idha use pannanga. |

### Recommendation (FundedNext Futures-ku)
1. **Phase 1 (MVP):** Yahoo Finance `GC=F` — free, instant start, chart + indicators test panna.
2. **Phase 2 (Live):** **Tradovate API** — FundedNext Futures-oda broker Tradovate dhaan. Adhulaye real-time CME data varum, extra cost illa.
3. **Phase 3:** CME direct / Polygon venumna upgrade pannalam.

> ⚠️ **Legal note:** CME real-time data-a scrape panni redistribute panna mudiyadhu. Personal use-ku prop firm feed / licensed vendor use pannalam. Delayed free data (Yahoo/Stooq) personal learning-ku ok.

---

## 2.5 FundedNext Futures — Unakku Enna Kidaikkum?

| Item | Detail |
|---|---|
| **Firm** | FundedNext Futures (FundedNext-oda futures division) |
| **Broker / Clearing** | **Tradovate** (NinjaTrader-um support) |
| **Platforms** | Tradovate (web/desktop/mobile), NinjaTrader 8, TradingView (via Tradovate) |
| **Instruments** | GC, MGC, SI, HG, ES, NQ, CL, 6E etc. — CME/COMEX/CBOT/NYMEX futures mattum. **Spot XAUUSD illa.** |
| **Real-time data** | Tradovate vazhiya Level 1 + Level 2 CME data. Data subscription fee FundedNext challenge price-laye absorb pannum — nee separate-a pay panna thevai illa. |
| **First login** | Tradovate web (`trader.tradovate.com`)-la first login panni CME/CBOT/NYMEX/COMEX data agreements sign pannanum. Apram dhaan live data varum. **Idhu romba mukkiyam — app-la data varalaina 90% idhu dhaan problem.** |
| **Trading hours (⚠️ mukkiyam)** | **Overnight / weekend holding illa.** Daily session: **5:00 PM CT** open → **3:10 PM CT** close. 3:10 PM CT-la open positions **automatic-a close aagum**. Sunday 5:00 PM CT-la reopen. |
| **Drawdown** | **EOD trailing Maximum Loss Limit (MLL)** — ellaa models-layum. Day close (5:00 PM CT) balance-la dhaan trail aagum, **real-time illa**. Initial balance-a reach panna **lock** aagum. |
| **Consistency** | 40% rule — chinna plans-la. 2026-la Legacy/Flex funded-la remove aayiduchu. |
| **Automation / EA** | ✅ **ALLOWED** — "FundedNext Futures allows the use of automated trading systems, including Expert Advisors (EAs) and trading bots" during Challenge **and** FundedNext Account. Aana support illa, and exploit strategies (HFT, latency abuse, order flooding) prohibited. |
| **Copy trading** | Only **un** own accounts-a copy panna allowed. Vera oruthar account / signal service prohibited. |
| **Country restriction** | Restricted list-la **India illa** ✅ (Bangladesh, Sri Lanka, Malaysia, Vietnam irukku — India illa) |

### FundedNext Futures Plans — App-ku Theriya Vendiya Numbers

| Plan | Sizes | Profit Target | Max Loss (EOD trailing MLL) | Daily Loss Limit | Consistency | Split |
|---|---|---|---|---|---|---|
| **Rapid Pro** | 25K / 50K / 100K | $1,500 / $3,000 / $5,000 | $1,000 / $2,000 / $2,500 | Illa (add-on optional) | 40% (funded) | 90% |
| **Rapid Daily** | 25K / 50K / 100K | $1,500 / $3,000 / $5,000 | $1,000 / $2,000 / $2,500 | $500 / $1,000 / $1,250 | Illa | 90% |
| **Flex** | 50K / 100K / 150K | $2,500 / $5,000 / $8,000 | $1,500 / $2,500 / $4,000 | Illa | 40% (challenge only) | 95% |
| **Legacy** ⚠️ | 25K / 50K / 100K | $1,250 / $3,000 / $6,000 | $1,000 / $2,000 / $3,000 | Illa | 40% (challenge only) | 80% |

> ⚠️ **Legacy October 11, 2026-la purchase-ku close aayiduchu** — existing accounts-ku reset-um illa. So **Rapid Pro / Rapid Daily / Flex** dhaan practical options. Blueprint-la Legacy-a reference-ku mattum vechirukken.

**MLL lock levels:** Legacy → initial balance. Flex / Rapid Pro / Rapid Daily / Direct → **initial balance + $100**.

**Contract limits (Challenge / Funded):**

| Size | Rapid Pro & Daily | Flex | Legacy |
|---|---|---|---|
| $25K | 2 mini / 20 micro | — | 2 / 20 |
| $50K | 4 mini / 40 micro | 3 / 30 | 3 / 30 |
| $100K | 6 mini / 60 micro | 5 / 50 | 5 / 50 |
| $150K | — | 8 / 80 | — |

**Mixing ratio 1:10** (1 e-mini = 10 micro). Limit exceed panna → excess contracts violate aagum, adhoda profit deduct aagum, loss count aagum.

> **App-ku idhu dhaan mukkiyam:** Indha numbers-a app-la **hardcode pannadha** — Settings-la user select pannum model + size vechu drawdown meter / contract guard calculate aagum. Rules maarum (2026-la neraya maathirukaanga), so **config-driven**-a vechuko, JSON config file-la vechu update panna easy-a irukkanum.

### 🎯 Starting-ku Endha Model? — Recommendation

**Rapid Daily $50K** — idhu dhaan best starting point.

| Reason | Detail |
|---|---|
| **Consistency rule illa** | Rapid Pro-la funded stage-la 40% consistency irukku. Adhu oru extra constraint — initial phase-la avoid pannalam. |
| **Daily loss limit safety net** | $1,000 daily soft stop. **Adhu account-a kolladhu** — trading pause aagum, next day reset. Beginner-ku idhu dhaan best guardrail. |
| **MLL $2,000** | 4% of account. 1% risk (=$500) panna 4 losses afford pannalam. |
| **Contract limit 4 mini / 40 micro** | GC-ku 4 contracts — enough room, but forced discipline. |
| **Daily payout** | Fast feedback loop. Learn pannum podhu reward cycle short-a irukku. |
| **90% split** | Same as Rapid Pro, better than Legacy. |

**Price:** ~$149.99 list (frequent 50% discount → ~$79.99)

**Size choice — $50K vs $25K:**

| | 25K | **50K** ✅ |
|---|---|---|
| Daily loss limit | $500 | $1,000 |
| MLL | $1,000 | $2,000 |
| Contract limit | 2 mini / 20 micro | **4 mini / 40 micro** |
| GC 1% risk ($500) sizing | 1 contract (challenging) | **1 contract, comfortable** |
| Micro flexibility | 20 MGC | **40 MGC** |

**25K-la problem:** $500 risk panna, 5-point stop-la GC 1 contract = exact $500. So sizing room illa — **MGC-la mattum trade panna vendiyirukkum**. 50K-la breathing room irukku.

> **Flex $50K enna?** 95% split nalladhu dhaan, aana challenge-la 40% consistency irukku and MLL $1,500 (Rapid-oda $2,000-a vida tight). Learn panna **Rapid Daily 50K** dhaan simplest.

**Intha decision-a app-la default config-a vechuko**, aana user Settings-la maathikalam (primary/secondary account-ku).

### Model Comparison — Quick Decision Tree

```
Nee beginner-a, first prop challenge-a?
  └─ YES → Rapid Daily $50K   ✅ (no consistency, daily loss guard)

Nee experienced, consistency maintain panna confident-a?
  └─ YES → Rapid Pro $50K     (better cap at 100K, but funded-la 40% consistency)

Nee long-term funded account venum, 95% split venum-a?
  └─ YES → Flex $50K          (consistency challenge-la, $1,500 MLL — tighter)

Nee already Legacy account vachirukka?
  └─ YES → Adhu close aayiduchu, reset illa → migrate pannu
```


### Tradovate API — Namma App Eppadi Connect Aagum?

```
Auth: POST https://live.tradovateapi.com/v1/auth/accessTokenRequest
      body: { name: "<Tradovate username>", password: "<password>", appId, appVersion, cid, sec }
      → accessToken (expiry ~80 min), mdAccessToken (market data-ku separate)

Contract resolve (front-month GC / MGC):
      GET  /contract/find?name=GCZ6      → exact contract
      GET  /contract/suggest?t=GC&l=1    → front month
      GET  /contract/item?id=<id>

Historical candles (Phase 2 initial load):
      GET  /md/getChart  { symbol, chartDescription, timeRange }
      → bars[] (open/high/low/close/volume) — Room-la cache pannu

Live streaming (WebSocket):
      wss://md.tradovateapi.com/v1/websocket     (demo: wss://md-demo.tradovateapi.com/v1/websocket)
      ops: md/subscribeQuote, md/subscribeChart, md/subscribeDOM, md/unsubscribe*

User/account data (optional, READ-ONLY):
      wss://live.tradovateapi.com/v1/websocket   (demo: wss://demo.tradovateapi.com/v1/websocket)
      ops: user/syncRequest → positions, orders, cash balance, account rules
```

**Symbol note:** GC front month Nov 2026-la `GCZ6` (Dec 2026). App hardcode pannadha — `/contract/suggest` vachu dynamic-a resolve pannu, rollover automatic-a handle aagum.

**Nalla vishayam:** Demo mode-la fake money vachu real market data test panna mudiyum — app build panna risk illa.

**✅ Nalla news:** FundedNext Futures **EAs and bots allow pannudhu** — Challenge-layum FundedNext Account-layum. Adhanaala app order poda munnadi "prohibited"-nu nenache, adhu thappu. Aana:

- FundedNext **support tharaadhu** — error, delay, malfunction ellame un responsibility.
- **HFT, latency abuse, order flooding, grid, spoofing, micro-scalping** prohibited. App-la order podum feature venumna, indha limits-a strict-a enforce pannanum.
- **Semi-auto dhaan best:** alerts + one-tap order poda, auto-fire illa. Risk-a nee control pannuva.

**Account data read panna mudiyuma?** — `user/syncRequest` vachu positions, orders, cash balance read-only-a pull pannalam → journal auto-fill, drawdown meter live-a work aagum. Idhu Tradovate API standard path, and FundedNext automation allow panradhala safe.

> **⚠️ App design-ku oru important implication:** FundedNext-la **overnight holding illa**, 3:10 PM CT-ku automatic close. App-la "session timer" + "force close countdown" kaattanum, illaati user position open-a vechutu confuse aavaan.


---

## 3. App Features

### MVP (V1) — First Release
- [ ] Live chart — GC & MGC, candlestick + line
- [ ] Timeframes: 1m, 5m, 15m, 1h, 4h, 1D
- [ ] Indicators: EMA, SMA, RSI, MACD, Bollinger Bands, VWAP, ATR, Supertrend
- [ ] **Custom indicator support** — un TradingView Pine indicators port pannalam (see §4.5)
- [ ] Volume + price axis, zoom / pan
- [ ] Watchlist (GC, MGC, SI, CL, ES, NQ — future expand)
- [ ] Price alerts (crossing, % move)
- [ ] Position size calculator (tick value, stop loss, risk $)
- [ ] Dark theme, mobile optimized

### V2
- [ ] Real-time WebSocket ticks (Tradovate Market Data API)
- [ ] Push notifications (FCM) for alerts
- [ ] Trade journal (entry, exit, P&L, screenshot, notes)
- [ ] Daily P&L tracker + prop firm drawdown meter
- [ ] Backtest simple strategies (EMA cross, RSI)
- [ ] Multi-chart layout

### V3
- [ ] **Semi-auto order entry** — one-tap order Tradovate API vazhiya, manual confirm dialog-oda. Auto-fire **illa**. FundedNext bots-a allow pannudhu, aana HFT/monthly limits enforce pannanum.
- [ ] Session guard — 3:10 PM CT auto-close countdown, "flat now" reminder
- [ ] Prohibited-pattern warnings (micro-scalp ≤10s, ultra-tight brackets)
- [ ] Economic calendar (CPI, FOMC, NFP — gold move aagum)
- [ ] AI / ML price prediction (experimental)
- [ ] Play Store release

---

## 4. Architecture

```
┌─────────────────────────────────────────────┐
│           Android App (Kotlin)              │
│  Jetpack Compose UI + MVVM + Clean Arch     │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │  Chart   │  │ Alerts   │  │ Risk Mgr  │  │
│  │  (Vico)  │  │ Engine   │  │ + MLL     │  │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘  │
│       └─────────────┼──────────────┘         │
│              ViewModel / UseCase             │
│                     │                        │
│  ┌──────────────────┴───────────────────┐    │
│  │  Repository (Data Layer)             │    │
│  │  Room DB (cache) + DataStore (pref)  │    │
│  │  + FundedNext rule config (JSON)     │    │
│  └──────────────────┬───────────────────┘    │
└─────────────────────┼────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │   Data Sources            │
        │  Phase1: Yahoo REST API   │
        │  Phase2: Tradovate WS     │
        └───────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │  (Optional) Backend       │
        │  FastAPI / Node.js        │
        │  - API key hide pannum    │
        │  - Alert engine (24/7)    │
        │  - Data caching           │
        └───────────────────────────┘
```

### Tech Stack
| Layer | Choice | Why |
|---|---|---|
| Language | **Kotlin** | Android official, modern |
| UI | **Jetpack Compose** | Latest, fast development |
| Architecture | **MVVM + Clean Architecture** | Maintainable, testable |
| Chart | **Vico** (Compose chart lib) + custom candlestick | Free, open source, customizable |
| Networking | **Retrofit + OkHttp** (REST), **OkHttp WebSocket / Ktor** (live ticks) | Standard |
| Local DB | **Room** | Candle cache, journal |
| Settings | **DataStore** | Alerts, preferences |
| Background | **WorkManager** | Alerts check pannum |
| Notifications | **Firebase Cloud Messaging (FCM)** | Push alerts |
| Backend (optional) | **Python FastAPI** or **Node.js** | API key hide, 24/7 alert engine |
| Version Control | **Git + GitHub** | Indha repo |
| Build | **Android Studio + Gradle** | Standard |

### Why not Flutter / React Native?
Android mattum dhaan venumna Kotlin best. Cross-platform venumna Flutter consider pannalam — aana first Android native start pannalam, apram decide pannalam.

---

## 4.5 TradingView Indicators-a App-la Add Pannuvadhu (Mukkiyam)

Unakku already TradingView-la indicators ready-a irukku. Adha **rendu vidhama** app-la kondu varalam:

| Approach | Enna Pannanum | Effort | Best For |
|---|---|---|---|
| **A. Native port** | Pine Script logic-a Kotlin-la rewrite pannu | Medium | Charts-la smooth-a render aagum, offline work aagum |
| **B. Pine Script parse** | User oda Pine code-a app-la paste panni interpret pannu | Very High | General purpose — **recommend illa** |
| **C. WebView** | TradingView widget / lightweight-charts WebView-la load pannu | Low | Fast MVP, aana offline illa |

**Recommendation: A + limited C.**
- **Built-in indicators** (EMA, RSI, MACD, BB, VWAP, ATR, Supertrend) → **native Kotlin** port
- **Un custom Pine indicators** → **Pine-to-Kotlin converter** (each one once)
- **Quick validation** → WebView-la TradingView widget vachu compare pannu

### Pine Script ↔ Kotlin — Exact Formula Match (Important!)

| Pine function | Kotlin-la enna pannanum | Gotcha |
|---|---|---|
| `ta.sma(src, n)` | Simple rolling average | Easy |
| `ta.ema(src, n)` | `alpha = 2/(n+1)` | Seed = SMA of first n bars |
| `ta.rma(src, n)` / SMMA | `alpha = 1/n`, seed = SMA | **⚠️ Idhu dhaan RSI/ATR-oda base. SMA-la pannina RSI thappu varum.** |
| `ta.rsi(src, n)` | RMA of gains / RMA of losses | **Wilder smoothing, NOT simple average** |
| `ta.atr(n)` | `ta.rma(ta.tr, n)` | `tr = max(high-low, |high-prevClose|, |low-prevClose|)` |
| `ta.macd` | EMA(12) − EMA(26), signal = EMA(9) of that | Three EMA, each seeded |
| `ta.bb(src, n, mult)` | SMA ± mult × stdev | Pine stdev = **population** (÷N), not sample (÷N−1) |
| `ta.vwap` | Session-anchored cumulative | **Must reset at session start (5:00 PM CT)** — rolling aana thappu |
| `ta.crossover(a, b)` | `a[1] <= b[1] && a > b` | Previous bar-a check pannanum |

> ⚠️ **Common bug:** `ta.rsi`-a simple moving average vachu port panna, values 1–2 points differ aagum → TradingView-oda match aagaadhu. RMA (Wilder) use pannanum. Pine default `ta.rsi` = `ta.rma`-based, RMA seed = SMA of first `n` values, then `rma = rma[1] + (src − rma[1]) / n`.

### Indicator Engine Design

```kotlin
interface Indicator {
    val id: String                 // "rsi_14", "ema_50"
    val overlay: Boolean           // chart mela draw aaguma, illa separate pane-a
    fun compute(bars: List<Bar>): IndicatorSeries
}

// Every indicator = pure function of bars → series.
// No state leakage → easy to unit test and easy to verify vs TradingView.
data class IndicatorSeries(
    val id: String,
    val points: List<Double?>,     // null = warm-up period (Pine `na`)
    val pane: Pane,                // OVERLAY | SEPARATE
)
```

**Incremental recompute:** Live tick vandha, full history-a recompute pannadha. Last bar-a update panni, indicator-oda **last value mattum** recalculate pannu (each indicator-ku `updateLast(bar)` implement pannu). Illaati 1-minute chart-la battery drain aagum.

### Un Custom Indicators-a Add Pannura Workflow

```
1. TradingView-la un indicator open pannu → "Pine Editor"
2. Code-a copy pannu
3. Inga paste pannu  →  naan Kotlin-a convert panren
4. Conversion checklist:
   □ ta.* function ellame exact match-a? (RMA vs SMA check!)
   □ input.* values → Kotlin data class params
   □ plot/plotshape/hline → Compose Canvas draw calls
   □ alertcondition → our alert engine trigger
   □ request.security (higher TF) → MTF data fetch — idhu tricky, phase 3
5. TradingView chart-oda side-by-side verify (same symbol, same TF, same bars)
```

**⚠️ Alert-ku common trap:** Pine `alertcondition`-a app-la port panna, **bar close vs tick** difference-a handle pannanum. TradingView default-a **bar close**-la alert podum (unless "Once per bar" select pannina). App-lum same behaviour vechuko — illaati repainting signals varum.

### ✅ Un Indicator Already Ported — LSMS v3

Un `LSMS_v3.txt` (798 lines, Pine v5) port pannitten. Idhu oru **complete trade engine**,
indicator mattum illa:

```
Liquidity map → sweep → structure break (MSS) → FVG entry → liquidity target
```

Adhoda 4 bonus features — prop account-ku idhu dhaan real value:

| Feature | Enna Pannum |
|---|---|
| **Kill-zone filter** | London (02:00–05:00) / NY (07:00–10:00) ET-la mattum signal |
| **HTF bias** | 4H EMA50 mela irundha longs mattum, keezha shorts mattum |
| **Risk guard** | N losses aana apram / daily limit near aana signal block |
| **Simulated outcome tracker** | Ovvoru signal-um auto-track, bucket-wise expectancy |

**FX-la irundhu gold-ku 6 values maathiten** (details: `LSMS_PORT_NOTES.md`):

| Pine | Problem | Fixed |
|---|---|---|
| `contract = 100000` | FX lot. Gold 100 oz. **1000× understatement** | GC $100/pt, MGC $10/pt |
| `pipSz = 0.0001` | Gold-la pip illa, tick 0.10 | Tick/point arithmetic |
| `spreadPips = 1.0` | Gold-la ~$0.01 ≈ free | 2 ticks = $20 round trip |
| `min/maxRiskPips 4/25` | Gold 1m ATR ~2–4 points | 1.5–15 points |
| `time + 25200000` | Fixed 7h offset — **winter-la thappu** | Real timezone (`NewYorkClock`) |
| `acctSize 10000, 5%/10%` | FundedNext 50K = **2%/4%** | $50K, 2%, 4% |

**⚠️ Measured finding — 0.5% risk-la GC unusable:**

| Instrument | 0.5% ($250) | 1.0% ($500) |
|---|---|---|
| GC (5pt stop) | **0 contracts** | 1 contract |
| MGC (5pt stop) | 5 (cap 40) | 10 (cap 40) |

$250-la GC 1 contract-oda stop = $500 risk. Adhanaala **MGC dhaan workhorse**.
`Sizing.kt` GC 0 aana MGC-equivalent kaattum — bare "0" illa.

**Proof:**
- `validation/parity_check.py` — 14/14 Pine maths tests (RMA/RSI/ATR exact)
- `validation/engine_spec.py` — 21/21 behavioural rules
- `validation/engine_smoke.py` — 2,000 bars, 11/11 structural invariants

### Phase Plan for Indicators

| Phase | Enna |
|---|---|
| **Phase 1** | 8 built-in indicators native Kotlin (EMA, SMA, RSI, MACD, BB, VWAP, ATR, Supertrend) + **golden test vs TradingView CSV export** |
| **Phase 1.5** | ✅ **LSMS v3 ported** — GC/MGC specs, engine, sizing, session clock |
| **Phase 3** | Multi-timeframe (`request.security` equivalent), indicator templates save pannu |

---

## 5. Screens (App Flow)

```
Splash → Home (Watchlist)
           ├── Chart Screen (GC/MGC)
           │     ├── Timeframe selector
           │     ├── Indicator menu
           │     ├── Alert set pannalam
           │     └── Trade calculator
           ├── Alerts Screen
           ├── Journal Screen
           ├── Risk Manager Screen
           └── Settings Screen
```

---

## 6. Risk Manager Logic (FundedNext Futures Special)

FundedNext-ku specific-a indha 6 rules-a app track pannanum:

| # | Rule | Official Logic | App-la Enna Kaattum |
|---|---|---|---|
| 1 | **MLL (EOD trailing)** | Moves up with balance, **never down**. Updates once/day at **5:00 PM CT**. Locks at initial balance (Legacy) or **initial + $100** (Flex/Rapid/Direct). Floating loss MLL-a touch panna **instant hard breach**. | "Stop-out level: $X,XXX.XX" + live distance in $ and points |
| 2 | **Daily Loss Limit** | Rapid Daily: $500 / $1,000 / $1,250. Rapid Pro: only if add-on. **Includes closed + floating + commissions + fees.** Soft breach → trading pauses till next day. Trails with profit. | Live "day loss remaining" + reset timer (next 5 PM CT) |
| 3 | **Consistency 40%** | `Best day P&L ÷ Total profit ≤ 40%` | Progress bar + warning when approaching |
| 4 | **Contract limit** | Fixed per model/size/phase, 1:10 mixing ratio. Excess → profit deducted, loss counted. | Max-contract badge on the order sheet |
| 5 | **No overnight holding** | Auto-close at **3:10 PM CT**, session reopens 5:00 PM CT | Countdown timer + "flat by 3:10 PM CT" reminder |
| 6 | **Prohibited-pattern guard** | No HFT, grid, micro-scalp (winning trades closed ≤10 sec), order flooding | Warn if a fill closes in <10 sec or brackets are ultra-tight |

Core position sizing:
```
Risk per trade ($) = Account size × Risk % (e.g. 0.5% or 1%)
Stop loss distance (points) = Entry − Stop
Position size = Risk $ / (Stop distance × Point value)
  GC: point value = $100 per 1 point  (tick 0.10 = $10)
  MGC: point value = $10 per 1 point  (tick 0.10 = $1)
```

Example (Rapid Pro 50K, 1% risk = $500, 5 point stop):
- GC → 500 / (5 × 100) = **1 contract**
- MGC → 500 / (5 × 10) = **10 contracts**

### "Losses Remaining" Guard — Idhu Dhaan Real Value

```
Affordable losses = MLL $ ÷ Risk per trade $
Example: Rapid Pro 50K → MLL $2,000 ÷ $500 risk = 4 losses
```

App-la idha prominent-a kaattu: **"You can afford only 4 more losses at this risk."** Prop firm-la idhu dhaan account blow aagama irukka mukkiya number — trader-oda sizing discipline-a enforce pannum.

### MLL Tracker Implementation (Careful-a Pannanum)

```kotlin
// Pseudocode — EOD trailing, daily 5:00 PM CT update
data class AccountState(
    val initialBalance: Double,   // 50_000.0
    val mllDistance: Double,      // 2_000.0 (model + size based)
    val lockOffset: Double,       // 0.0 Legacy, 100.0 Flex/Rapid/Direct
    val highestEodBalance: Double,
    val currentBalance: Double,
)

fun mllStopLevel(s: AccountState): Double {
    val lockLevel = s.initialBalance + s.lockOffset
    val trailing = s.highestEodBalance - s.mllDistance
    return minOf(trailing, lockLevel)   // never rises above lock
}

// At 5:00 PM CT daily close:
// highestEodBalance = max(highestEodBalance, closingBalance)
```

**⚠️ Common mistake:** MLL-a intraday high-water-mark-la irundhu trail pannadha. FundedNext-la **EOD balance** dhaan. So intraday profit day close-la capture aagala-na MLL lift aagaadhu — app-la idha clearly explain pannanum.

---

## 7. Roadmap

| Phase | Duration | Deliverable |
|---|---|---|
| **Phase 0 — Blueprint** | This week | Indha document ✅ |
| **Phase 1 — MVP** | 2–3 weeks | Yahoo data vachu chart + indicators + position size calculator |
| **Phase 2 — Real-time** | 2–3 weeks | Tradovate auth + `/md/getChart` + WebSocket ticks + push alerts |
| **Phase 3 — Pro** | 3–4 weeks | Journal, backtest, FundedNext drawdown meter + consistency tracker, calendar |
| **Phase 4 — Release** | 1–2 weeks | Play Store (personal build-a irundhalum sideload podhum), testing, documentation |

**Total: ~2–3 months** for a solid V1 (part-time build panna).

---

## 8. Cost Estimate

| Item | Cost |
|---|---|
| Android Studio, Kotlin, Vico, Room | Free |
| Yahoo Finance data (Phase 1) | Free |
| Firebase (FCM, Crashlytics) | Free tier |
| Backend server (optional, Phase 2) | ₹0–₹500/mo (Render/Railway free tier) |
| Tradovate data (FundedNext) | Free — challenge price-laye include |
| CME real-time direct | $50–$200+/mo (later, if needed) |
| Play Store developer account | $25 one-time |

---

## 9. Risks & Challenges

1. **Data delay (Phase 1):** Yahoo ~15 min delayed → scalping-ku set aagadhu. Phase 2-la Tradovate real-time vandhadhukku apram sari.
2. **CME licensing:** Real-time data redistribute panna mudiyadhu. Personal app-ku ok, public app-ku license venum. **Tradovate API key-a app-la hardcode pannadha — user-oda own credentials-a vechuko, phone-la mattum (EncryptedSharedPreferences / Keystore).**
3. **FundedNext automation rules:** Bots allowed, aana **HFT, order flooding, latency abuse, grid** prohibited. Semi-auto design vechuko — auto-fire illa. FundedNext support tharaadhu, so crash aana un account responsibility.
4. **EOD trailing nuances:** MLL EOD balance-la dhaan trail aagum, real-time illa. Intraday profit day close-la capture aagala-na MLL lift aagaadhu. App idha clearly explain pannala na user wrong assumption pannuvaan — **UI-la "MLL updates at 5:00 PM CT" badge kaattu**.
5. **No overnight holding:** 3:10 PM CT auto-close. App-la countdown illa-na user position open-a vechutu breach aavaan (automatic close aanaalum slippage irukkum).
6. **Chart performance:** 1m candles neraya load panna lag aagum → caching + pagination venum.
7. **Rate limits:** Tradovate API-la request limits irukku. WebSocket prefer pannanum, reconnect + token refresh logic venum (accessToken ~80 min-la expire aagum).
8. **Market hours:** FundedNext session **5:00 PM CT → 3:10 PM CT**, Fri close – Sun 5:00 PM CT gap. "Market closed" UI + holiday early-close handling venum.
9. **Rules maarum:** FundedNext 2026-la rules-a repeatedly maathirukaanga (Legacy close, MLL lock levels change). Config-driven design illa-na app rapidly outdated aagum.

---

## 10. Next Steps — Ippo Enna Pannanum?

1. ✅ **Prop firm:** FundedNext Futures — confirm aayiduchu.
2. **Account model decide pannu:** Rapid Pro / Rapid Daily / Flex + size (25K / 50K / 100K / 150K). App-la default config idhu dhaan. (Legacy closed.)
3. **FundedNext account already irukka?** — irundha Tradovate credentials vachu Phase 2-a direct-a start pannalam. Illa-na Phase 1 (Yahoo) MVP munnadi build pannalam.
4. **Phase 1 start pannalama?** — Yahoo data vachu chart + indicators + risk calculator app build start pannalam.
5. **App name decide pannalam** — e.g. "GoldPulse", "CMEGold", "AuTrade"...
6. **First login checklist:** Tradovate web-la login → CME/CBOT/NYMEX/COMEX data agreements sign → subscription active-a check pannu. Idhu mudinjaale app-ku real-time data varum.

---

## 11. Sources (Verify Pannanum, Rules Maaralam)

| Topic | Source |
|---|---|
| EAs/bots allowed, no overnight holding, margin/contract model | helpfutures.fundednext.com — "FundedNext Futures — Most Frequently Asked Questions" |
| Trading hours (5:00 PM CT → 3:10 PM CT) | helpfutures.fundednext.com — "What Are the Trading Hours in FundedNext Futures?" |
| MLL / Daily Loss Limit, lock levels, EOD trailing | helpfutures.fundednext.com — "Daily Loss Limit and Maximum Loss Limit at FundedNext Futures" |
| Contract limits by model/size | helpfutures.fundednext.com — "Contract Limits and Contract Types at FundedNext Futures" |
| Plan targets, splits, consistency | fundednext.com/futures + plan review pages |
| Tradovate API endpoints | partner.tradovate.com — API cheat sheet / partner API intro |

> Rules-a **quarterly-a re-check** pannu. FundedNext 2026-la Legacy-a close pannanga, MLL lock levels maathinanga — so app-la rule config-a **remote-updatable**-a vechuko (simple JSON on GitHub/R2), app update illama rules fix panna mudiyum.

---

*Blueprint prepared for vjk_18 — Gold Futures Android App*
*Last updated: Nov 2026 — FundedNext Futures (Tradovate) verified agst. official help center*
