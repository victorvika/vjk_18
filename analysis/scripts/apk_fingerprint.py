#!/usr/bin/env python3
"""
APK Fingerprint — Phase 1/2 of the RideAccepter Pro Max RE roadmap.
Stdlib-only (optional: androguard for manifest details). Does NOT decompile
or modify the APK; read-only first-pass triage.

Usage:
    python3 apk_fingerprint.py /path/to/rideaccepter-pro-max.apk
    python3 apk_fingerprint.py app.apk --json report.json --md report.md

What it answers (before jadx/apktool):
  * Exact size + SHA-256 / MD5 (prove the two Drive copies are identical)
  * Tech stack: Native Kotlin/Java vs Flutter vs React Native vs Xamarin/Unity
  * DEX count, native .so libraries per ABI, signing cert files
  * If androguard is installed: package, version, permissions, components
"""
import argparse, hashlib, json, re, sys, zipfile
from collections import Counter, defaultdict
from pathlib import Path

def hashes(p: Path):
    h256, hmd5 = hashlib.sha256(), hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h256.update(chunk); hmd5.update(chunk)
    return h256.hexdigest(), hmd5.hexdigest()

def detect_stack(names):
    n = set(names)
    sig = {
        "Flutter":      any("libflutter.so" in x or x.startswith("assets/flutter_assets/") for x in n),
        "React Native": any(x.endswith("index.android.bundle") for x in n) or any("libhermes" in x for x in n),
        "Xamarin/.NET": any("libmonodroid" in x or "assemblies/" in x for x in n),
        "Unity":        any("libunity.so" in x or "assets/bin/Data/" in x for x in n),
        "Kotlin":       any(x.startswith("kotlin/") or x == "kotlin-tooling-metadata.json" for x in n),
        "Compose":      any("androidx/compose" in x for x in n),
    }
    primary = next((k for k in ("Flutter","React Native","Xamarin/.NET","Unity") if sig[k]), "Native Android (Java/Kotlin)")
    return primary, {k: v for k, v in sig.items() if v}

def printable_strings(data: bytes, min_len=4):
    return re.findall(rb"[ -~]{%d,}" % min_len, data)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("apk")
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--md", dest="md_out")
    a = ap.parse_args()
    apk = Path(a.apk)
    if not apk.is_file():
        sys.exit(f"APK not found: {apk}")
    if not zipfile.is_zipfile(apk):
        sys.exit("Not a valid APK/ZIP file")

    sha256, md5 = hashes(apk)
    with zipfile.ZipFile(apk) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        dex = sorted(x for x in names if re.fullmatch(r"classes\d*\.dex", x))
        libs = defaultdict(list)
        for x in names:
            m = re.fullmatch(r"lib/([^/]+)/(.+\.so)", x)
            if m: libs[m.group(1)].append(m.group(2))
        certs = [x for x in names if x.startswith("META-INF/") and x.rsplit(".",1)[-1].upper() in ("RSA","DSA","EC","SF")]
        assets = [x for x in names if x.startswith("assets/")][:50]
        primary, signals = detect_stack(names)
        top = Counter(x.split("/")[0] for x in names).most_common()
        manifest_strings = []
        if "AndroidManifest.xml" in names:
            raw = z.read("AndroidManifest.xml")
            # Binary AXML: printable strings still reveal package / service names
            manifest_strings = [t for t in (s.decode(errors="ignore") for s in printable_strings(raw, 5))
                                if "." in t and " " not in t][:60]

    report = {
        "file": str(apk), "size_bytes": apk.stat().st_size,
        "size_mb": round(apk.stat().st_size / 1048576, 2),
        "sha256": sha256, "md5": md5,
        "entry_count": len(names), "dex_files": dex,
        "primary_stack_guess": primary, "stack_signals": signals,
        "native_libs_by_abi": {k: sorted(v) for k, v in libs.items()},
        "signing_files": certs, "assets_sample": assets,
        "top_level_entries": top, "manifest_interesting_strings": manifest_strings,
    }

    # Optional deep manifest parse
    try:
        from androguard.misc import AnalyzeAPK  # type: ignore
        _a, _d, _dx = AnalyzeAPK(str(apk))
        report["androguard"] = {
            "package": _a.get_package(), "app_name": _a.get_app_name(),
            "version_name": _a.get_androidversion_name(),
            "version_code": _a.get_androidversion_code(),
            "min_sdk": _a.get_min_sdk_version(), "target_sdk": _a.get_target_sdk_version(),
            "permissions": sorted(_a.get_permissions()),
            "activities": sorted(_a.get_activities()),
            "services": sorted(_a.get_services()),
            "receivers": sorted(_a.get_receivers()),
            "providers": sorted(_a.get_providers()),
        }
    except ImportError:
        report["androguard"] = "not installed — `pip install androguard` for package/permissions/components"
    except Exception as e:  # noqa: BLE001
        report["androguard"] = f"failed: {e}"

    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)
    if a.json_out: Path(a.json_out).write_text(text, encoding="utf-8")
    if a.md_out:
        lines = [f"# APK Fingerprint — {apk.name}\n",
                 f"- Size: {report['size_mb']} MB ({report['size_bytes']} bytes)",
                 f"- SHA-256: `{sha256}`", f"- MD5: `{md5}`",
                 f"- Stack guess: **{primary}** {signals}",
                 f"- DEX: {dex}", f"- Native ABIs: {list(libs)}",
                 f"- Signing files: {certs}\n",
                 "## Next step\njadx-gui + apktool + MobSF (see ../README.md), then fill "
                 "`../templates/ANALYSIS_REPORT_TEMPLATE.md`."]
        Path(a.md_out).write_text("\n".join(lines), encoding="utf-8")

if __name__ == "__main__":
    main()
