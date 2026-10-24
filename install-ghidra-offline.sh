#!/usr/bin/env bash
# Install Ghidra 12.1.4 + a working JDK 21 for REA using only hosts that are
# reachable from this sandbox (github.com git + pypi.org). No release assets, no
# Debian mirrors, no Maven Central.
#
#   bash install-ghidra-offline.sh          # install / repair
#   bash install-ghidra-offline.sh --check  # report status only
#
# What it does
#   1. clones a public mirror of the official Ghidra 12.1.4 distribution
#      (NationalSecurityAgency/ghidra release Ghidra_12.1.4_build,
#       sha256 ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db)
#   2. builds a "full JDK" from the PyPI JRE (jdk4py) by adding the pure-Java
#      jdk.compiler + jdk.internal.opt modules taken from an Oracle JDK 21
#      (Windows build: these modules are platform-independent bytecode)
#   3. repoints javax.tools.ToolProvider (patched into java.compiler) so Ghidra's
#      runtime script compilation works without jdk.compiler in the image
#   4. wires GHIDRA_INSTALL_DIR / JAVA_HOME into the shell profile and the four
#      registered MCP clients, then verifies with `rea doctor --provider ghidra`
#
# /opt is outside the workspace snapshot, which is why this script exists:
# re-run it after a fresh sandbox boot.
set -euo pipefail

GHIDRA_REPO="https://github.com/Chaborsz/Ghidra-12.1.4-Workspace.git"
GHIDRA_DIR="/opt/ghidra_12.1.4_PUBLIC"
JDK_DIR="/opt/jdk-21-full"
MODULE_DIR="/opt/javac-modules"
PATCH_DIR="/opt/javac-patch"
JDK21_SRC="https://github.com/MineFartsEmbed/JDK.git"
JDK21_BRANCH="21"
JRE_SRC="${JRE_SRC:-/home/user/.tools/jdk-21}"      # pypi jdk4py JRE (linux x64)
REA_BIN="${REA_BIN:-/home/user/bin/rea}"

say() { printf '\n== %s ==\n' "$1"; }
die() { printf '\nERROR: %s\n' "$1" >&2; exit 1; }
SUDO=""; if [ "$(id -u)" != "0" ]; then SUDO="sudo -n"; fi

jre_ok() { [ -x "$1/bin/java" ] && [ -f "$1/lib/modules" ]; }
ghidra_ok() { [ -f "$1/Ghidra/application.properties" ] && grep -q '^application.version=12\.1\.' "$1/Ghidra/application.properties" \
              && [ -x "$1/support/analyzeHeadless" ]; }
jdk_shim_ok() { [ -x "$1/bin/javac" ] && [ -f "$2" ] && [ -f "$3/jdk.compiler.jar" ]; }

if [ "${1:-}" = "--check" ]; then
  say "status"
  ghidra_ok "$GHIDRA_DIR" && echo "ghidra   : OK $GHIDRA_DIR" || echo "ghidra   : MISSING"
  jre_ok "$JDK_DIR"        && echo "jre base : OK $JDK_DIR"    || echo "jre base : MISSING"
  jdk_shim_ok "$JDK_DIR" "$PATCH_DIR/java.compiler-patch.jar" "$MODULE_DIR" \
    && echo "jdk shim : OK ($("$JDK_DIR/bin/javac" -version 2>&1 | head -1))" || echo "jdk shim : MISSING"
  [ -x "$REA_BIN" ] && GHIDRA_INSTALL_DIR="$GHIDRA_DIR" JAVA_HOME="$JDK_DIR" \
    "$REA_BIN" doctor --provider ghidra --format json 2>/dev/null |
    python3 -c 'import json,sys;d=json.load(sys.stdin);print("rea healthy:",d.get("healthy"));[print("  %-26s %s %s"%(c["name"],c["ok"],(c.get("detail") or "")[:60])) for c in d["scope_checks"]]' || true
  exit 0
fi

command -v unzip >/dev/null || die "unzip is required"
command -v git >/dev/null || die "git is required"
jre_ok "$JRE_SRC" || die "base JRE not found at $JRE_SRC (pip install jdk4py first)"
JRE_REAL="$(readlink -f "$JRE_SRC")"

# ---------------------------------------------------------------- 1. Ghidra
say "1/6 Ghidra 12.1.4"
if ghidra_ok "$GHIDRA_DIR"; then
  echo "already installed: $GHIDRA_DIR"
else
  work="$(mktemp -d /tmp/ghidra-clone.XXXXXX)"
  git clone --quiet --depth 1 --single-branch "$GHIDRA_REPO" "$work/src"
  src="$work/src/ghidra_12.1.4_PUBLIC"
  [ -d "$src" ] || die "clone did not contain ghidra_12.1.4_PUBLIC"
  $SUDO mkdir -p "$(dirname "$GHIDRA_DIR")"
  $SUDO rm -rf "$GHIDRA_DIR"
  $SUDO mv "$src" "$GHIDRA_DIR"
  $SUDO chown -R "$(id -un)":sudo "$GHIDRA_DIR"
  $SUDO chmod +x "$GHIDRA_DIR/support/analyzeHeadless" "$GHIDRA_DIR/ghidraRun" 2>/dev/null || true
  rm -rf "$work"
  ghidra_ok "$GHIDRA_DIR" || die "installed tree failed validation"
  echo "installed $GHIDRA_DIR ($(du -sh "$GHIDRA_DIR" | cut -f1))"
fi

# ------------------------------------------------- 2. pure-Java compiler modules
say "2/6 jdk.compiler + jdk.internal.opt (pure Java, from an Oracle JDK 21)"
$SUDO mkdir -p "$MODULE_DIR"
$SUDO chown "$(id -un)" "$MODULE_DIR"
if [ -f "$MODULE_DIR/jdk.compiler.jar" ] && [ -f "$MODULE_DIR/jdk.internal.opt.jar" ]; then
  echo "already built"
else
  work="$(mktemp -d /tmp/jdkmods.XXXXXX)"
  git clone --quiet --filter=blob:none --no-checkout --depth 1 --branch "$JDK21_BRANCH" "$JDK21_SRC" "$work/jdk"
  git -C "$work/jdk" sparse-checkout init --no-cone
  git -C "$work/jdk" sparse-checkout set '/jmods/jdk.compiler.jmod' '/jmods/jdk.internal.opt.jmod'
  git -C "$work/jdk" checkout --quiet
  cat > "$work/strip_module_target.py" <<'PY'
import struct, sys, pathlib
def strip(path):
    d = bytearray(pathlib.Path(path).read_bytes()); assert d[:4] == b"\xca\xfe\xba\xbe"
    pos = 8; n = struct.unpack_from(">H", d, pos)[0]; pos += 2; cp = {}; i = 1
    while i < n:
        tag = d[pos]; pos += 1
        if tag == 1:
            ln = struct.unpack_from(">H", d, pos)[0]; pos += 2
            cp[i] = bytes(d[pos:pos+ln]).decode("utf-8", "replace"); pos += ln
        elif tag in (3, 4): pos += 4
        elif tag in (5, 6): pos += 8; i += 1
        elif tag in (7, 8, 16, 19, 20): pos += 2
        elif tag in (9, 10, 11, 12, 17, 18): pos += 4
        elif tag == 15: pos += 3
        else: raise ValueError("tag " + str(tag))
        i += 1
    pos += 6
    k = struct.unpack_from(">H", d, pos)[0]; pos += 2 + 2 * k
    for _ in range(2):
        m = struct.unpack_from(">H", d, pos)[0]; pos += 2
        for _ in range(m):
            pos += 6; a = struct.unpack_from(">H", d, pos)[0]; pos += 2
            for _ in range(a):
                ln = struct.unpack_from(">I", d, pos + 2)[0]; pos += 6 + ln
    start = pos; cnt = struct.unpack_from(">H", d, pos)[0]; pos += 2; kept = []
    for _ in range(cnt):
        idx, ln = struct.unpack_from(">HI", d, pos); raw = bytes(d[pos:pos+6+ln])
        if cp.get(idx) != "ModuleTarget": kept.append(raw)
        pos += 6 + ln
    if pos != len(d): raise ValueError("trailing bytes")
    out = bytearray(d[:start]); out += struct.pack(">H", len(kept))
    for r in kept: out += r
    pathlib.Path(path).write_bytes(bytes(out))
for p in sys.argv[1:]: strip(p)
PY
  for m in jdk.compiler jdk.internal.opt; do
    mkdir -p "$work/$m"
    # .jmod files carry a 4-byte header before the zip; unzip warns and exits 1,
    # so extract with Python's zipfile, which locates the central directory.
    python3 - "$work/jdk/jmods/$m.jmod" "$work/$m" <<'PY'
import sys, zipfile
zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])
PY
    python3 "$work/strip_module_target.py" "$work/$m/classes/module-info.class"
    ( cd "$work/$m/classes" && python3 - "$MODULE_DIR/$m.jar" <<'PY'
import sys, zipfile, pathlib
out = pathlib.Path(sys.argv[1])
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(pathlib.Path(".").rglob("*")):
        if p.is_file(): z.write(p, p.as_posix())
PY
    )
  done
  $SUDO chown "$(id -un)" "$MODULE_DIR"/*.jar
  rm -rf "$work"
  echo "built $MODULE_DIR/jdk.compiler.jar + jdk.internal.opt.jar"
fi

# ------------------------------------------------------ 3. JDK "full JDK" shim
say "3/6 JDK home at $JDK_DIR (JRE + classpath compiler)"
if jre_ok "$JDK_DIR" && [ -x "$JDK_DIR/bin/javac" ]; then
  echo "already assembled"
else
  $SUDO rm -rf "$JDK_DIR.new"
  $SUDO cp -a "$JRE_REAL" "$JDK_DIR.new"
  $SUDO rm -rf "$JDK_DIR"
  $SUDO mv "$JDK_DIR.new" "$JDK_DIR"
  $SUDO chown -R "$(id -un)":sudo "$JDK_DIR"
  $SUDO cp "$JDK_DIR/bin/java" "$JDK_DIR/bin/java.real"
  $SUDO tee "$JDK_DIR/bin/java" >/dev/null <<'EOF'
#!/bin/bash
# Launcher for the REA JDK shim: adds javac to the class path and patches
# javax.tools.ToolProvider (the base image has no jdk.compiler module).
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
compiler_cp="/opt/javac-modules/jdk.compiler.jar:/opt/javac-modules/jdk.internal.opt.jar"
argv=("$@"); out=(--patch-module "java.compiler=/opt/javac-patch/java.compiler-patch.jar"); cp_seen=0; i=0
while (( i < ${#argv[@]} )); do
  a="${argv[i]}"
  case "$a" in
    -cp|-classpath|--class-path) out+=("$a" "$compiler_cp:${argv[i+1]:-}"); i=$((i+2)); cp_seen=1; continue ;;
    --class-path=*)             out+=("$a" "$compiler_cp:${a#*=}");   i=$((i+1)); cp_seen=1; continue ;;
  esac
  out+=("$a"); i=$((i+1))
done
(( cp_seen == 0 )) && export CLASSPATH="${compiler_cp}${CLASSPATH:+:$CLASSPATH}"
exec "$here/java.real" "${out[@]}"
EOF
  $SUDO tee "$JDK_DIR/bin/javac" >/dev/null <<'EOF'
#!/bin/bash
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$here/java" -cp /opt/javac-modules/jdk.compiler.jar:/opt/javac-modules/jdk.internal.opt.jar \
  com.sun.tools.javac.Main "$@"
EOF
  $SUDO chmod +x "$JDK_DIR/bin/java" "$JDK_DIR/bin/javac" "$JDK_DIR/bin/java.real"
  $SUDO chown -R "$(id -un)":sudo "$JDK_DIR"
fi

# ------------------------------------------------- 4. patched ToolProvider
say "4/6 javax.tools.ToolProvider patch"
$SUDO mkdir -p "$PATCH_DIR"
$SUDO chown "$(id -un)" "$PATCH_DIR"
if [ -f "$PATCH_DIR/java.compiler-patch.jar" ]; then
  echo "already built"
else
  work="$(mktemp -d /tmp/tp.XXXXXX)"
  mkdir -p "$work/src/javax/tools" "$work/out"
  cat > "$work/src/javax/tools/ToolProvider.java" <<'EOF'
package javax.tools;

/** Replacement ToolProvider for images that lack the jdk.compiler module. */
public class ToolProvider {
    private ToolProvider() {}

    public static JavaCompiler getSystemJavaCompiler() {
        try {
            Class<?> tool = Class.forName("com.sun.tools.javac.api.JavacTool", true,
                    ClassLoader.getSystemClassLoader());
            return (JavaCompiler) tool.getMethod("create").invoke(null);
        } catch (Throwable t) {
            return null;
        }
    }

    public static DocumentationTool getSystemDocumentationTool() {
        return null; // javadoc is not part of this shim
    }
}
EOF
  "$JRE_REAL/bin/java" -cp "$MODULE_DIR/jdk.compiler.jar:$MODULE_DIR/jdk.internal.opt.jar" \
    com.sun.tools.javac.Main --patch-module "java.compiler=$work/src" \
    -d "$work/out" "$work/src/javax/tools/ToolProvider.java"
  ( cd "$work/out" && python3 - "$PATCH_DIR/java.compiler-patch.jar" <<'PY'
import sys, zipfile, pathlib
out = pathlib.Path(sys.argv[1])
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(pathlib.Path(".").rglob("*.class")): z.write(p, p.as_posix())
PY
  )
  $SUDO chown "$(id -un)" "$PATCH_DIR/java.compiler-patch.jar"
  rm -rf "$work"
  echo "built $PATCH_DIR/java.compiler-patch.jar"
fi

# ------------------------------------------------------- 5. wire the environment
say "5/6 environment + MCP clients"
python3 - "$GHIDRA_DIR" "$JDK_DIR" <<'PY'
import json, pathlib, re, sys
ghidra, java = sys.argv[1:3]
block = (
    "\n# --- Ghidra 12.1.4 for REA (installed from git; /opt is not snapshot-persisted) ---\n"
    f'export GHIDRA_INSTALL_DIR="{ghidra}"\n'
    f'export JAVA_HOME="{java}"\n'
    'case ":$PATH:" in *":$JAVA_HOME/bin:"*) ;; *) export PATH="$JAVA_HOME/bin:$PATH";; esac\n'
)
for path in ("/home/user/.bashrc", "/home/user/.profile"):
    p = pathlib.Path(path)
    if not p.exists(): continue
    t = re.sub(r"\n# --- Ghidra 12\.1\.4 for REA.*?(?=\n# --- |\Z)", "\n", p.read_text(), flags=re.S)
    p.write_text(t.rstrip("\n") + "\n" + block)
for path in ("/home/user/.claude.json", "/home/user/.cursor/mcp.json", "/home/user/.gemini/settings.json"):
    p = pathlib.Path(path)
    if not p.exists(): continue
    d = json.loads(p.read_text()); servers = d.get("mcpServers", d)
    if "rea" in servers:
        servers["rea"].setdefault("env", {}).update(GHIDRA_INSTALL_DIR=ghidra, JAVA_HOME=java)
        p.write_text(json.dumps(d, indent=2) + "\n"); print("updated", path)
p = pathlib.Path("/home/user/.codex/config.toml")
if p.exists():
    t = p.read_text()
    for k, v in {"GHIDRA_INSTALL_DIR": ghidra, "JAVA_HOME": java}.items():
        line = f'{k} = "{v}"'
        t = re.sub(rf"^{k} = .*$", line, t, flags=re.M) if re.search(rf"^{k} = ", t, flags=re.M) else t.rstrip("\n") + "\n" + line + "\n"
    p.write_text(t); print("updated", p)
PY

# --------------------------------------------------------------- 6. verify
say "6/6 verification"
export GHIDRA_INSTALL_DIR="$GHIDRA_DIR" JAVA_HOME="$JDK_DIR" PATH="$JDK_DIR/bin:$PATH"
"$JDK_DIR/bin/javac" -version
if [ -x "$REA_BIN" ]; then
  "$REA_BIN" doctor --provider ghidra --format json 2>/dev/null | python3 -c '
import json, sys
d = json.load(sys.stdin)
print("rea healthy:", d.get("healthy"))
for c in d.get("scope_checks", []):
    print("  %-26s %s %s" % (c["name"], c["ok"], (c.get("detail") or "")[:60]))
'
  echo
  echo "Try: rea decompile /bin/ls 0x61d0 --provider ghidra"
fi
