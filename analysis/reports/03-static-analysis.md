# Phase 3 Report — Static Code Analysis ✅ DONE (06-Nov-2026)

- **Tool:** androguard class/method/string/bytecode (const-string) analysis — `04-pass3.json`, `05-pass4.json`
- ⚠️ Secrets rule: payment UPI handle / crypto key names report-la **redacted**. Raw JSON local only.

## 1. Own Code Map (`com/example/` — 51 classes mattum dhaan app, rest libraries)

| Class | Velai |
|-------|-------|
| `AutoAcceptService` | ⭐ Engine: AccessibilityService. Fields: `fareFilter`, `locationFilter`, `multiAppClicker`, `handler+scanRunnable`, `SCAN_DEBOUNCE_MS`, `isProcessing`, `lastAcceptTime`, `knownCoordinates`, `tts`. Methods: `onAccessibilityEvent`, `handleNotificationEvent`, `collectLeafTexts`, `parseRideDetails→RideDetails`, `parseFareFromText`, `parseDistanceFromText`, `findAcceptButtons`, `performNodeClick`, `performGestureTap(path)`, `scanAndClick`, `saveRideToHistory`, `speak` (TTS) |
| `MultiAppClicker` | `clickAllAppsSimultaneously`, `clickAppByPackage`, `launchAllSupportedApps` — Shizuku vazhi simultaneous tap |
| `OverlayService` | Floating control (View layout), `checkPlanStatus` runnable (plan expiry periodic check), toggle/open-dashboard actions |
| `FareFilterManager` | SharedPrefs keys: min/max fare, min/max distance, both toggles; `isFareInRange`, `isDistanceInRange` |
| `LocationFilterManager` | Driver-zone / No-zone lists (serialize/deserialize), `normalizeText` + `isSubStringMatch`, `isLocationAllowed→FilterEvaluationResult` |
| `ShizukuManager` | `isShizukuInstalled/Running`, `requestPermission`, `executeCommand`, `tapScreen`, `tapAllCoordinates` (shell input tap) |
| `DevOptionsFixActivity` | Observed strings: executes `settings put global development_settings_enabled 0/1`, Ola Driver cache clear, Geto app (`com.android.geto`) permission grant. **Clean-room rebuild-la indha behaviour exclude (Roadmap Phase 0 rule)** |
| `PreferencesHelper` | Prefs file `auto_accept_config`: auth token, userId, saved password, **baseUrl (changeable server URL!)**, plan name/days/expiresTs, `secondsLeftAtSync + elapsedRealtime` (monotonic-clock anti-tamper), device fingerprint, click interval ms, cooldown sec, TTS on/off, multi-app mode, selected package |
| `api/ApiService` | Retrofit: `loginForm`, `getDashboard`, `heartbeat`, `createOrder`, `verifyOrder`, `paymentSuccess`, `logout` + Moshi models (`LoginResponse`: token, userId, plan, planExpires, secondsRemaining, isSubscribed, isBlocked…; `PlanCatalogItem`: id, label, days, price, desc, tag; `QrPaymentData`: amount, upiId, upiUri, qrImageUrl, orderId) |
| `repository/AuthRepository` | OkHttp + **certificatePinner + securityInterceptor + PersistentCookieJar** (session cookies prefs-la save) |
| `data/RideDatabase` (Room) | `RideHistoryEntity`: id, appName, fare(Double), fareString, pickupKm, tripKm, pickupLocation, dropoffLocation, timestamp. DAO: insert / getAll / clear |
| `security/CryptoUtils` | AES/GCM + Android Keystore (`OlaRideTaker_MasterKey_v1` alias name — key material device keystore-la) token/password encrypt |
| `security/SecurityGuard` | `isRooted`, `isFridaServerRunning`, `isDebuggerAttached`, `isProxyActive`, `performSecurityAudit` — anti-analysis checks |
| `ui/` | Compose screens: `IndexScreen`, `LoginScreen` ("LOGIN TO TERMINAL", User ID + password), `DashboardScreen`, `DashboardTimerCard`, `FilterScreen`, **`PlanRequiredScreen`** (plan illana lock), `ProfileScreen` (AppTab enum: INDEX, LOGIN, DASHBOARD, FILTER, HISTORY, PROFILE), `SubscriptionDialogs` (Plan / QR Payment / CreatedCredentials / PlanUpgraded), `PreloaderScreen` |

## 2. Supported Target Apps (`SupportedApps.<clinit>` const-strings, exact)

| Name | Package | Accept text variants (bytecode order) |
|------|---------|----------------------------------------|
| Ola Driver | `com.olacabs.oladriver` | Accept Order / ACCEPT ORDER |
| Rapido Captain | `com.rapido.rider` ⚠️ (Captain peru, rider package — developer mapping) | (universal variants) |
| Porter Driver | `com.theporter.driverapp` | Start Delivery / Pick Up |
| Swiggy Delivery | `in.swiggy.deliveryapp` | Go Online |
| Uber Driver | `com.ubercab.driver` | ACCEPT RIDE / Start Ride |

- **Universal accept variants:** `Accept, ACCEPT, accept, Ride Accept, RIDE ACCEPT, View >`
- **Fare text variants (default):** `₹, Rs., INR, Fare, Estimated Fare`
- ⚠️ Ride app mattum illa — **Swiggy delivery partner-um target!** Gig-work auto-accept general tool idhu.

## 3. Backend & Monetisation (observed, redacted)

- **Base:** `http://olaridetaker.com` (cleartext HTTP!) — endpoints: login / dashboard / heartbeat / create-order / verify-order / payment-success / logout
- **Heartbeat loop** (`MainViewModel.startHeartbeatLoop`) — server periodically plan/blocked status check, `isBlocked` flag iruku (remote kill-switch)
- **Plans (local defaults):** 1 Day (24h) · 7 Days · 15 Days · 30 Days · 365 Days. Price strings: ₹150 / ₹270 / ₹399 / ₹2999 (+ server catalog varalam)
- **Payment:** Direct UPI QR (`upi://pay?pa=••••@ybl&pn=OLARideTaker` — handle redacted) + QR bitmap ZXing generate + server verify → **CreatedCredentials (new User ID + password auto-generate!)** → auto-login
- **Distribution/support channel:** APK direct downloads (`/Shizuku.apk`, `/geto.apk`, `/shell.apk`, `/tutorial.mp4`), Telegram `t.me/olaridetaker`, YouTube channel, WhatsApp channel (links app kullaye)

## 4. Key Technical Findings Summary

1. **Debug-signed, cleartext-HTTP, dev leftovers (`10.0.2.2`, pazhaya package permissions)** — hobby/small-team build, professional release discipline illa.
2. Aana core engine design **proper**: debounce scan loop, node-click → gesture-tap fallback, coordinate memory (`knownCoordinates`), notification-event path-um iruku, TTS voice announcements, monotonic clock plan check.
3. Library bloat: 9 DEX / 35k classes ku perumbaalum Firebase AI/Vertex, Google Sign-In, Compose icons — app own code 51 classes dhaan. Recreate-na indha **bloat ellame cut panni <8 MB APK** kudukalam.

## 5. Jadx-la Confirm Panna Vendiyadhu (next round, local)

- [ ] ApiService annotation endpoint paths · [ ] SupportedApps per-app exact variant mapping
- [ ] `parseRideDetails` regex patterns · [ ] SCAN_DEBOUNCE / click interval default values
- [ ] SecurityGuard blocked-aana enna seiyum (warn/exit?) · [ ] google-services project id
