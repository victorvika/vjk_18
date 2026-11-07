# RideAccepter Pro Max — A-to-Z Reverse Engineering + Clean-Room Recreate Roadmap

> **Matter enna:** Google Drive-la iruka `rideaccepter-pro-max.apk`-ai (a) full reverse-engineer panni enna
> seiyudhu nu purinjikittu, (b) adhey *features* ulla pudhu Android app-ai **sollra code copy pannaama,
> clean-room-la** recreate panradhukana complete plan idhu.
> Language: Tanglish (notes) + English (technical terms) — repo docs apdiye maintain pannalam.

---

## 0. Ground Truth — Ippo Namakku Therindhadhu

### 0.1 Google Drive-la kandupidichadhu (verified, 06-Nov-2026)

| # | File | Drive File ID | Size | Created | Notes |
|---|------|---------------|------|---------|-------|
| 1 | `rideaccepter-pro-max.apk` | `1FviIUh3OtSIErGwT0b-D7eBED97_eC0O` | 24,949,212 B (23.79 MB) | 2026-11-06 | Latest copy |
| 2 | `rideaccepter-pro-max.apk` | `1D2Z6ra3Vle7KN14RLojDlZQAjJKa2kNa` | 24,949,212 B (23.79 MB) | 2026-10-26 | **Same size — probably identical duplicate** (Phase 1-la SHA-256 vechu confirm pannanum) |
| 3 | `rideraccepter.apk` | `1n_FZQ7yY5jVNDs-FnPfSh2ZWuq8QQfJ9` | 56,706,205 B (54.08 MB) | 2026-10-26 | Pazhaya/periya build. ⚠️ *Anyone-with-link = writer* a share aagiruku — idhu security risk, private aakunga |

> ✅ **UPDATE (06-Nov-2026, second session):** APK Drive connector vazhiya sandbox-kulla vandhudu!
> Full static analysis **mudinjidu** — Phase 1, 2, 3 reports ready:
> [`01 Fingerprint`](analysis/reports/fingerprint.md) · [`02 Manifest Map`](analysis/reports/02-manifest-map.md) ·
> [`03 Static Analysis`](analysis/reports/03-static-analysis.md) · Engine spec: [`docs/ENGINE_SPEC.md`](docs/ENGINE_SPEC.md) ·
> Backend spec: [`docs/BACKEND_SPEC.md`](docs/BACKEND_SPEC.md)
> **Headline findings:** `com.rideaccepterpro.max` v1.0, Native Kotlin+Compose, own code 51 classes (`com.example`),
> engine = `AutoAcceptService` + `OverlayService`, targets = Ola/Rapido/Porter/Swiggy/Uber,
> backend = olaridetaker.com (cleartext), debug-signed ⚠️. Remaining: jadx-la exact regex/endpoints (local round).

### 0.2 Screenshots-la irundhu therindha features (3 screenshots, 15–16 Aug 2026)

Full spec: [`docs/FEATURE_INVENTORY.md`](docs/FEATURE_INVENTORY.md). Summary:

- **Dashboard:** App status `IDLE`, plan countdown (00:11:29:46), expiry `16 Aug 2026 01:51 PM`,
  User/Plan `OLA949E169 (1_day)`, System Status (Accessibility ENABLED, Shizuku ACTIVE, Overlay GRANTED,
  Shizuku READY), `START OVERLAY` / `STOP`, Target App dropdown = **Rapido Captain**
- **Ride Filters:** Fare ₹60–₹1000 (ON), Distance KM (OFF), Driver Zone / allowed locations (OFF, empty),
  No Zone / blocked locations (OFF, 1 entry: "seven wells")
- **History:** Total ₹589, 6 rides auto-accepted; ride card = fare, pickup+trip km (e.g. `1.0 + 3.2 km`),
  pickup/drop address + timestamp. Areas: Sembakkam / Rajakilpakkam / Selaiyur, Chennai
- **Bottom nav:** Plans · Login · Dashboard · Filter · History · Profile (6 tabs)

---

## 1. GitHub Reverse-Engineering Toolchain (Single repo illa — oru chain)

"GitHub-la reverse engineering repo" nu onnu illa; industry standard chain idhu.
Curated index repo: **Awesome-Android-Reverse-Engineering** (`user1342/Awesome-Android-Reverse-Engineering`) —
static/dynamic/decompiler tools ellame category-wise list pannirukum, anga irundhu dhaan keela ulla tools select panrom.

| Phase | Tool | GitHub | Velai enna |
|-------|------|--------|-----------|
| Triage | **Androguard** | `androguard/androguard` | Python-la package, permissions, components, DEX parse |
| Triage | **APKiD** | `rednaga/APKiD` | Packer / obfuscator / compiler fingerprint |
| Static | **jadx / jadx-gui** | `skylot/jadx` | DEX → readable Java/Kotlin source (main decompiler) |
| Static | **Apktool** | `iBotPeaches/Apktool` | Resources + smali, AndroidManifest decode, rebuild capability |
| Static | **MobSF** | `MobSF/Mobile-Security-Framework-MobSF` | One-shot automated report: manifest, cert, secrets, URLs, trackers |
| Static | **APKLeaks** | `dwisiswant0/apkleaks` | API keys, endpoints, Firebase config scan |
| Static | **APKLab** (VS Code) | `APKLab/APKLab` | jadx+apktool integration, orey IDE-la |
| Dynamic | **Frida + Objection** | `frida/frida`, `sensepost/objection` | Runtime-la enna nadakudhu nu own test device-la observe |
| Dynamic | **PCAPdroid / mitmproxy** | `emanuele-f/PCAPdroid` | Own device network traffic (endpoints categories theriya) |
| Reference | **Shizuku** (original app use panradhu) | `RikkaApps/Shizuku` | ADB-level API without root — pudhu app-layum idhey library dhaan official vazhi |

Setup commands + day-by-day runbook: [`analysis/README.md`](analysis/README.md)

---

## 2. Roadmap — Phases 0 → 12 (A to Z)

### Phase 0 — Scope, Safety, Legal Gate (Day 0–1) ⛔ Skip panna koodadhu
- [ ] **Clean-room rule:** Original APK code, logo, name, assets copy panna koodadhu. Features/behaviour
      mattum spec-a eduthu, pudhu code eludhanum. "Ride Accepter Pro Max" branding-um reuse panna koodadhu.
- [ ] **License/plan system crack panna koodadhu:** Original server, keys, plan bypass — analysis scope-ku
      veliya. Pudhu app-ku **sollra own** licensing backend dhaan build pannanum (Phase 9).
- [ ] **Platform risk purinjikonga:** Rapido/Ola maari driver apps-oda Terms, auto-accept automation-ai
      thadai seiyalam; driver account ban risk undu. Indha risk-ai product decision-a document pannunga.
      Detection-evasion ("developer options maraikaradhu" maari) features — indha roadmap-la
      **implement panna sollala**; compatibility check + user warning-a maatum design pannalam.
- [ ] Isolated test setup: second phone / emulator, test account, real driver account analysis-ku vendaam.
- **Exit criteria:** `docs/SCOPE.md`-la enna pannalam / panna koodadhu nu sign-off.

### Phase 1 — APK Acquisition & Fingerprint (Day 1–2) ✅ DONE — `analysis/reports/fingerprint.md`
```bash
# Drive-la irundhu rendu copy-yum download panni (local machine):
cp rideaccepter-pro-max.apk analysis/original/rideaccepter-pro-max_v1.apk
cp rideraccepter.apk       analysis/original/rideraccepter_old.apk
sha256sum analysis/original/*.apk          # rendu pro-max copy identical-a?
python3 analysis/scripts/apk_fingerprint.py analysis/original/rideaccepter-pro-max_v1.apk \
        --json analysis/reports/fingerprint.json --md analysis/reports/fingerprint.md
```
- [ ] Aapt badging: `aapt dump badging app.apk` → package name, versionCode/Name, min/target SDK, launchable activity
- [ ] Certificate: `keytool -printcert -jarfile app.apk` / `apksigner verify --print-certs app.apk`
- [ ] Virus/safety scan (VirusTotal — private sample option) — third-party APK trust panna munnadi
- **Deliverable:** `analysis/reports/fingerprint.md` · **Exit:** Stack guess (Native/Flutter/RN) confirm.

> **Size clue:** Pro Max 23.8 MB vs pazhaya build 54 MB. Flutter build-na `libflutter.so` +
> `assets/flutter_assets/` irukum; Native-na `classes*.dex` + `res/layout` adhigam irukum.
> Script indha decision-ai automatic-a sollum. Stack therindha dhaan Phase 3 depth maarum.

### Phase 2 — Manifest & Surface Map (Day 2–3) ✅ DONE — `analysis/reports/02-manifest-map.md`
- [ ] `apktool d app.apk -o analysis/decompiled/apktool/` → decoded `AndroidManifest.xml`
- [ ] List pannunga: package, **permissions** (expected: `SYSTEM_ALERT_WINDOW`, Accessibility bind,
      `FOREGROUND_SERVICE`, `INTERNET`, `QUERY_ALL_PACKAGES`?), activities, services, receivers, providers
- [ ] Kandupidikka vendiyadhu: AccessibilityService class name + `accessibility-service` XML config
      (endha package events kekudhu — Rapido Captain package id), Overlay/Foreground service,
      Shizuku provider (`rikka.shizuku.ShizukuProvider` iruka?), deep links
- [ ] Exported components + intent filters — pudhu architecture-ku input
- **Deliverable:** `analysis/reports/02-manifest-map.md` (template: `analysis/templates/ANALYSIS_REPORT_TEMPLATE.md`)

### Phase 3 — Static Code Analysis (Day 3–7) ✅ DONE (androguard) — `analysis/reports/03-static-analysis.md` · jadx confirm pending
- [ ] **jadx-gui**-la APK open panni package tree map: UI / engine / licensing / network packages pirikunga
- [ ] **MobSF** (Docker) full report: hardcoded URLs, Firebase, trackers, crypto, WebView, cert pinning iruka
- [ ] **APKLeaks** scan → endpoints list (secrets redact panni report; keys *reuse panna koodadhu*)
- [ ] Strings/resources: `res/values/strings.xml`, layouts, colors — UI text/flow puriya
      (Screenshot oda match pannunga: "PLAN ACTIVE — TIME REMAINING", "SAVE FARE RANGE" etc.)
- [ ] Obfuscation iruka (R8/ProGuard `a.a.a` class names)? Irundha jadx-la flow kandupidika kashtam —
      string anchors + resource IDs vechu navigate pannunga
- **Deliverables:** `03-static-analysis.md`, `03-endpoints-and-config.md` (redacted), class responsibility map

### Phase 4 — UI/UX Reconstruction (Day 5–7, parallel)
- [ ] 6 tabs oda screen inventory: Dashboard, Filters, History, Plans, Login, Profile
      (Plans/Login/Profile screenshots illa — APK layouts-la irundhu complete pannunga)
- [ ] Design tokens extraction (screenshots): bg `#0B0B10`-ish black, accent red `#FF0A3C`-ish,
      success green, card radius, typography — **pudhu brand identity**-a adapt pannunga, logo copy vendaam
- [ ] Ovvoru screen-um: states (loading/empty/error/plan-expired), clicks, navigation graph varaiyunga
- **Deliverable:** `docs/FEATURE_INVENTORY.md` update + Figma/wireframe (illa paper sketch photo)

### Phase 5 — Dynamic / Runtime Analysis (Day 7–10) — Own test device mattum
- [ ] Test phone-la install, permission flow record: Accessibility ON → Overlay grant → Shizuku start
      (Shizuku official app + wireless debugging/ADB flow)
- [ ] `adb logcat` tags, app state transitions: IDLE → overlay running → stop
- [ ] Screen-by-screen video/screenrecord + filter set panni behaviour notes
- [ ] Frida/Objection = **own app observe panna mattum** (function calls order, parser input/output).
      Vera app (Rapido) hook/pin-bypass indha roadmap scope-la illa — dummy target app (Phase 8) vechu test pannalam.
- **Deliverable:** `05-runtime-behaviour.md` — state machine + sequence notes

### Phase 6 — Network & Licensing Behaviour (Day 9–11)
- [ ] Own device traffic (PCAPdroid): endha domains, plan check frequency, expiry check epdi
      (online verify-a illa local clock-a?), login flow (phone/OTP? user id?)
- [ ] Telivupaduthunga: plan `1_day` pricing, payment method (UPI?), `OLA949E169` format
      = prefix + random ID pattern-a? (own backend design-ku input mattum)
- **Deliverable:** `06-backend-surface.md` — endpoint *categories* (auth, plan, config), **no copied credentials**

### Phase 7 — Core Engine Logic Reconstruction (Day 10–14) ⭐ ✅ SPEC READY — `docs/ENGINE_SPEC.md`
Original app-oda idhayam (inferred from screenshots + static analysis-la confirm pannanum):
```
Target app screen (ride offer)
   → [1] Event capture: AccessibilityEvent (window/content changed)
   → [2] Parse: fare ₹, pickup km, trip km, pickup/drop text (node tree + regex)
   → [3] Rule engine: fare range ✓/✗, distance ✓/✗, zone allow-list, no-zone block-list
   → [4] Decision: MATCH → accept action; NO-MATCH → ignore (observe mattum)
   → [5] Record: History + earnings total update
```
- [ ] Ovvoru step-kum: input/output, failure modes (fare parse aagala, address split, language)
- [ ] "Reject" nu history address-la kalanthu varudhu screenshot-la theriyudhu — original parser
      screen text-ai appdiye scrape panradhu naala varra artifact. Pudhu app-la address clean panna rules eludhanum.
- [ ] Debounce/cooldown: orey ride-ku multiple events vandha double-action aaga koodadhu
- **Deliverable:** `docs/ENGINE_SPEC.md` — parser spec, rule-engine truth table, state machine

### Phase 8 — Recreate: Architecture & Project Setup (Week 3) ✅ DONE (06-Nov-2026) — Gradle project ready: `:app` (Compose UI + Accessibility engine + Overlay), `:core` (parser/rules, verified), `:simulator` (mock target app). See `BUILD_GUIDE.md`
**Recommended stack (Native branch — Phase 1 confirm aanal):**
- Kotlin + Jetpack Compose + Material 3 (dark theme), minSdk 26 / targetSdk latest
- Multi-module: `:app` · `:core:database` (Room) · `:core:datastore` (preferences) ·
  `:feature:dashboard|filters|history|plans|profile` · `:engine:accessibility` · `:engine:overlay` · `:engine:rules`
- DI: Hilt · Async: Coroutines/Flow · Nav: Compose Navigation (6 bottom tabs)
- Shizuku: official `dev.rikka.shizuku:api` — permission/status check mattum, sollra scope-la
- **First build a "Mock Ride Simulator"** — pudhu dummy app, ride-offer screen maariye kaatum;
  parser + rule engine-ai Rapido illama 100% test panna idhu dhaan safe vazhi
- Flutter/RN branch aanal: Phase 1 stack guess base panni adhey stack select pannunga,
  architecture layers (parser/rules/db) concept same.

### Phase 9 — Recreate: Feature Sprints (Week 3–6) 🔶 S1–S4 DONE (Dashboard, Filters, Engine, History working code; Plans/Login = local demo, own backend pending)
| Sprint | Deliverable | Screenshot parity |
|--------|-------------|-------------------|
| S1 | Dashboard: status card, plan countdown timer, system-status checklist (Accessibility/Shizuku/Overlay real checks), Start/Stop overlay, target-app dropdown | Screenshot 1 ✓ |
| S2 | Filters: fare range save, distance toggle, zone/no-zone CRUD (add/edit/delete locations), persistence (DataStore/Room) | Screenshot 2 ✓ |
| S3 | Engine: AccessibilityService + node parser (mock app mela), rule engine, overlay floating UI, foreground service notification | — (core) |
| S4 | History: ride cards, total earnings, clear-history, Room queries, empty state | Screenshot 3 ✓ |
| S5 | Own backend: auth/login, Plans (pricing, Razorpay/UPI), plan activation + server-time expiry, Profile | Nav tabs ✓ |
| S6 | Polish: plan-expired lock screen, permission onboarding wizard, settings, logs/debug screen | — |

### Phase 10 — Testing (Week 5–7, parallel)
- [ ] Unit tests: rule engine (fare ₹60/₹1000 boundary, zone contains-match, empty list = accept all),
      parser fixtures (real screen text samples, ₹/km regex, Tamil/English address)
- [ ] UI tests: Compose, filter CRUD, countdown
- [ ] Device matrix: Android 10–15, Samsung/Xiaomi/Realme (battery optimization + accessibility reliability vera vera)
- [ ] Failure tests: target app UI maarina parser graceful-a fail (crash illa), overlay permission revoke
- [ ] Battery/heat: accessibility event frequency throttle

### Phase 11 — Hardening, Policy & Release (Week 7–8)
- [ ] Play Store: Accessibility API use panna apps-ku strict declaration — reject chance adhigam.
      Distribution decision: direct APK / own website + clear user consent (document pannanum)
- [ ] Privacy policy: screen content access panradhu naala enna data collect panrom/pannom nu velippadai
- [ ] Signing: own keystore (safe backup), versioning, update check (own server/GitHub releases)
- [ ] Crash reporting (Firebase Crashlytics — own project), analytics opt-in

### Phase 12 — Maintain (Ongoing)
- [ ] Target app (Rapido Captain) UI update aana parser break aagum — version-wise parser adapters,
      remote config-a selectors update panna mechanism (own backend)
- [ ] Chase panna koodadhu: anti-detection cat-and-mouse. Bathila user-ku transparent status +
      "target app updated, parser not verified" warning kaatunga

---

## 3. Timeline Summary (1 developer)

| Week | Phase | Result |
|------|-------|--------|
| 1 | 0–3 | Scope, fingerprint, manifest, jadx/MobSF reports |
| 2 | 4–7 | UI inventory, runtime notes, **ENGINE_SPEC freeze** |
| 3 | 8 + S1–S2 | Project setup, Dashboard + Filters working |
| 4 | S3 | Engine (mock app mela full auto flow) |
| 5 | S4–S5 | History + own licensing backend |
| 6 | S6 + 10 | Polish, device testing |
| 7–8 | 11 | Hardening, release candidate |
| — | 12 | Maintenance mode |

2 developers (UI + Engine parallel) na 5–6 weeks. **Realistic solo estimate: 6–8 weeks.**

## 4. Repo Structure (indha repo apdiye grow aagum)

```
vjk_18/
├── ROADMAP.md                  ← indha file
├── docs/
│   ├── FEATURE_INVENTORY.md    ← screenshot + APK feature spec
│   ├── SCOPE.md                ← Phase 0-la create pannanum
│   └── ENGINE_SPEC.md          ← Phase 7-la create pannanum
├── analysis/
│   ├── README.md               ← RE lab runbook (commands)
│   ├── original/               ← APK copies (GITIGNORE — repo-la commit pannaadha)
│   ├── scripts/apk_fingerprint.py
│   ├── templates/ANALYSIS_REPORT_TEMPLATE.md
│   └── reports/                ← phase reports inga varum
└── app/                        ← Phase 8-la Android project inga varum (pudhu, clean-room)
```

## 5. First Commands (Nalaikke start panna)

```bash
# 1. APK-ai inga koondhu vaa (Drive-la irundhu download panni):
#    analysis/original/rideaccepter-pro-max_v1.apk
# 2. Fingerprint:
python3 analysis/scripts/apk_fingerprint.py analysis/original/rideaccepter-pro-max_v1.apk \
  --md analysis/reports/fingerprint.md
# 3. Tools install (analysis/README.md full list):
#    jadx-gui, apktool, MobSF (docker), androguard, apkid
# 4. Report fill panna start: analysis/templates/ANALYSIS_REPORT_TEMPLATE.md
```

**Adutha step sollunga:** APK-ai `analysis/original/`-la veinga (illa local-la commands run panni
`fingerprint.md` output paste pannunga) — Phase 1–3 reports-ai actual data vechu complete panni,
`docs/ENGINE_SPEC.md` + Android project skeleton (Phase 8) create panni tharen.
