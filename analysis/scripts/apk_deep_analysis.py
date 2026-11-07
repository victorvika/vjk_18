#!/usr/bin/env python3
"""
Deep (but jadx-free) APK analysis — Phase 2/3.
Produces reports/02-deep-analysis.json with:
  manifest (package/version/SDK/permissions/components/main activity)
  signing certificates, accessibility + network-security XML (decoded)
  resource string samples, DEX class inventory (app package tree)
  interesting DEX strings: URLs, target-app keywords, engine keywords
Run: /tmp/revenv/bin/python analysis/scripts/apk_deep_analysis.py <apk> <out.json>
"""
import json, re, sys, zipfile, collections
from pathlib import Path

APK_PATH, OUT = sys.argv[1], sys.argv[2]
from androguard.core.apk import APK
from androguard.core.axml import AXMLPrinter
from androguard.core.dex import DEX

a = APK(APK_PATH)
report = {
    "package": a.get_package(), "app_name": a.get_app_name(),
    "version_name": a.get_androidversion_name(), "version_code": a.get_androidversion_code(),
    "min_sdk": a.get_min_sdk_version(), "target_sdk": a.get_target_sdk_version(),
    "max_sdk": a.get_max_sdk_version(), "main_activity": a.get_main_activity(),
    "permissions": sorted(a.get_permissions()),
    "declared_permissions": sorted(a.get_declared_permissions() or []),
    "activities": sorted(a.get_activities()), "services": sorted(a.get_services()),
    "receivers": sorted(a.get_receivers()), "providers": sorted(a.get_providers()),
    "libraries": sorted(a.get_libraries()) if a.get_libraries() else [],
    "files": sorted(a.get_files()),
    "signatures": a.get_signatures(),
    "is_signed": a.is_signed(),
}

# ---- certificates ----
certs = []
try:
    for cert in a.get_certificates():
        certs.append({"subject": str(cert.subject.human_friendly) if hasattr(cert.subject, "human_friendly") else str(cert.subject),
                      "issuer": str(cert.issuer.human_friendly) if hasattr(cert.issuer, "human_friendly") else str(cert.issuer),
                      "serial": str(cert.serial_number),
                      "not_before": str(cert.not_valid_before_utc if hasattr(cert, "not_valid_before_utc") else cert.not_valid_before),
                      "not_after": str(cert.not_valid_after_utc if hasattr(cert, "not_valid_after_utc") else cert.not_valid_after),
                      "sha256_fp": cert.fingerprint(__import__("hashlib").sha256).hex() if hasattr(cert, "fingerprint") else None})
except Exception as e:
    certs = [f"cert parse failed: {e}"]
report["certificates"] = certs

# ---- interesting XML files (accessibility, network security, backup...) ----
xml_out = {}
with zipfile.ZipFile(APK_PATH) as z:
    for name in z.namelist():
        if name.startswith("res/xml/") or name in ("AndroidManifest.xml",):
            if name == "AndroidManifest.xml":
                continue
            try:
                xml_out[name] = AXMLPrinter(z.read(name)).get_buff().decode(errors="ignore")
            except Exception as e:
                xml_out[name] = f"<decode failed: {e}>"
report["xml_configs"] = xml_out

# ---- resource strings (sample, helps confirm UI text) ----
res_strings = []
try:
    arsc = a.get_android_resources()
    if arsc:
        pkg = a.get_package()
        # get all string resources for the app package
        for p in arsc.get_packages_names():
            try:
                strs = arsc.get_strings_resources(p)  # may not exist in all versions
            except Exception:
                strs = None
            if strs:
                res_strings.append(str(strs)[:2000])
except Exception as e:
    res_strings = [f"arsc failed: {e}"]
report["resource_strings_sample"] = res_strings[:5]

# ---- DEX: classes + strings ----
URL_RE = re.compile(r"https?://[^\s\"'<>\)\]]+")
KEYWORDS = ["rapido", "ola", "uber", "porter", "namma", "captain", "accept", "fare",
            "shizuku", "rikka", "accessib", "overlay", "dispatchgesture", "gesture",
            "plan", "expir", "subscription", "razorpay", "upi", "firebase", "supabase",
            "ktor", "okhttp", "api/", "/v1", "token", "license", "device", "click"]
pkg_path = "L" + (a.get_package() or "").replace(".", "/") + "/"
class_counter = collections.Counter()
app_classes, interesting_strings, urls = [], [], set()
per_dex = {}
with zipfile.ZipFile(APK_PATH) as z:
    dex_names = sorted(n for n in z.namelist() if re.fullmatch(r"classes\d*\.dex", n))

for dn in dex_names:
    with zipfile.ZipFile(APK_PATH) as z:
        raw = z.read(dn)
    d = DEX(raw)
    classes = [c.get_name() for c in d.get_classes()]
    strings = list(d.get_strings())
    per_dex[dn] = {"classes": len(classes), "strings": len(strings), "size": len(raw)}
    for c in classes:
        if c.startswith(pkg_path) or ("/" not in c[1:-1].replace("L", "", 1)[:1]):
            pass
    app_pkg_classes = [c for c in classes if c.startswith(pkg_path)]
    app_classes.extend(app_pkg_classes)
    for c in app_pkg_classes:
        parts = c[len(pkg_path):].split("/")
        class_counter[parts[0] if len(parts) > 1 else "(root)"] += 1
    for s in strings:
        low = s.lower()
        for u in URL_RE.findall(s):
            urls.add(u.rstrip(".,"))
        if any(k in low for k in KEYWORDS) and len(s) < 300:
            interesting_strings.append({"dex": dn, "s": s})
    print(f"  {dn}: {len(classes)} classes, {len(strings)} strings", flush=True)

report["dex"] = per_dex
report["app_class_count"] = len(app_classes)
report["app_package_top_level"] = class_counter.most_common(60)
report["app_classes_sample"] = sorted(set(app_classes))[:400]
report["urls_found"] = sorted(urls)[:200]
# de-dup interesting strings, cap output
seen, uniq = set(), []
for item in interesting_strings:
    if item["s"] not in seen:
        seen.add(item["s"]); uniq.append(item)
report["interesting_strings"] = uniq[:600]
report["interesting_strings_total"] = len(uniq)

Path(OUT).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nWROTE {OUT}")
print(f"package={report['package']} version={report['version_name']}({report['version_code']}) "
      f"sdk min={report['min_sdk']} target={report['target_sdk']} main={report['main_activity']}")
print(f"permissions={len(report['permissions'])} activities={len(report['activities'])} "
      f"services={len(report['services'])} receivers={len(report['receivers'])} providers={len(report['providers'])}")
print(f"app classes={len(app_classes)} urls={len(urls)} interesting strings={len(uniq)}")
