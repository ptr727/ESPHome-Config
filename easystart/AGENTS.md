# AGENTS.md - notes for the next agent session

Hints for a Claude agent picking up this project. Read this first, then `PROTOCOL.md` and
`BLE-RE-PLAYBOOK.md`.

## What this project is

Reverse-engineering the **Micro-Air EasyStart** soft-starter's BLE protocol and exposing the AC
compressor state in Home Assistant via an **ESPHome** `ble_client` component. The user has two
modules. Discover units with the monitor's `--discover` scan. **Real device MACs/names are PII
and stay out of the repo** - the only place they live is the git-ignored ESPHome `secrets.yaml`.
When editing docs/code/config, never paste real MACs or advertised names; use placeholders like
`EasyStart_XXXX` / `AA:BB:CC:DD:EE:01`.

## Status

- **Protocol: fully decoded and hardware-validated**, and cross-checked against the community
  implementations. See `PROTOCOL.md`. Don't re-derive it.
- **ESPHome component: feature-complete and hardware-validated** at `components/easystart/`
  (current, estimated power, frequency, peak, SCPT delay, system state, counters,
  running-from-BLE-presence). The reusable package is `../templates/easystart.yaml`; the working
  two-module config is `../office-bluetooth-proxy.yaml`. Flashed on the office GL-S10 proxy and
  confirmed against both live modules: both `ble_client`s connect, every decoded field matches the
  frame math (e.g. HVAC 1 `6.7 A` / `59.82 Hz` / peak `23.7 A` / `1978` starts; HVAC 2 `6.4 A` /
  `4961` starts), and both `running` binary_sensors report `on` in Home Assistant.
- **`bluetooth_proxy` + 2 `ble_client`s coexist cleanly.** Needs `esp32_ble: max_connections: 5`
  (3 proxy default + 2 clients); `max_connections` lives on `esp32_ble` now, not
  `esp32_ble_tracker`, and a change needs a clean rebuild to take effect (see the root `AGENTS.md`
  flashing gotchas). Free heap stays healthy (~160 KB), so the classic ESP32-D0WD has ample RAM
  for all five connections plus the proxy.
- **Placement matters: EasyStart BLE is very short range.** The proxy first would not connect from
  its original office location; relocating it near the units was required before either module
  linked. An external-antenna ESP32 helps if the signal is marginal.
- **Compressor shutoff behavior: confirmed.** When a compressor stops, the module powers its BLE
  radio down, the `ble_client` disconnects, and the component's offline path fires: `running` goes
  `off`, the live sensors blank to NaN (shown as `unknown` in Home Assistant), and system state
  reports `Off`. Both modules did this cleanly on power-down, within a couple of seconds of each
  other; the exact flip latency is BLE supervision-timeout dependent.

## Protocol cheat-sheet (validated)

- Laird VSP service `d973f2e0-...`; **`e1` = NOTIFY, `e2` = WRITE** (opposite of Laird convention).
- Poll: write ASCII `{"Cmd": ReadLive}` to `e2`. Reply = one 18-byte binary frame + an ASCII
  `{"Sts": Success}` on `e1`.
- Frame: `[2]`=state (0=Normal), `[4]+[5]*256 /10`=current A, `[6]+[7]*256`->`500000/that`=Hz,
  `[8]+[9]*256 /10`=peak A, `[12..13]`=faults, `[14..17]`(u32)=total starts.
- The module powers BLE only while the compressor runs -> **BLE presence = running**.

## Tool discovery & sourcing policy

When a tool is needed, in order:

1. **Look for it** - check PATH, then winget package dirs
   (`~/AppData/Local/Microsoft/WinGet/Packages/<Publisher>.<Name>_*/`), then local copies in the
   repo (zips/jars already downloaded here).
2. **Self-source if missing** - download the official **GitHub release** (or vendor zip) and
   extract it locally; that's fine to do without asking.
3. **Ask the user** only if it can't be found or self-sourced.

**Do NOT auto-run `winget install`** (or other system package managers). Sourcing a portable
zip/jar into the repo or a temp dir is fine; mutating the system's installed packages is not.

## Working the tools (Windows, Git Bash) - verified invocations & gotchas

- **`adb`** - on PATH via winget (`Google.PlatformTools`). Run `adb` directly; the repo's
  `platform-tools/` zip is redundant. Phone stays authorized between sessions.
- **`apktool`** - NOT on PATH. Run the local jar: `java -jar apktool_3.0.3.jar d <apk> -o <dir>`.
- **`jadx` (CLI)** - winget `Skylot.jadx` installs the **GUI only** (`jadx-gui-*.exe`), no CLI.
  The CLI is in the GitHub-release zip: **`jadx-1.5.6/bin/jadx.bat`** (verified `--version`
  1.5.6). In Git Bash invoke via `cmd //c "jadx-1.5.6\bin\jadx.bat ..."`. `apktool` smali is
  usually enough - reach for jadx only when readable Java helps.
- `adb shell pm path <pkg>` (or `cmd package path`) prints a `package:` prefix **and a Windows
  `\r`** - strip both: `... | tr -d '\r' | sed 's/^package://'`.
- `adb pull` prints progress to **stderr**, not stdout.
- **`tools/pull-apk.sh <keyword> [outdir]`** does the whole extract: resolves the package, reads
  version via `dumpsys`, pulls to `<package>-<versionName>-<versionCode>.apk` (handles split
  APKs). E.g. `bash tools/pull-apk.sh easystart .` -> `net.microair.easystart-4.2-19.apk`.
- The already-extracted decompile is in `EasyStart-apktool/` (app package under
  `smali/net/microair/easystart/`). Grep UUIDs / `writeCharacteristic` / `setValue` there.

## Live BLE validation

- The user runs `python/easystart_monitor.py` (uv-runnable, `bleak`) from their **MacBook** and
  pastes the text output. The agent can't reach the user's BLE radio, so it can't run the
  monitor itself. On macOS select by `--name` (CoreBluetooth hides the MAC).
- Only one BLE central connects at a time - close the phone app first.

## User preferences

- Prefers **uv / uvx** for Python (PEP 723 inline deps; `uv run script.py`), not pip/venv.
- Wants the agent to **drive CLI tools directly** (adb/apktool/jadx) - no phone-app data
  capture, no screenshots for static analysis. See `BLE-RE-PLAYBOOK.md`.
- Keep scripts minimal; extend per-purpose when needed rather than pre-building features.

## Repo map

- `PROTOCOL.md` - the validated protocol (source of truth).
- `BLE-RE-PLAYBOOK.md` - the reusable, low-friction RE method.
- `python/` - `bleak` live monitor (run with `--discover` to find your own units). Real MACs
  are kept only in the ESPHome `secrets.yaml`, never in this repo.
- `components/easystart/` - the ESPHome external component (code + codegen).
- `../templates/easystart.yaml` - reusable per-module package; `../office-bluetooth-proxy.yaml`
  is the working two-module proxy config.
- `tools/pull-apk.sh` - APK extraction helper.
- `EasyStart-apktool/` - decompiled app (kept local; not committed - proprietary).
