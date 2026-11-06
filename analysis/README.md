# RE Lab Runbook — Ride Accepter Pro Max Analysis

Unga **own local machine**-la run panna commands. APK indha sandbox-ku direct-a vara mudiyala
(Drive download blocked), ellame inga dhaan nadakanum illa APK-ai `original/`-la vechu next session-la continue pannalam.

## 0. Folder Setup
```bash
mkdir -p analysis/original analysis/decompiled analysis/reports
# Drive-la irundhu download panna APK-ai inga copy pannunga:
#   analysis/original/rideaccepter-pro-max_v1.apk
#   analysis/original/rideraccepter_old.apk
```

## 1. Install Tools
```bash
# Ubuntu/Debian
sudo apt install -y openjdk-17-jdk aapt apktool adb unzip
pip install androguard apkid frida-tools objection apkleaks
# jadx (GitHub release: skylot/jadx)
wget https://github.com/skylot/jadx/releases/download/v1.5.1/jadx-1.5.1.zip && unzip jadx-1.5.1.zip -d ~/jadx
# MobSF (Docker — MobSF/Mobile-Security-Framework-MobSF)
docker run -it --rm -p 8000:8000 opensecurity/mobile-security-framework-mobsf:latest
```

## 2. Phase 1 — Fingerprint (indha repo script)
```bash
sha256sum analysis/original/*.apk
python3 analysis/scripts/apk_fingerprint.py analysis/original/rideaccepter-pro-max_v1.apk \
  --json analysis/reports/fingerprint.json --md analysis/reports/fingerprint.md
apkid analysis/original/rideaccepter-pro-max_v1.apk
aapt dump badging analysis/original/rideaccepter-pro-max_v1.apk | head -20
apksigner verify --print-certs analysis/original/rideaccepter-pro-max_v1.apk
```

## 3. Phase 2–3 — Decompile & Static
```bash
apktool d analysis/original/rideaccepter-pro-max_v1.apk -o analysis/decompiled/apktool_pro_max
~/jadx/bin/jadx-gui analysis/original/rideaccepter-pro-max_v1.apk    # GUI-la explore
~/jadx/bin/jadx -d analysis/decompiled/jadx_src analysis/original/rideaccepter-pro-max_v1.apk
apkleaks -f analysis/original/rideaccepter-pro-max_v1.apk -o analysis/reports/apkleaks.txt
# MobSF: browser-la http://127.0.0.1:8000 → APK upload → report save
cat analysis/decompiled/apktool_pro_max/AndroidManifest.xml
```

## 4. Phase 5 — Dynamic (Own test device)
```bash
adb install analysis/original/rideaccepter-pro-max_v1.apk
adb logcat | grep -i -E "ride|accepter|accessib"   # package name confirm aanaprom tag maarum
adb shell dumpsys accessibility                    # service register aana?
adb shell settings get secure enabled_accessibility_services
# Screenrecord: Dashboard → Filters set → Start Overlay → Stop (full flow)
```

## 5. Report Writing
Ovvoru phase mudichalum: `templates/ANALYSIS_REPORT_TEMPLATE.md` copy panni
`reports/NN-phase-name.md` a fill pannunga. Secrets (API keys etc.) report-la **redact** pannunga.

## ⚠️ Rules
- `original/*.apk` + `decompiled/` — **Git-la commit pannaadha** (`.gitignore` already blocks).
- Original code/assets pudhu app-ku copy pannaadha — behaviour/spec mattum.
- Real driver account-la test pannaadha; test device/test account mattum.
