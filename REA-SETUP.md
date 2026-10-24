# REA (Reverse Engineer Anything) — install report

Status of the `morluto/rea` checkout in this sandbox, what was installed, what was
verified, and what is still missing and why.

- Repository clone: `/home/user/rea` (upstream `master`, `rea-agents` **6.7.0**, commit `2250e67bc`)
- Reproduction script: [`setup-rea.sh`](setup-rea.sh) (idempotent; re-run it after a
  fresh sandbox boot, because `node_modules/` and `dist/` are not persisted)

---

## 1. Installed toolchain

| Component | Version | Where it came from |
| --- | --- | --- |
| Node.js | **24.22.1** (matches `rea/.nvmrc`, satisfies `engines.node`) | npm package `node` (nodejs.org is blocked) |
| npm | **11.16.0** (matches `package.json#packageManager`) | npm package `npm` |
| REA runtime + CLI | **6.7.0**, built with `npm run build:cached` | `npm ci` (712 packages) + turbo/tsc/esbuild |
| Git submodules | `jadx-headless-mcp`, `binwalk`, `unblob`, `ghidra-nativeaot`, `wakaru` | `git submodule update --init --recursive` |
| JDK | **Temurin 21.0.8 (JRE modules)** | PyPI `jdk4py` → `/home/user/.tools/jdk-21` |
| Apktool | **2.9.3** (REA requires ≥ 2.7.0) | npm package `@postar/apktool-node` → `/home/user/.tools/apktool/apktool.jar` |
| pwntools + pyelftools + unicorn | **4.15.0 / 0.33 / 2.1.2** (exact versions REA's ELF adapter wants) | PyPI into `/home/user/.venv-rea` |
| Unblob | **26.6.4** (+ `libmagic` from PyPI `pylibmagic`) | PyPI |
| Binwalk | **v2.3.3** (pure Python; the v3 submodule needs Rust, unavailable) | codeload tarball `ReFirmLabs/binwalk v2.3.4` |
| mitmproxy | **11.0.2** (`mitmdump`) | PyPI (with `bcrypt==4.0.1` pin, passlib incompatibility) |
| Chromium (headless) | **153.0.8010.0** | npm package `@sparticuz/chromium`, Brotli-decompressed → `/home/user/.tools/chromium/chromium` |
| Binutils | objdump/readelf/nm 2.40 (pre-installed) | system |

Stable command wrappers live in `/home/user/bin`: `rea`, `node`, `npm`, `npx`,
`apktool`, `unblob`, `binwalk`, `mitmdump`. `~/.bashrc` and `~/.profile` export
`JAVA_HOME`, `PATH`, `REA_APKTOOL_COMMAND`, `REA_PWNTOOLS_PYTHON`,
`REA_UNBLOB_COMMAND`, `REA_BINWALK_COMMAND`.

`/home/user/bin/rea` is a shell wrapper that always launches REA with the pinned
Node 24.22.1, so the CLI and every MCP client spawn the correct runtime
regardless of ambient `PATH`.

## 2. MCP server

`rea setup --yes --all-detected` and `rea setup --yes --client claude_code --client
codex --client cursor --client gemini_cli` installed the workflow skill and wrote
registrations (with backups where a config already existed):

| Client | Config path | Status |
| --- | --- | --- |
| Claude Code | `~/.claude.json` + `~/.claude/skills/reverse-engineer-anything` | configured |
| Codex | `~/.codex/config.toml` | configured |
| Cursor | `~/.cursor/mcp.json` | configured |
| Gemini CLI | `~/.gemini/settings.json` | configured |
| Shared workflow skill | `~/.agents/skills/reverse-engineer-anything` | aligned (skill v46) |

Every registration carries the provider environment (`JAVA_HOME`,
`REA_APKTOOL_COMMAND`, `REA_PWNTOOLS_PYTHON`, `REA_UNBLOB_COMMAND`,
`REA_BINWALK_COMMAND`, `PATH`) in its `env` block, so the tools below are usable
from inside the MCP server.

Verified over a real stdio JSON-RPC session against `rea mcp`:

```
serverInfo    : {"name":"rea","version":"6.7.0"}
protocol      : 2025-06-18
capabilities  : completions, prompts, tools
tools/list    : 223 tools
prompts/list  : 6 prompts
tools/call    : inspect_binary_layout  -> provider pwntools-elf, 177 KB Evidence
tools/call    : analyze_javascript_application -> 193 KB Evidence
```

`rea doctor --client claude_code --client codex --client cursor --client gemini_cli`
→ `healthy: true` (node + all four registrations). `rea doctor --skill` → `healthy: true`.

## 3. What works right now

Verified by actually running each workflow:

| Workflow | Evidence |
| --- | --- |
| CLI (171 commands) | `rea --help`, `rea --version` → 6.7.0 |
| MCP server | 223 tools / 6 prompts, handshake + tool calls above |
| Build/quality gate | `npm run build:cached` and `npm run check:fast` (typecheck + oxlint, 12.6 s) pass |
| Test runner | `npx vitest run --project mcp-boundary tests/boundary/mcp/analysisSummaryDetailMcp.test.ts` → 4 passed |
| Python bridge | `python -m unittest bridge/mitmproxy/test_capture.py` → 22 passed |
| Static JavaScript / Electron | `analyze-javascript-application` on a fixture Electron app (CLI **and** MCP) |
| Native ELF layout | `inspect-binary-layout /bin/ls` via `pwntools-elf` provider |
| Firmware extraction | `extract-firmware` on a gzip blob via **unblob 26.6.4**; standalone `unblob` extraction works |
| Android resources (decode) | `inspect-apktool-client` → apktool **2.9.3** accepted (`capability_unavailable` gone) |
| Built-in static domains | PE/CLI managed metadata, Go, Rust, IL2CPP, Godot PCK, WASM (WABT required), IPS, BEAM, GGUF/safetensors, PyInstaller, APK signatures — no external engine needed |
| Network capture tooling | `mitmdump 11.0.2` on `PATH` for HAR/SAZ-independent native capture |
| Submodule sources | all five `third_party/` checkouts present |

## 4. Not installed, and why

The sandbox network allowlist covers `github.com`, `codeload.github.com`,
`api.github.com`, `registry.npmjs.org`, `pypi.org`, `files.pythonhosted.org`.
GitHub **release assets** and Debian mirrors are unreachable, and there is no
Rust toolchain.

| Missing | Blocker | How to close it |
| --- | --- | --- |
| **Ghidra 12.1.x** (primary native decompiler) | 570 MB release zip is a GitHub *release asset* (`release-assets.githubusercontent.com`, blocked); also needs a **full** JDK with `javac`, and `jdk4py` ships JRE modules only | Download Ghidra 12.1.4 + Temurin JDK 21 on a networked machine, extract, then `export GHIDRA_INSTALL_DIR=/path/to/ghidra_12.1.4_PUBLIC` and `export JAVA_HOME=/path/to/jdk-21` |
| **jadx-headless-mcp 0.7.1 JAR** | npm `jadx-headless-mcp` is only a downloader for the GitHub release; Gradle build needs Maven Central (blocked) | `export REA_JADX_MCP_JAR=/abs/path/jadx-headless-mcp-0.7.1-all.jar` |
| **Hopper** | macOS-only app | macOS hosts only (`HOPPER_LAUNCHER_PATH`) |
| **IDA / JEB / Kuna** | proprietary, licence-required | `REA_IDA_MCP_CONFIG`, `REA_JEB_MCP_URL`, `REA_KUNA_COMMAND` |
| **gdb / pwndbg** | no Debian package access | needs `gdb` on `PATH` |
| **tshark / capinfos** | no Debian package access | apt package `tshark` |
| **adb** | no Debian package access | `REA_ADB_PATH` |
| **sigrok-cli** | no Debian package access | `REA_SIGROK_COMMAND` |
| **WABT 1.0.42** | not on npm/PyPI as a binary | `REA_WABT_BIN_DIRECTORY` |
| **ILSpy** | needs .NET SDK | `REA_ILSPY_CMD_PATH` |
| **Wakaru** | submodule cloned, needs Node build of the Rust/TS deobfuscator | `REA_WAKARU_COMMAND` |
| **Playwright/Chromium for web workflows** | Chromium 153 binary obtained and runs (`--version`), but headless page rendering hangs in this 2-CPU container (zygote/shared-memory limits) | on a normal host: `npx playwright install chromium`, then `REA_BROWSER_EXECUTABLE` |
| **binwalk v3** | submodule is Rust; no cargo and no crates.io access | binwalk v2.3.3 installed as the Python fallback |

Because the four native providers are absent, `rea doctor` reports
`environment_healthy: false` (audit-wide). That is the expected, honest state:
REA's own scoped checks (`node`, `skill:identity`, each client registration) all
pass, and every engine-free workflow above runs.

## 5. Using it

```bash
rea --version                 # 6.7.0
rea doctor                    # readiness audit
rea analyze-javascript-application /path/to/app --json
rea inspect-binary-layout /bin/ls --json
rea extract-firmware blob.bin /tmp/out --json
rea mcp                       # MCP server over stdio (what the clients launch)
```

In an agent, ask e.g. *"Use REA to tell me how search works in this Electron app
and show me the evidence."* The skill instructions are already installed for
Claude Code, Codex, Cursor and Gemini CLI.

## 6. Sandbox caveats

- `node_modules/`, `dist/`, `build/` are excluded from workspace snapshots. If the
  sandbox is recreated, run `bash setup-rea.sh` again; it is incremental and
  skips anything already present (`/home/user/.node24`, `/home/user/.tools`,
  `/home/user/.venv-rea`, and the clone itself do persist).
- The clone lives at `/home/user/rea` (outside this git repository) so the
  upstream history stays untouched. Only `setup-rea.sh` and this report are
  committed here.
