# Feature Inventory — Screenshots + Drive APK (Observed Spec)

> Source: 3 screenshots (15–16 Aug 2026, 2:21–2:22 AM) + Google Drive metadata.
> Idhu *observed behaviour* spec — original code/design copy illa. Pudhu app (clean-room) build panna reference.

## 1. App Identity (Observed)
- **Name:** Ride Accepter Pro Max · **Tagline:** "Automatic High-Speed Clicker"
- **Downloads in Drive:** `rideaccepter-pro-max.apk` 23.79 MB (2 copies, Oct 26 + Nov 6),
  `rideraccepter.apk` 54.08 MB (older build — 30 MB size difference → stack/feature change aagirukalam, Phase 1-la confirm)

## 2. Screens

### 2.1 Dashboard (Screenshot 1)
| Element | Detail |
|---------|--------|
| Header card | Logo + app name + tagline; status pill `● IDLE` (red border when idle) |
| Plan card | `PLAN ACTIVE — TIME REMAINING`, countdown `DD : HH : MM : SS` ticking live |
| Plan meta | `Expires on 16 Aug 2026, 01:51 pm` · `User ID / Plan: OLA949E169 (1_day)` (red) |
| System Status | 4 rows, each: label + green dot + value + `GRANTED` chip |
| | `Accessibility Service → ENABLED` · `Hide Developer Options → SHIZUKU ACTIVE` |
| | `Draw Overlays → GRANTED` · `Shizuku Service → READY` |
| Actions | `▶ START OVERLAY` (solid red) · `■ STOP` (outline) |
| Click Config | `Target Driver Application` dropdown → `Rapido Captain` |
| Nav | Plans · Login · **Dashboard (active)** · Filter · History · Profile |

### 2.2 Ride Filters (Screenshot 2)
| Filter | Toggle | Controls | Notes |
|--------|--------|----------|-------|
| Fare Value Filter | ON | Min ₹ `60`, Max ₹ `1000`, `SAVE FARE RANGE` | Only filter actually ON |
| Distance (KM) Filter | OFF | — | Trip distance filter |
| Driver Zone Filter | OFF | `+ Add Location` (red button) | Empty → "All locations accepted when empty" |
| No Zone Filter | OFF | `+ Add Blocked Location`; list item `seven wells` (edit ✎ / delete 🗑) | OFF aanalum data save aagiruku |

### 2.3 History (Screenshot 3)
| Element | Detail |
|---------|--------|
| Total Earnings card | `₹589` · `6 rides auto-accepted` · clear/trash icon (top-right) |
| Accepted Ride List | Card: `Rapido Captain` badge, timestamp (`15 Aug, 05:51 pm`), fare `₹100`, distance `1.0 km + 3.2 km` (= pickup + trip) |
| Ride card body | `● PICKUP • 1.0 km` → address · `■ DROPOFF • 3.2 km` → address |
| Sample rides | ₹100 (Sembakkam→Rajakilpakkam), ₹125 (Rajakilpakkam→Selaiyur 6.3 km), ₹60 (Selaiyur, 0.8 km) |
| Parser artifact | Drop address end-la "Reject" text kalanthu varudhu — screen scrape raw-a save panradhala |

### 2.4–2.6 Plans / Login / Profile (Not in screenshots)
APK layouts + runtime-la (Phase 2/5) confirm pannanum: pricing tiers (`1_day` pattern),
login identifier (User ID `OLA949E169` auto-generated-a / phone?), profile fields.

## 3. Inferred System Behaviour
```
state: IDLE ──START OVERLAY──▶ RUNNING (overlay + accessibility listening)
       ◀──────── STOP ────────┘     └─ plan expired ─▶ LOCKED
SYSTEM STATUS checks: Accessibility ON? · Overlay permission? · Shizuku running/binder?
PLAN: activation timestamp + duration (1_day) → live countdown → expiry = engine disabled
FILTERS: fare ∈ [min,max]; zone allow-list (empty=all); block-list (contains → skip)
```

## 4. Design Tokens (for new branding — values approx. from screenshots)
- Background `#0A0A0F`, Card `#14141C`, Border `#2A2A35`, Accent Red `#FF0A3C`, Success Green `#22C55E`,
  Text `#FFFFFF / #9CA3AF` (muted), Card radius ~16–20dp, countdown font = bold monospace-ish 32sp+

## 5. Open Questions (Analysis phases-la answer pannanum)
1. Package name / version / SDK levels? (Phase 1–2)
2. Target apps evlo? Rapido Captain thavira Ola/Uber drop-down-la iruka? (Phase 2/5)
3. Plan verify online-a, illa local time-a? Payment epdi? (Phase 6)
4. "Multi App / Simultaneous" feature screenshot keela partial-a theriyudhu — confirm pannanum.
5. History export/share iruka? Earnings reset manual-a? (Phase 4–5)
