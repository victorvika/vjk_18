# LSMS v6 Clean Pro — Enna Maari Iruku?

**File:** `indicators/LSMS_v6_Clean_Pro.pine` (XAUUSD 5m/15m)

v6 unga rendu complaint-kum direct fix:

## 1. Noise pochu — "Clean (signals only)" default

Settings → **Visuals (v6) → Visual mode** default `Clean`:

| Munbu therindadhu | v6 Clean-la |
|---|---|
| Ellaa swing lines + PDH/Asia/EQH labels | **Hidden** (logic ulla run aagum, drawing theriyaadhu) |
| BOS/MSS text chart fulla | **Hidden** |
| BSL/SSL grab labels, red dots, Asia shading | **Hidden** |
| HTF zones + Order Blocks | Irukum, aana **romba faint** (background context mattum) |
| **Entry / SL / TP plan** | **Bold lines + shading** (red = risk zone, green = reward zone) |

Pazhaya style venumna Visual mode → `Standard` (v5 behaviour) illa `Full` nu maathiko. Overrides: `Style` group-la pazhaya toggles-um work aagum (clean + std/full-la).

## 2. Trade details ippo chart-laye theriyum

- Setup pass aana: **Entry (blue), SL (red), TP1 (dotted green), TP2 (green)** lines 40 bars neelum (settings-la `Trade plan extends` maathalam), nadula red/green shading. Label size perusu.
- Setup **block** aana (score 65, weak candle...): **grey colour-la `BLOCKED - NO TRADE` preview** varum — entry/SL/TP enna irundhurukum-nu padikalam, grey-na trade illa-nu clear theriyum. Vendam-na `Draw BLOCKED setup preview` off pannu.
- Dashboard-la 3 pudhu rows: **Trade plan** (`LONG 78 (A)` / `BLOCKED Short 65 (B)`), **Entry | SL**, **Targets** (TP1/TP2 values). Table perusaa irundha `Style → Show dashboard` off panni chart plan mattum paako.

## 3. Screenshot pathi

Neenga anupiya screenshot-la irundhadhu **v4** (dashboard `Discount -279%`, `Score (v4)`). v5-la fix panna ATR logic + 0–100% Premium/Discount rendu-um v6-layum iruku. **v4-a remove pannitu v6 mattum podunga + vera 2 indicators (anta "3") remove pannunga** — moonu suite serndha dhaan noise.

## Mobile tips

Phone-la chart paakaradhuna: landscape mode, dashboard top-right konjam space edukum — trade plan lines dhaan mukkiyam, dashboard venam-na off panniko. Signal vandha mattum phone-la screenshot eduthu journal-la podu.
