#!/usr/bin/env bash
# Reproducible install of morluto/rea (REA — Reverse Engineer Anything) in this sandbox.
#
# Constraints this script is written around:
#   * Only these hosts are reachable: github.com, codeload.github.com, api.github.com,
#     registry.npmjs.org, pypi.org, files.pythonhosted.org.
#   * GitHub *release assets* (release-assets.githubusercontent.com / objects.githubusercontent.com)
#     are NOT reachable, and apt/Debian mirrors are NOT reachable.
#   * Therefore Node.js comes from the npm `node` package, the JDK comes from PyPI `jdk4py`,
#     apktool comes from the npm `@postar/apktool-node` package, binwalk from a codeload tarball,
#     and libmagic from PyPI `pylibmagic`.
#   * Ghidra / JADX / IDA / Hopper / JEB / Kuna cannot be obtained here (see REA-SETUP.md).
#
# Usage: bash setup-rea.sh
set -euo pipefail

REA_DIR="${REA_DIR:-/home/user/rea}"
REA_REPO="${REA_REPO:-https://github.com/morluto/rea.git}"
TOOLS="${TOOLS:-/home/user/.tools}"
NODE_PREFIX="${NODE_PREFIX:-/home/user/.node24}"
VENV="${VENV:-/home/user/.venv-rea}"
NODE_VERSION=24.22.1   # matches rea/.nvmrc
NPM_VERSION=11.16.0    # matches rea/package.json#packageManager

log() { printf '\n== %s ==\n' "$1"; }

log "1/9 clone repository"
if [ ! -d "$REA_DIR/.git" ]; then
  git clone "$REA_REPO" "$REA_DIR"
else
  git -C "$REA_DIR" fetch --quiet origin && echo "already cloned: $REA_DIR"
fi

log "2/9 Node.js $NODE_VERSION + npm $NPM_VERSION (from the npm registry, not nodejs.org)"
mkdir -p "$NODE_PREFIX/bin"
if [ ! -x "$NODE_PREFIX/node_modules/node/bin/node" ]; then
  npm install --prefix "$NODE_PREFIX" "node@$NODE_VERSION" --no-audit --no-fund
fi
ln -sf "$NODE_PREFIX/node_modules/node/bin/node" "$NODE_PREFIX/bin/node"
if [ ! -d "$NODE_PREFIX/node_modules/npm" ]; then
  npm install --prefix "$NODE_PREFIX" "npm@$NPM_VERSION" --no-audit --no-fund
fi
# npm@11 ships as a JS CLI; expose it with a stable name next to our node.
ln -sf "$NODE_PREFIX/node_modules/npm/bin/npm-cli.js" "$NODE_PREFIX/bin/npm"
ln -sf "$NODE_PREFIX/node_modules/npm/bin/npx-cli.js" "$NODE_PREFIX/bin/npx"
chmod +x "$NODE_PREFIX"/node_modules/npm/bin/*.js || true
export PATH="$NODE_PREFIX/bin:$PATH"
echo "node $(node -v) / npm $(npm -v)"

log "3/9 project dependencies (npm ci)"
cd "$REA_DIR"
# esbuild's install scripts are blocked by npm's allow-scripts policy by default.
npm approve-scripts --allow-scripts-pending >/dev/null 2>&1 || true
npm ci --no-audit --no-fund
npm rebuild esbuild >/dev/null 2>&1 || true

log "4/9 git submodules (jadx-headless-mcp, binwalk, unblob, ghidra-nativeaot, wakaru)"
git submodule update --init --recursive --depth 1

log "5/9 build runtime + bundled skill"
npm run build:cached

log "6/9 Python tooling in $VENV"
if [ ! -x "$VENV/bin/python" ]; then python3 -m venv "$VENV"; fi
"$VENV/bin/pip" -q install --upgrade pip
# bcrypt is pinned: mitmproxy's passlib backend breaks on bcrypt>=4.1
"$VENV/bin/pip" -q install pwntools mitmproxy "bcrypt==4.0.1" unblob pylibmagic
# binwalk v3 (Rust, the git submodule) needs cargo, which is unavailable;
# binwalk v2 from a codeload tarball is pure Python and works on 3.11.
if [ ! -x "$VENV/bin/binwalk" ] || ! "$VENV/bin/binwalk --help" >/dev/null 2>&1; then
  curl -sL -o /tmp/binwalk-v2.tgz "https://codeload.github.com/ReFirmLabs/binwalk/tar.gz/refs/tags/v2.3.4"
  "$VENV/bin/pip" -q install /tmp/binwalk-v2.tgz
  "$VENV/bin/pip" -q install "capstone==5.0.6"   # binwalk v2 needs CS_ARCH_ARM64
fi

log "7/9 JDK 21 (jdk4py) + apktool 2.9.3 (npm @postar/apktool-node)"
"$VENV/bin/pip" -q install "jdk4py==21.0.8.2"
JDK_REAL="$("$VENV/bin/python" -c 'import jdk4py; print(jdk4py.JAVA_HOME)')"
mkdir -p "$TOOLS"
ln -sfn "$JDK_REAL" "$TOOLS/jdk-21"

mkdir -p "$TOOLS/apktool" "$TOOLS/bin" "$TOOLS/lib"
if [ ! -f "$TOOLS/apktool/apktool.jar" ]; then
  ( cd /tmp && npm pack @postar/apktool-node --silent >/dev/null
    rm -rf /tmp/apktool-pkg && mkdir -p /tmp/apktool-pkg
    tar xzf /tmp/postar-apktool-node-*.tgz -C /tmp/apktool-pkg --strip-components=1
    cp /tmp/apktool-pkg/lib/apktool.jar "$TOOLS/apktool/apktool.jar" )
fi
cat > "$TOOLS/bin/apktool" <<'EOS'
#!/bin/sh
JAVA_BIN="${REA_JAVA_BIN:-/home/user/.tools/jdk-21/bin/java}"
exec "$JAVA_BIN" -jar /home/user/.tools/apktool/apktool.jar "$@"
EOS
chmod +x "$TOOLS/bin/apktool"

# unblob needs libmagic.so.1, which Debian would normally provide; pylibmagic ships it.
cp "$VENV"/lib/python3.11/site-packages/pylibmagic/libmagic.so* "$TOOLS/lib/" 2>/dev/null || true
cat > "$TOOLS/bin/unblob" <<EOS
#!/bin/sh
export LD_LIBRARY_PATH=$TOOLS/lib:$VENV/lib/python3.11/site-packages/pylibmagic:\${LD_LIBRARY_PATH}
export MAGIC=$VENV/lib/python3.11/site-packages/pylibmagic/magic.mgc
exec $VENV/bin/unblob "\$@"
EOS
chmod +x "$TOOLS/bin/unblob"

log "8/9 stable command wrappers in /home/user/bin"
mkdir -p /home/user/bin
cat > /home/user/bin/rea <<EOS
#!/bin/sh
# Pinned to the Node.js version rea/package.json#engines requires.
exec $NODE_PREFIX/bin/node $REA_DIR/scripts/rea.mjs "\$@"
EOS
chmod +x /home/user/bin/rea
ln -sfn "$NODE_PREFIX/bin/node" /home/user/bin/node
ln -sfn "$NODE_PREFIX/bin/npm" /home/user/bin/npm
ln -sfn "$NODE_PREFIX/bin/npx" /home/user/bin/npx
ln -sfn "$TOOLS/bin/apktool" /home/user/bin/apktool
ln -sfn "$TOOLS/bin/unblob" /home/user/bin/unblob
ln -sfn "$VENV/bin/binwalk" /home/user/bin/binwalk
ln -sfn "$VENV/bin/mitmdump" /home/user/bin/mitmdump

export JAVA_HOME="$TOOLS/jdk-21"
export REA_APKTOOL_COMMAND="$TOOLS/bin/apktool"
export REA_PWNTOOLS_PYTHON="$VENV/bin/python"
export REA_UNBLOB_COMMAND="$TOOLS/bin/unblob"
export REA_BINWALK_COMMAND="$VENV/bin/binwalk"

log "9/9 REA skill + MCP registrations (Claude Code, Codex, Cursor, Gemini CLI)"
# Registration is written by REA itself so doctor's identity checks stay green.
"$REA_DIR/scripts/rea.mjs" setup --yes --all-detected
"$REA_DIR/scripts/rea.mjs" setup --yes \
  --client claude_code --client codex --client cursor --client gemini_cli

cat <<'EOS'

Done. Verify with:
  rea --version
  rea doctor --format json | head -c 600
  rea doctor --client claude_code --client codex --client cursor --client gemini_cli
  printf '' | rea mcp        # MCP server over stdio

Environment (also appended to ~/.bashrc and ~/.profile):
  PATH includes /home/user/bin /home/user/.node24/bin /home/user/.tools/bin /home/user/.venv-rea/bin
  JAVA_HOME, REA_APKTOOL_COMMAND, REA_PWNTOOLS_PYTHON, REA_UNBLOB_COMMAND, REA_BINWALK_COMMAND
EOS
