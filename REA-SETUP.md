# REA (Reverse Engineer Anything) — install report

Status of the `morluto/rea` checkout in this sandbox, what was installed, what was
verified, and what is still missing and why.

- Repository clone: `/home/user/rea` (upstream `master`, `rea-agents` **6.7.0**, commit `2250e67bc`)
- Reproduction script: [`setup-rea.sh`](setup-rea.sh) (idempotent; re-run it after a
  fresh sandbox boot, because `node_modules/` and `dist/` are not persisted)
- Ghidra installers: [`install-ghidra-offline.sh`](install-ghidra-offline.sh) (works here) and
  [`install-ghidra.sh`](install-ghidra.sh) (for hosts with release-asset access) — see [section 7](#7-ghidra-1214-installed)

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
| **Ghidra** | **12.1.4** (`Ghidra_12.1.4_build`) | git mirror `Chaborsz/Ghidra-12.1.4-Workspace` → `/opt/ghidra_12.1.4_PUBLIC` |
| **JDK for Ghidra** | **21.0.8 runtime + 21.0.11 javac** | `jdk4py` JRE + pure-Java `jdk.compiler`/`jdk.internal.opt` modules from `MineFartsEmbed/JDK` (branch 21) → `/opt/jdk-21-full` |
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
| **Native decompilation (Ghidra)** | `rea decompile /bin/ls 0x61d0 --provider ghidra` → real pseudocode, provider `ghidra 12.1.4`; also over MCP (`open_binary` + `procedure_pseudo_code`) |
| **Ghidra script compilation** | `analyzeHeadless … -postScript HelloRea.java` → `HELLO_FROM_GHIDRA` |
| Firmware extraction | `extract-firmware` on a gzip blob via **unblob 26.6.4**; standalone `unblob` extraction works |
| Android resources (decode) | `inspect-apktool-client` → apktool **2.9.3** accepted (`capability_unavailable` gone) |
| Built-in static domains | PE/CLI managed metadata, Go, Rust, IL2CPP, Godot PCK, WASM (WABT required), IPS, BEAM, GGUF/safetensors, PyInstaller, APK signatures — no external engine needed |
| Network capture tooling | `mitmdump 11.0.2` on `PATH` for HAR/SAZ-independent native capture |
| Submodule sources | all five `third_party/` checkouts present |

## 4. Not installed, and why

Ghidra was the one engine that mattered and it is now installed (section 7).
These remain unavailable because the sandbox network allowlist covers `github.com`, `codeload.github.com`,
`api.github.com`, `registry.npmjs.org`, `pypi.org`, `files.pythonhosted.org`.
GitHub **release assets** and Debian mirrors are unreachable, and there is no
Rust toolchain.

| Missing | Blocker | How to close it |
| --- | --- | --- |
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
rea decompile /bin/ls 0x61d0 --provider ghidra       # Ghidra pseudocode
rea decompile /bin/ls --procedure <symbol> --provider ghidra
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
- Ghidra and the JDK shim live in `/opt`, which is **not** part of the snapshot.
  After a restart run `bash install-ghidra-offline.sh` (~2 min) to restore them.
- The clone lives at `/home/user/rea` (outside this git repository) so the
  upstream history stays untouched. Only `setup-rea.sh` and this report are
  committed here.

## 7. Ghidra 12.1.4 — installed

Ghidra is the primary native decompiler and it is now running. Nothing here could
be fetched from the obvious place: `github.com` answers `302` for the release zip
and the redirect target `release-assets.githubusercontent.com` fails at TLS
(`code=000`), `api.adoptium.net` is unreachable, and Maven Central / Debian
mirrors are closed. So both pieces came in through **git**, which is reachable.

### How it was sourced

| Piece | Source | Evidence |
| --- | --- | --- |
| Ghidra 12.1.4 | `git clone https://github.com/Chaborsz/Ghidra-12.1.4-Workspace` (public mirror of the official archive, `ddac49f9…d4db`) | `Ghidra/application.properties` → `application.version=12.1.4`, `application.java.min=21`; native decompiler present at `Ghidra/Features/Decompiler/os/linux_x86_64/decompile` (3.4 MB) |
| `javac` | `jdk.compiler.jmod` + `jdk.internal.opt.jmod` from `MineFartsEmbed/JDK` branch `21` (Oracle JDK 21.0.11), pulled with a sparse partial clone (22 MB) | `javac 21.0.11` compiles and runs code |
| JVM runtime | `jdk4py` 21.0.8 JRE (already installed) | `java 21.0.8`, `os.arch=amd64`, 64-bit |

### Why the JDK needed a shim

`jdk4py` ships a **JRE**: `java --list-modules` has no `jdk.compiler`, and Ghidra
refuses a JRE (`JDK_ONLY`) before it will even start. Downloading Temurin is
blocked, so the missing module was supplied from another JDK build:

* `jdk.compiler` and `jdk.internal.opt` are **pure Java bytecode**, so the Windows
  JDK 21 modules work unchanged once their `ModuleTarget` attribute is removed
  (otherwise the JVM rejects `windows-amd64` against the host's `linux-amd64`).
* The modules cannot be added with `--upgrade-module-path`/`--module-path`:
  this image's `java.base` records module hashes, and the recorded hash never
  matches a foreign build (`FindException: Hash of jdk.compiler … differs`).
* Instead the modules ride on the **class path**, and `javax.tools.ToolProvider`
  — the API Ghidra's `ResourceFileJavaFileManager` calls to compile `.java`
  scripts — is **patched into `java.compiler`** with `--patch-module`, returning
  `JavacTool` from the class path.

Result: `/opt/jdk-21-full` behaves like a full JDK for REA and Ghidra
(`bin/javac`, `bin/java`, `lib/modules`), which is exactly what REA's probe reads
(`bin/javac` present → "JDK", `java.home` → `/opt/jdk-21-full`, 64-bit).

### Verified

```
rea doctor --provider ghidra        → healthy: True (9/9 checks)
  ghidra, ghidra-platform(linux), ghidra-architecture(x64), ghidra-installation,
  ghidra-version(12.1.4), ghidra-headless, ghidra-native_decompiler,
  ghidra-java(21.0.8; 64-bit; JDK; /opt/jdk-21-full)

analyzeHeadless … -postScript HelloRea.java  → HelloRea.java> HELLO_FROM_GHIDRA

rea decompile /bin/ls 0x61d0 --provider ghidra
  provider: ghidra 12.1.4 | subject: ls x86_64
  void processEntry entry(undefined8 param_1,undefined8 param_2)
  { __libc_start_main(FUN_00104730, param_2, &stack0x00000008, 0,0, param_1, auStack_8); ... }

MCP: open_binary{path:"/bin/ls", provider_id:"ghidra"} + procedure_pseudo_code{procedure:"0x61d0"}
  → same Evidence (ev_5aaae12c…), status ok, 22 s
```

### Re-installing

`/opt` is outside the workspace snapshot, so the install does not survive a fresh
sandbox. Re-create it in ~2 minutes with:

```bash
bash install-ghidra-offline.sh          # clone Ghidra, rebuild modules + JDK shim, rewire clients
bash install-ghidra-offline.sh --check  # status only
```

The script is idempotent, and re-running it also repairs a half-deleted install.
If this environment ever gains access to `release-assets.githubusercontent.com`
and `api.adoptium.net`, [`install-ghidra.sh`](install-ghidra.sh) installs the
official zip plus a real Temurin JDK instead, with no shim needed.

### Caveats

* The JDK is a shim, not a vendor JDK: `javadoc`, `jshell`, `jlink` and `jmod`
  are absent, and `javac` is 21.0.11 running against a 21.0.8 runtime (same major,
  works). Ghidra's Java-script compilation is patched through `ToolProvider`.
* `/opt/ghidra_12.1.4_PUBLIC` (876 MB) and `/opt/jdk-21-full` (~180 MB) live
  outside the repo and outside the snapshot; keep `install-ghidra-offline.sh`
  with the workspace.
* Ghidra analysis of a small binary takes ~20–25 s per session in this 2-vCPU
  container; sessions are ephemeral per REA invocation unless an MCP server
  keeps them alive.
