# Phase 2 Report — Manifest & Surface Map ✅ DONE (06-Nov-2026)

- **APK:** `rideaccepter-pro-max_v1.apk` · SHA-256 `474219341fd2a9e65ac7bb8f86e5153c98050604d36a5c436266e38ce96b417c`
- **Tool:** androguard 4.1.4 (Python) — jadx thevai illa, manifest full decode aayidu
- **Raw data:** `02-deep-analysis.json`, `03-pass2.json` (git-ignored, local only)

## 1. Identity

| Item | Value |
|------|-------|
| Package | `com.rideaccepterpro.max` |
| App name | Ride Accepter Pro Max |
| Version | `1.0` (versionCode 1) |
| minSdk / targetSdk | 24 (Android 7.0) / **36 (Android 16)** |
| Main activity | `com.example.MainActivity` ⚠️ code ellaame default `com.example` package-la |
| Own classes | 51 real classes (`com/example/...`), rest = libraries. Total 35,685 classes / 9 DEX |
| Tech stack | **Native Kotlin + Jetpack Compose (Material3)**, Room, DataStore, OkHttp+Retrofit+Moshi, Ktor (partial), Firebase, Shizuku API, ZXing (QR) |
| Signing | ⚠️ **Android Debug certificate** (CN=Android Debug, 2026-07-20 → 2053). Release key illa — Play Store build kedayadhu, sideload distribution dhaan. Update integrity-um weak. |

## 2. Permissions (15)

| Permission | Use (inferred) |
|------------|----------------|
| `SYSTEM_ALERT_WINDOW` | Overlay floating control |
| `FOREGROUND_SERVICE` + `FOREGROUND_SERVICE_SPECIAL_USE` | OverlayService persistent |
| `WRITE_SECURE_SETTINGS` | ⚠️ Powerful — normal app-ku kedayadhu, Shizuku/ADB grant la varum (settings modify) |
| `moe.shizuku.manager.permission.API_V23` | Shizuku API access |
| `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`, `WAKE_LOCK`, `VIBRATE` | Engine alive + alerts |
| `POST_NOTIFICATIONS`, `RECEIVE_BOOT_COMPLETED` | Notifications, boot persistence |
| `INTERNET`, `ACCESS_NETWORK_STATE` | Backend (olaridetaker.com) |
| `com.ridetaker.ola.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION` | ⚠️ **Pazhaya app (`com.ridetaker.ola`) oda leftover** — indha app first "Ola RideTaker"-a irundhiruku, rebrand copy-paste aagiruku |

## 3. Components

**Activities (own):** `MainActivity` (Compose UI), `DevOptionsFixActivity` (Hide Developer Options screen — separate non-Compose XML layout!)
**Services (own):**
- `AutoAcceptService` — AccessibilityService (core engine)
- `OverlayService` — Foreground overlay control

**Providers:** `rikka.shizuku.ShizukuProvider` (Shizuku), `FirebaseInitProvider`, AndroidX Startup

## 4. Accessibility Service Config (`res/xml/accessibility_service_config.xml`) ⭐

```xml
android:accessibilityEventTypes="0x00400860"
  = TYPE_WINDOWS_CHANGED | TYPE_WINDOW_CONTENT_CHANGED
  | TYPE_NOTIFICATION_STATE_CHANGED | TYPE_WINDOW_STATE_CHANGED
android:accessibilityFlags="0x00000052"
  = FLAG_RETRIEVE_INTERACTIVE_WINDOWS | FLAG_REPORT_VIEW_IDS | FLAG_INCLUDE_NOT_IMPORTANT_VIEWS
android:canRetrieveWindowContent="true"     ← full screen text padikum
android:canPerformGestures="true"           ← dispatchGesture tap seiyum
android:notificationTimeout="50"            ← 50ms — romba fast reaction
```

## 5. Network Security Config (`res/xml/network_security_config.xml`) ⚠️

- `cleartextTrafficPermitted="true"` (ella HTTP allow)
- Domains: `olaridetaker.com`, **`10.0.2.2`, `localhost`** — emulator dev backend-um production build-la leftover!

## 6. Layouts (View-based, Compose-ku veliya)

- `res/layout/overlay_control.xml` — floating pill: Toggle button + Dashboard button + filter status texts
  (`Zone: Delhi, Sector11`, `NoZone: Kurla` placeholder examples — developer Delhi/Mumbai sample vechu test pannirukan)
- `res/layout/activity_dev_fix.xml` — "Hide Developer Options", Target: Ola Driver App `com.olacabs.oladriver`, Shizuku status badge
- `res/raw/` — `hello.wav` (alert sound?), `videoplayback.mp4` (tutorial video), `ola_logo.jpg`, `app_logo.png`

## 7. Open Items

- [ ] Retrofit endpoint paths (annotation values) — jadx-la 100% confirm (strings-la path theriayala, methods theriyum)
- [ ] `google-services.json` values (resource strings-la) — MobSF next round
- [ ] Pazhaya `rideraccepter.apk` (54 MB) diff — same process, second round
