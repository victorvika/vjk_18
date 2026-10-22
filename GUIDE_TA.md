# VJK PropFirm Edge Pro - Tamil Guide (Tanglish) 🇮🇳

Vanakkam da! Idhu thaan propfirm la trade panna **best indicator** - full guide Tamil la!

---

## Yen Ithu PropFirm ku Best?

Normal indicator ellam trend mattum kaatum. Ana **prop firm la trend vida risk management thaan mukkiyam!**

- Daily 5% loss = account close!
- Max 10% drawdown = fail!
- Overtrading = consistency rule breach!

Adhanala naan **research panni** (FTMO, Topstep, Apex, FundedNext strategies) oru **all-in-one** indicator build panniten:

> **VWAP + EMA + ATR SuperTrend + RSI + MACD + Volume + Session Filter + Kill Switch + Dashboard**

Oru indicator la ellam irukku - vera ethuvum theva illa!

---

## Part 1: Installation (2 Nimisham)

### TradingView Free Account kooda pothum!

1. **TradingView.com** open pannu -> Chart open pannu (NAS100, US30, EURUSD ethuvum)
2. Keela `Pine Editor` nu irukkum - atha click pannu
3. `VJK_PropFirm_Edge_Pro_Indicator.pine` file la irukka code full-a copy pannu
4. Pine Editor la paste pannu -> `Add to Chart` click pannu
5. Mudinchu! Chart la BUY/SELL signals + VWAP + EMA ellam vanthidum

**Second file (Strategy):** Backtest panna thaan. Adha separate ah Pine Editor la add pannanum - Tester tab la profit paaka.

---

## Part 2: Settings Eppadi Mathanum?

Chart la indicator peru pakkathula **⚙️ gear icon** click pannu:

### 🏦 PROP FIRM SETTINGS

**Example 1: FTMO 100k Challenge**
```
Account Size: 100000
Max Daily Loss %: 5      (FTMO rule)
Max Total Loss %: 10     (FTMO rule)
Profit Target %: 8       (Phase 1)
Risk Per Trade %: 0.5    (IMPORTANT! 0.5 thaan best)
```

**Example 2: Apex 50k (Futures)**
```
Account Size: 50000
Max Daily Loss %: 3      (Apex trailing)
Max Total Loss %: 6
Profit Target %: 6
Risk Per Trade %: 0.5
```

**Example 3: The5ers 20k**
```
Account Size: 20000
Max Daily Loss %: 5
Max Total Loss %: 6
Profit Target %: 8
Risk Per Trade %: 0.7
```

> **Risk 0.5% yen?** 100k account ku $500 per trade. 5 losing streak vanthalum $2500 thaan loss = daily limit 50% thaan! Safe!

### ⚙️ STRATEGY ENGINE

- **Puthusa?** -> `Conservative (Prop Safe)` select pannu - signals koravu, ana quality high!
- **Experience?** -> `Aggressive` or `Scalping` - trades athigam
- **Swing trader?** -> `Swing (15m-1H)` - daily chart ku best

### 📊 INDICATOR SETTINGS

Default settings already best research pannathu:
- EMA 9,21,50,200 - trend confirm
- ATR 14, 1.5x SL - 5m chart ku perfect
- SuperTrend 2.5x - NAS100/US30 ku best
- RSI 70/30 - overbought avoid

**Matha theva illa - default la ye use pannalam!** Gold mattum ATR 2.0x ku mathu (volatility athigam).

### 🕒 SESSION SETTINGS

- **Forex/Indices (FTMO):** London ON, NY ON
- **US Futures (Topstep/Apex):** London OFF, NY ON mattum
- **Midday Avoid:** ON pannu - 11:30-13:30 ET la market chop aagum, loss varum
- **Max Trades/Day:** 3 - itha thandina indicator auto block pannidum!

---

## Part 3: Eppadi Trade Pannanum? (Step-by-Step)

### 🟢 BUY Entry Example

1. Chart la **"BUY"** label vantha (green arrow keela)
2. Check pannu:
   - Dashboard la `Trend = 🟢 BULL` irukka?
   - `Session = 🟢 OPEN` irukka?
   - `Trades Today < 3` irukka?
3. Ellam OK-na entry edukalam!
4. **SL = Red dashed line**, **TP1 = Green dashed line** - chart la auto draw aagum
5. TP1 la 50% close pannu, balance TP2 ku trail pannu (BE ku move pannu)

### 🔴 SELL Entry Example

Same, aana `Trend = 🔴 BEAR` + `SELL` label vantha

### ❌ Trade Panna Koodathu - Eppo?

- Dashboard `⛔ KILL SWITCH` nu kaatuna - STOP! Daily limit mudinchu
- Background **orange** (midday chop) - trade pannath inga loss thaan
- **VWAP ku opposite** - VWAP mela iruntha SELL pannath, keela iruntha BUY pannath
- **News time** - Red news ku 30min muna trade pannath (FTMO kooda news allowed ana risk athigam!)
- **Emotion la** - 2 loss thodarndhu vantha innaiku trading mudinchu - naalaiku paakalam

---

## Part 4: Alerts Set Pannurathu

Phone la notification vara:

1. Chart la `Alt + A` or Right click -> `Add Alert`
2. Condition: `VJK PropFirm Edge Pro` -> `BUY Signal` select pannu
3. Options: `Notify on App` + `Show Popup` tick pannu
4. Create pannu
5. Same for `SELL Signal` + `Daily Limit Hit`

TradingView app mobile la install panniruntha phone ku direct varum - chart paathute irukka theva illa!

---

## Part 5: Backtest Panni Check Pannurathu (Important!)

### Yaro sonna indicator ah nambama, neeye test pannu!

1. Pine Editor la `VJK_PropFirm_Edge_Pro_Strategy.pine` code paste pannu -> `Add to Chart`
2. Keela `Strategy Tester` tab open pannu
3. Paarunga:
   - **Net Profit:** Positive ah?
   - **Profit Factor:** 1.3 kulla irukka? (1.0 kulla iruntha waste)
   - **Max Drawdown:** Account size la 8% kulla irukka?
   - **Win Rate:** 45-55% iruntha super - 60% kku mela expect pannath (prop la impossible!)

**Test panna timeframe:**
- Forex: 15m, 1H
- Indices: 5m, 15m
- Futures: 5m (MES/MNQ ku best)

**Time period:** Last 6 months - 1 year data la test pannu. 1 month mattum paatha matha pothathu!

---

## Part 6: Prop Firm Tips (Challenge Pass Panna)

### 5 Golden Rules:

**1. Risk 0.5% thaan!**
100k ku $500, 50k ku $250. 1% kuda athigam thaan daily DD ku. 5 loss streak la account safe ah irukanum.

**2. Daily Target 0.5% - 1% pothum!**
8% target ku 10-15 trading days la mudikkalam. Oru nalaikka 3% eduka try pannina daily loss thaan varum. Slow and steady!

**3. 2 Trades ku mela loss vantha STOP!**
Revenge trading thaan prop fail ku main reason. Indicator kill switch 3 trades nu solrathu summa illa - respect pannu.

**4. London or NY mattum trade pannu - full day chart paathute irukka theva illa!**
Session fixed pani, alert set pani, velai paaru. Signal vantha mattum vanthu trade pannu.

**5. Demo la 2 weeks practice pannu!**
Direct challenge ku pogath. Indicator purinju, alerts purinju, profit factor nalla irukku nu confirm pannitu pin challenge eduthuko.

### FTMO Specific:
- FTMO ippo TradingView direct trading support pannuthu - indicator signal vantha TradingView la ye order poda mudiyum!
- Free Trial challenge first try pannu - rules puriyum

### Topstep/Apex Specific:
- EOD trailing drawdown - overnight hold pannath (indicator session filter NY mattum nu vechu)
- Evaluation la 5 winning days venum - daily consistency thaan mukkiyam

---

## Part 7: Market-Specific Settings

| Market | Timeframe | ATR SL | Notes |
|--------|-----------|--------|-------|
| **NAS100** | 5m | 1.5x | FTMO ku most popular, volatility athigam |
| **US30** | 5m | 1.5x | NAS100 vida slow, beginners ku easy |
| **GER40** | 15m | 1.5x | London session ku best |
| **EURUSD** | 15m/1H | 1.5x | Forex la spread koravu, prop ku safe |
| **XAUUSD (Gold)** | 15m/1H | 2.0x | ATR perusu - 1.5x la SL adikadi hit aagum |
| **BTCUSD** | 1H/4H | 2.0x | Crypto 24/7 - VWAP off panni use pannu |
| **MES (S&P micro)** | 5m | 2.5x | Topstep 50k ku best - research result |
| **MNQ (Nasdaq micro)** | 5m | 2.5x | Apex 50k ku best |

---

## Part 8: Common Mistakes (Pannathinga!)

❌ **Mistake 1:** Indicator signal ellam edukarathu - 5/6 confluence irukka nu paama random entry
✅ Correct: Dashboard `✅ READY` + Trend match + Session OPEN nu iruntha mattum entry

❌ **Mistake 2:** SL ah move pannarathu (loss perusa varathu ku)
✅ Correct: ATR SL thaan final - move pannath, hit aana accept pannu, next trade ku po

❌ **Mistake 3:** TP ku muna close pannarathu (fear)
✅ Correct: TP1 auto level thaan - 1:1.5 RR kudukkurom, atha respect pannu

❌ **Mistake 4:** Martingale (loss ku pin double lot)
✅ Correct: Prop firm la martingale = instant fail. Fixed 0.5% thaan eppavum!

❌ **Mistake 5:** Indicator mattum nambi fundamentals paakama irukkarathu
✅ Correct: High impact news (NFP, CPI, FOMC) time la trade pannath - calendar check pannu

---

## Part 9: Enna Expect Pannalam?

**Realistic expectations:**

- Daily 1-3 signals thaan varum (Conservative mode)
- Winrate 50% average - 10 trades la 5 win, 5 loss
- Ana RR 1:1.5 - 1:2.5 na: 5 wins = +$3500, 5 losses = -$2500, Net = +$1000 (100k account la)
- Monthly 4-6% growth realistic - 1 month la double pannuvom nu expect pannath

**Prop firm evaluate pannrathu:**
- Profit vida **consistency** and **discipline** thaan mukkiyam!
- Indicator unakku discipline enforce pannuthu - kill switch, session filter ellam athukku thaan

---

## Help Theva na?

- TradingView la indicator add panna error vantha: Pine Editor la `// @version=5` first line irukka nu check pannu
- Signals varala na: Timeframe 5m/15m mathi paaru, Session ON irukka nu paaru, market open ah nu paaru
- Dashboard theriyala na: Settings la `Show Prop Dashboard` ON irukka nu paaru

**Wishes:** Challenge pass panni funded trader aaganum nu vaazhthukkal da! 💪🔥

**Remember:** Indicator oru tool mattum thaan - un discipline thaan unakku payout kudukkum!

---

VJK_18 | Tamil Traders Community | 2025
