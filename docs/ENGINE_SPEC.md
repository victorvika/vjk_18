# ENGINE_SPEC — Auto-Accept Engine (Clean-Room Spec)

> Source: `AutoAcceptService` class/method/field names + accessibility config + screenshots.
> Idhu behaviour spec — original code illa. Pudhu app-ku implement panna blueprint.
> Exact regex/default values jadx round-la confirm aaganum (Phase 3 open items).

## 1. Components

```
┌────────────────┐  events   ┌──────────────────┐  RideDetails  ┌──────────────┐
│ Target App UI  │──────────▶│ AutoAcceptService │──────────────▶│ Rule Engine  │
│ (ride offer)   │           │ (Accessibility)   │               │ Fare+Location│
└────────────────┘           └──────────────────┘               └──────┬───────┘
        ▲                            │ parse: fare/km/address          │ MATCH
        │ click/gesture              ▼                                 ▼
┌───────┴────────┐           ┌──────────────────┐               ┌──────────────┐
│ Action Layer   │◀──────────│ Decision+Cooldown │               │ History(Room)│
│ node/gesture/  │           └──────────────────┘               │ + Earnings   │
│ Shizuku tap    │                                               └──────────────┘
└────────────────┘    ┌───────────────┐   ┌────────────────┐
                      │ OverlayService │   │ TTS speak()    │ (optional voice alert)
                      └───────────────┘   └────────────────┘
```

## 2. Event Pipeline (original method names base-la)

1. **Trigger — rendu vazhi:**
   - `onAccessibilityEvent` — window/content changed (config: 50ms timeout, all windows, view IDs)
   - `handleNotificationEvent` — ride notification vandhalum scan start
2. **Debounced scan loop:** `handler + scanRunnable`, `SCAN_DEBOUNCE_MS`, `isProcessing` guard —
   orey time-la parallel scan illa.
3. **Collect:** `collectLeafTexts(rootNode)` — screen-la ella leaf node texts-um list.
   `determineAppNameFromText` — endha app ride nu text vechu kandupidikum.
4. **Parse → `RideDetails`:** `parseFareFromText` (variants: `₹, Rs., INR, Fare, Estimated Fare`),
   `parseDistanceFromText` (pickup km + trip km), pickup/dropoff address lines.
5. **Rules (truth table):**

   | Fare filter ON & fare ∉ [min,max] | → IGNORE ("Fare out of range") |
   | Distance ON & km ∉ [minDist,maxDist] | → IGNORE |
   | No-Zone ON & address contains blocked (normalized substring) | → IGNORE |
   | Driver-Zone ON & list non-empty & address NOT contains any allowed | → IGNORE |
   | Ellame pass | → **ACCEPT** |

   `LocationFilterManager.normalizeText` (lowercase, trim, extra-space remove) + `isSubStringMatch`.
6. **Action — moonu level fallback:**
   1. `findAcceptButtons` (text variants per-app + universal) → `performNodeClick` (ACTION_CLICK)
   2. Fail aana → `performGestureTap` (node bounds center, `GestureDescription` stroke)
   3. Multi-app mode → `MultiAppClicker.clickAllAppsSimultaneously` / Shizuku `tapAllCoordinates`
   - `knownCoordinates` — successful tap coordinates nyabagam vechu next time fast.
7. **Cooldown:** `lastAcceptTime` + `KEY_COOLDOWN` (sec, configurable) + `KEY_CLICK_INTERVAL` (ms).
8. **Record:** `saveRideToHistory` → Room `RideHistoryEntity(appName, fare, fareString, pickupKm, tripKm, pickupLocation, dropoffLocation, timestamp)` → History screen + Total Earnings.
9. **Announce:** `speak()` TTS (toggle in prefs) — accepted ride details voice-la.

## 3. Parser Spec (pudhu implementation)

```kotlin
data class RideDetails(
    val appName: String, val appPackage: String,
    val fareAmount: Double?, val fareText: String?,
    val pickupKm: Double?, val tripKm: Double?,
    val pickupText: String?, val dropoffText: String?
)
// Fare regex:  (₹|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)   |  Fare[:\s]*...
// Km regex:    ([\d.]+)\s*km
// Address clean: drop standalone action words (Accept/Reject/View) — original bug fix
```

## 4. Supported Apps Config (JSON-a maintain — code hardcode vendaam)

```json
[
 {"name":"Ola Driver","pkg":"com.olacabs.oladriver","accept":["Accept Order","ACCEPT ORDER"]},
 {"name":"Rapido Captain","pkg":"TBC — jadx confirm","accept":[]},
 {"name":"Porter Driver","pkg":"com.theporter.driverapp","accept":["Start Delivery","Pick Up"]},
 {"name":"Swiggy Delivery","pkg":"in.swiggy.deliveryapp","accept":["Go Online"]},
 {"name":"Uber Driver","pkg":"com.ubercab.driver","accept":["ACCEPT RIDE","Start Ride"]}
]
```
Universal: `Accept, ACCEPT, accept, Ride Accept, RIDE ACCEPT, View >`

## 5. State Machine & Safety (pudhu design)

```
IDLE ──START──▶ RUNNING ──plan expired (OverlayService periodic check)──▶ LOCKED(PlanRequired)
 ▲                 │ target app UI maarina / parse fail ×N
 └────STOP─────────┴──▶ DEGRADED (user-ku "parser update needed" nu kaatu, crash vendaam)
```
- Mock Ride Simulator app dhaan mudhal test target — real driver apps-la direct test vendaam.
- Dev-options-hide maari evasion features **indha spec-la illa** (Phase 0 rule) — bathila permission
  status check + user guidance mattum.

## 6. Config Defaults (PreferencesHelper keys-la irundhu)

Prefs file: `auto_accept_config` · Keys: click_interval_ms, cooldown_sec, tts_enabled, multi_app_mode,
selected_package, plan_expires_ts + seconds_left_sync/elapsed_realtime_sync (server-time monotonic check).
