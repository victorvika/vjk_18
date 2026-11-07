# BUILD GUIDE — Android Studio-la Open Panni Run Panradhu (Step-by-Step)

> Code ready. Indha sandbox-la Android SDK/JDK kedayadhu (compile inga mudiyala) — unga PC-la
> **Android Studio**-la dhaan build pannanum. Neenga developer illa naalum indha steps follow pannale podhum.

## 1. Thevaiyanadhu
- Android Studio (latest stable) — install panna JDK + Android SDK automatic-a varum
- Oru Android phone (Android 7+) + USB cable

## 2. Project Open
1. GitHub repo `victorvika/vjk_18` → branch `arena/affce881-vjk-18` clone/download
2. Android Studio → **Open** → repo folder select (root-la `settings.gradle.kts` irukum idhaan proof)
3. Gradle sync automatic-a nadakum (first time 5–10 min, internet thevai)
   - *Wrapper missing nu error vandha:* Terminal-la `gradle wrapper --gradle-version 8.7` (illa File → Settings → Gradle → "Use Gradle from: Android Studio's") — project open aagum.

## 3. Run — Modhal-la Simulator Mattum Test Pannunga ⭐
1. Run configuration-la **simulator** module select → ▶ Run (phone-la "Mock Ride Simulator" install aagum)
2. App-la ride varadhu — inimel main app test:

## 4. Main App Test (Full Loop)
1. Run configuration **app** → ▶ Run ("RideAccepter" install aagum)
2. **FREE build — subscription/plans kedayadhu.** Direct Dashboard-ku ponga.
3. **Dashboard**: 
   - `Open Accessibility Settings` → **RideAccepter Engine** ON panni allow
   - `Grant Overlay Permission` → Allow
   - Target dropdown → **Mock Ride Simulator** select
   - **START OVERLAY** click → floating ▶/■ pill varum
5. **Simulator app** open → `Simulate Incoming Ride`:
   - **₹100 ride** → filter (₹60–1000) pass → **automatic-a Accept click aaganum** + History-la entry + earnings ₹100
   - Adutha ride **₹40 preset/custom fare** → filter ignore seiyanum (accept aaga koodadhu) — `Custom fare`-la 40 type panni test pannalam
   - **Seven Wells** address ulla ride + Filter tab-la No Zone-la "Seven Wells" add + toggle ON → ignore aaganum

## 5. Core Logic Test (Android illaamalum)
```
# PC-la JDK irundha:
kotlinc core/src/main/kotlin core/src/test/kotlin -include-runtime -d verify.jar && java -jar verify.jar
# Expected: ALL CHECKS PASSED (11 checks — screenshot data vechu naan already Python mirror-la verify panniten)
```

## 6. Ippo Demo Mode-la Irupadhu (Production-ku Maathanum)
| Vishayam | Ippo | Production |
|----------|------|------------|
| Subscription | ❌ Remove panniyachu — free build, plan/expiry kedayadhu | Thevai illa |
| Target apps | Simulator + 5 real apps registry-la iruku | Real app-la test = **unga responsibility** (account ban risk, Profile tab warning paarunga) |
| Shizuku | Installed check mattum | Multi-app simultaneous tap (Phase 2) |

## 7. Build Error Vandha
Error message-ai appadiye copy panni chat-la paste pannunga — naane fix panni tharen.
