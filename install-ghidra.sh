#!/usr/bin/env bash
# Install Ghidra 12.1.x + a full JDK 21 for REA, then wire it into the CLI and
# the registered MCP clients.
#
#   bash install-ghidra.sh                  # download official Ghidra 12.1.4 + Temurin JDK 21
#   bash install-ghidra.sh --ghidra-zip ~/ghidra_12.1.4_PUBLIC_20260921.zip
#   bash install-ghidra.sh --ghidra-zip X.zip --jdk /path/to/jdk-21
#   bash install-ghidra.sh --check          # report status, change nothing
#
# REA's requirements (docs/installation.md "Ghidra"):
#   * Ghidra 12.1.x
#   * 64-bit *full* JDK 21+ (must contain javac) for the same host platform
#   * native decompiler at Ghidra/Features/Decompiler/os/linux_x86_64/decompile
#   * env: GHIDRA_INSTALL_DIR + JAVA_HOME
set -euo pipefail

TOOLS="${TOOLS:-/home/user/.tools}"
GHIDRA_VERSION="12.1.4"
GHIDRA_ZIP_NAME="ghidra_12.1.4_PUBLIC_20260921.zip"
GHIDRA_URL="https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_12.1.4_build/${GHIDRA_ZIP_NAME}"
JDK_URL="https://api.adoptium.net/v3/binary/latest/21/ga/linux/x64/jdk/hotspot/normal/eclipse"
GHIDRA_HOME="${GHIDRA_HOME:-$TOOLS/ghidra_${GHIDRA_VERSION}_PUBLIC}"
REA_BIN="${REA_BIN:-/home/user/bin/rea}"
CLIENTS=(claude_code codex cursor gemini_cli)
CLIENT_CONFIGS=(
  "/home/user/.claude.json"
  "/home/user/.codex/config.toml"
  "/home/user/.cursor/mcp.json"
  "/home/user/.gemini/settings.json"
)

ghidra_zip=""
jdk_arg=""
check_only=false
wire=true

usage() { sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; }

while (($#)); do
  case "$1" in
    --ghidra-zip) ghidra_zip="${2:?--ghidra-zip needs a path}"; shift 2 ;;
    --jdk)        jdk_arg="${2:?--jdk needs a directory or .tar.gz}"; shift 2 ;;
    --check)      check_only=true; shift ;;
    --no-wire)    wire=false; shift ;;
    -h|--help)    usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

say()  { printf '\n== %s ==\n' "$1"; }
warn() { printf 'WARN: %s\n' "$1" >&2; }
die()  { printf '\nERROR: %s\n' "$1" >&2; exit 1; }

# ---------------------------------------------------------------- discovery
find_local_zip() {
  local d
  for d in "$PWD" /home/user /home/user/vjk_18 /home/user/Downloads /tmp; do
    [ -d "$d" ] || continue
    local f
    f="$(find "$d" -maxdepth 2 -name 'ghidra_*_PUBLIC_*.zip' -type f 2>/dev/null | head -1)"
    if [ -n "$f" ]; then printf '%s\n' "$f"; return 0; fi
  done
  return 1
}

# A JDK usable by Ghidra: bin/javac + 64-bit + major >= 21.
check_jdk() {
  local home="$1"
  [ -n "$home" ] && [ -x "$home/bin/javac" ] || return 1
  local ver major
  ver="$("$home/bin/javac" -version 2>&1 | head -1)"
  major="$(printf '%s' "$ver" | sed -n 's/.*javac[[:space:]]\{1,\}\([0-9][0-9]*\).*/\1/p')"
  [ -n "$major" ] || return 1
  [ "$major" -ge 21 ] 2>/dev/null || return 1
  local props
  props="$("$home/bin/java" -XshowSettings:properties -version 2>&1 | tr -d '\r')"
  printf '%s' "$props" | grep -q 'sun.arch.data.model = 64' || return 1
  printf '%s' "$props" | grep -Eq 'os.arch = (amd64|x86_64)' || return 1
  # A JRE (e.g. the PyPI jdk4py runtime) has no compiler module; Ghidra needs a
  # full JDK, and REA's doctor reports a runtime-only JDK as config_drift.
  "$home/bin/java" --list-modules 2>/dev/null | grep -q '^jdk\.compiler@' || return 1
  printf '%s\n' "$home"
}

find_jdk() {
  local c
  for c in "$jdk_arg" "${JAVA_HOME:-}" "$TOOLS/jdk-21-full" "$TOOLS/jdk-21" /usr/lib/jvm/*; do
    [ -n "$c" ] || continue
    [ -e "$c" ] || continue
    check_jdk "$c" 2>/dev/null && return 0
  done
  return 1
}

# A Ghidra tree usable by REA.
check_ghidra() {
  local home="$1"
  [ -f "$home/Ghidra/application.properties" ] || return 1
  grep -q "^application.version=12\.1\." "$home/Ghidra/application.properties" || return 1
  local dec="$home/Ghidra/Features/Decompiler/os/linux_x86_64/decompile"
  if [ -f "$dec" ] && [ -x "$dec" ]; then return 0; fi
  for alt in "$home/Ghidra/Features/Decompiler/build/os/linux_x86_64/decompile"; do
    [ -x "$alt" ] && return 0
  done
  return 1
}

# ---------------------------------------------------------------- reporting
if [ "$check_only" = true ]; then
  say "Ghidra status"
  if check_ghidra "$GHIDRA_HOME" 2>/dev/null; then
    echo "ghidra      : OK  $GHIDRA_HOME  ($(grep '^application.version=' "$GHIDRA_HOME/Ghidra/application.properties" | cut -d= -f2))"
  else
    echo "ghidra      : MISSING  (expected at $GHIDRA_HOME)"
  fi
  if jdk="$(find_jdk 2>/dev/null)"; then
    echo "jdk         : OK  $jdk  ($("$jdk/bin/javac" -version 2>&1 | head -1))"
  else
    echo "jdk         : MISSING a full 64-bit JDK 21+ with javac"
  fi
  echo "GHIDRA_INSTALL_DIR env : ${GHIDRA_INSTALL_DIR:-<unset>}"
  echo "JAVA_HOME env          : ${JAVA_HOME:-<unset>}"
  if [ -x "$REA_BIN" ]; then
    echo
    "$REA_BIN" doctor --provider ghidra --format json 2>/dev/null |
      tr ',' '\n' | grep -E '"(name|ok|classification|detail|remediation)"' | head -12
  fi
  exit 0
fi

# ---------------------------------------------------------------- JDK
say "1/4 full JDK 21 with javac"
if jdk="$(find_jdk 2>/dev/null)"; then
  echo "using $jdk  ($("$jdk/bin/javac" -version 2>&1 | head -1))"
elif [ -n "$jdk_arg" ] && [ -f "$jdk_arg" ]; then
  echo "extracting $jdk_arg"
  mkdir -p "$TOOLS/jdk-unpack"
  tar xzf "$jdk_arg" -C "$TOOLS/jdk-unpack"
  top="$(find "$TOOLS/jdk-unpack" -maxdepth 1 -mindepth 1 -type d | head -1)"
  [ -n "$top" ] || die "could not find the extracted JDK directory"
  rm -rf "$TOOLS/jdk-21-full" && mv "$top" "$TOOLS/jdk-21-full"
  jdk="$(check_jdk "$TOOLS/jdk-21-full")" || die "the supplied JDK is not a full 64-bit JDK 21+ (bin/javac missing or wrong version)"
  echo "installed $jdk"
else
  echo "downloading Temurin JDK 21 from api.adoptium.net ..."
  if curl -fsSL --retry 2 --max-time 900 -o /tmp/temurin21.tar.gz "$JDK_URL"; then
    mkdir -p "$TOOLS/jdk-unpack" && tar xzf /tmp/temurin21.tar.gz -C "$TOOLS/jdk-unpack"
    top="$(find "$TOOLS/jdk-unpack" -maxdepth 1 -mindepth 1 -type d | head -1)"
    rm -rf "$TOOLS/jdk-21-full" && mv "$top" "$TOOLS/jdk-21-full"
    rm -rf "$TOOLS/jdk-unpack"
    jdk="$(check_jdk "$TOOLS/jdk-21-full")" || die "downloaded JDK failed validation"
    echo "installed $jdk"
  else
    die "cannot download the JDK (api.adoptium.net unreachable from this sandbox).
Pass a JDK explicitly:
  bash install-ghidra.sh --jdk /path/to/jdk-21.tar.gz
Note: the JDK bundled here (\$TOOLS/jdk-21, from PyPI jdk4py) is JRE-only — Ghidra
needs javac, so it cannot satisfy this requirement."
  fi
fi

# ---------------------------------------------------------------- Ghidra
say "2/4 Ghidra $GHIDRA_VERSION"
if check_ghidra "$GHIDRA_HOME" 2>/dev/null; then
  echo "already installed at $GHIDRA_HOME"
else
  if [ -z "$ghidra_zip" ]; then ghidra_zip="$(find_local_zip 2>/dev/null || true)"; fi
  if [ -z "$ghidra_zip" ]; then
    echo "downloading $GHIDRA_URL ..."
    if ! curl -fSL --retry 2 --max-time 1800 -o "/tmp/$GHIDRA_ZIP_NAME" "$GHIDRA_URL"; then
      die "cannot download Ghidra (release-assets.githubusercontent.com is blocked here).
Download ghidra_${GHIDRA_VERSION}_PUBLIC_*.zip on a networked machine, then either:
  1) upload it into this workspace and run:
       bash install-ghidra.sh --ghidra-zip /home/user/<file>.zip
  2) or allowlist release-assets.githubusercontent.com and api.adoptium.net, then rerun this script."
    fi
    ghidra_zip="/tmp/$GHIDRA_ZIP_NAME"
  fi
  [ -f "$ghidra_zip" ] || die "no such zip: $ghidra_zip"
  echo "extracting $ghidra_zip"
  mkdir -p "$TOOLS/ghidra-unpack"
  unzip -q -o "$ghidra_zip" -d "$TOOLS/ghidra-unpack"
  top="$(find "$TOOLS/ghidra-unpack" -maxdepth 1 -mindepth 1 -type d | head -1)"
  [ -n "$top" ] || die "zip contained no top-level Ghidra directory"
  rm -rf "$GHIDRA_HOME" && mv "$top" "$GHIDRA_HOME"
  rmdir "$TOOLS/ghidra-unpack" 2>/dev/null || rm -rf "$TOOLS/ghidra-unpack"
  check_ghidra "$GHIDRA_HOME" || die "extracted tree failed validation: $GHIDRA_HOME
Expected Ghidra/application.properties with application.version=12.1.x and
Ghidra/Features/Decompiler/os/linux_x86_64/decompile.
On Linux ARM64 the official archive omits that prebuilt decompiler; build it
first (see docs/installation.md, 'Ghidra') or REA will refuse the provider."
  echo "installed $GHIDRA_HOME"
fi

# ---------------------------------------------------------------- wiring
say "3/4 environment + MCP clients"
if [ "$wire" = true ]; then
  python3 - "$TOOLS" "$GHIDRA_HOME" "$jdk" <<'PY'
import json, pathlib, re, sys
tools, ghidra_home, jdk = sys.argv[1:4]
exports = {
    "GHIDRA_INSTALL_DIR": ghidra_home,
    "JAVA_HOME": jdk,
}
block = (
    "\n# --- Ghidra (installed by install-ghidra.sh) ---\n"
    f'export GHIDRA_INSTALL_DIR="{ghidra_home}"\n'
    f'export JAVA_HOME="{jdk}"\n'
    'case ":$PATH:" in *":$JAVA_HOME/bin:"*) ;; *) export PATH="$JAVA_HOME/bin:$PATH";; esac\n'
)
for path in ("/home/user/.bashrc", "/home/user/.profile"):
    p = pathlib.Path(path)
    if not p.exists():
        continue
    text = re.sub(r"\n# --- Ghidra \(installed by install-ghidra\.sh\) ---.*?(?=\n# --- |\Z)", "", p.read_text(), flags=re.S)
    p.write_text(text.rstrip("\n") + "\n" + block)

for path in ("/home/user/.claude.json", "/home/user/.cursor/mcp.json", "/home/user/.gemini/settings.json"):
    p = pathlib.Path(path)
    if not p.exists():
        continue
    data = json.loads(p.read_text())
    servers = data.get("mcpServers", data) if isinstance(data, dict) else {}
    if "rea" in servers:
        servers["rea"].setdefault("env", {}).update(exports)
        p.write_text(json.dumps(data, indent=2) + "\n")
        print("updated", path)

p = pathlib.Path("/home/user/.codex/config.toml")
if p.exists():
    text = p.read_text()
    for key, value in exports.items():
        line = f'{key} = "{value}"'
        if re.search(rf"^{key} = .*$", text, flags=re.M):
            text = re.sub(rf"^{key} = .*$", line, text, flags=re.M)
        else:
            text = text.rstrip("\n") + "\n" + line + "\n"
    p.write_text(text)
    print("updated", p)
PY
  echo "wired GHIDRA_INSTALL_DIR + JAVA_HOME into the shell profile and 4 MCP clients"
else
  echo "skipped (--no-wire)"
fi

# ---------------------------------------------------------------- verify
say "4/4 REA readiness"
export GHIDRA_INSTALL_DIR="$GHIDRA_HOME" JAVA_HOME="$jdk" PATH="$jdk/bin:$PATH"
if [ -x "$REA_BIN" ]; then
  "$REA_BIN" doctor --provider ghidra --format json 2>/dev/null | python3 -c '
import json, sys
d = json.load(sys.stdin)
print("healthy:", d.get("healthy"))
for c in d.get("scope_checks", []):
    print("  %-16s ok=%s %s %s" % (
        c.get("name", ""), c.get("ok"),
        c.get("classification", "") or "", (c.get("detail") or "")[:90]))
' || true
  echo
  echo "Quick smoke test:"
  echo "  rea open-binary /bin/ls --provider ghidra --format json | head -c 400"
  echo "  rea decompile /bin/ls --procedure main"
else
  echo "set for this shell only; $REA_BIN not found"
fi
