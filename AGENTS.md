# AGENTS.md

Operating rules for AI coding agents working in this repository. Read this
before editing ESPHome configs.

## Repo at a glance

- ESPHome configs for this household. Top-level `*.yaml` files are per-device
  configs; `templates/*.yaml` are shared device templates included via
  `packages:`.
- ESPHome runs in Docker. Container name: `esphome` (image
  `ptr727/esphome-nonroot:latest`). The host path
  `/data/appdata/esphome/config` is mounted at `/config` inside the container.
- All ESPHome CLI invocations must run **inside the container** and use
  `/config/<file>.yaml` as the path argument.

## Branching Model

This is an **operational** repo (see the fleet
[`workflowModel`](https://github.com/ptr727/ProjectTemplate/blob/main/registry/repos.json)):
configuration is committed **directly to `develop`** with signed commits - there
is no feature branch, because this tracks the live controller state. A
`develop -> main` pull request occasionally promotes a known-good snapshot to
`main`. `develop` takes direct pushes (advisory CI); the promotion PR runs the
enforced lint check. Both branches are protected; never force-push or delete
either - fix mistakes with follow-up commits.

## Git and Commit Rules

- **Signing.** Every commit on both `develop` and `main` must be
  cryptographically signed (SSH or GPG); branch protection rejects unsigned
  commits. If signing is not configured in the environment, do not commit -
  stop at `git add` and tell the developer/maintainer that signing is
  not configured so they can set it up; do not proceed with the commit.
- **Author identity.** Commit as the repository owner's GitHub `noreply`
  identity (the same identity whose key signs) - never a private, personal, or
  invented/bot address. Verify `git config --get user.email` before committing.
- **Default to staging.** Stage changes with `git add` and leave `git commit`
  to the developer, unless the current task explicitly authorizes committing.
- **No history rewrites.** Never force-push or delete `develop` or `main`; fix
  mistakes with follow-up commits.
- **ESPHome Device Builder auto-commits (disabled - keep it that way).** This
  directory is the `/config` mount of the running `esphome` container. Device
  Builder's version history feature polls the tree for changes
  (`controllers/_device_scanner.py`, stat-based on `(inode, dev, mtime, size)`,
  not inotify) and commits every changed YAML as `Edit <file>.yaml`, authored
  `ESPHome Device Builder <device-builder@esphome.io>` and unsigned. It shells
  out to `git -c user.email=... -c commit.gpgsign=false commit --no-verify`, and
  command-line `-c` outranks the host gitconfig, so neither the host signing
  policy nor a hook can stop it. It hit this repo twice: 2026-07-14 (amended
  away) and 2026-07-18 (five commits, reset and re-committed as `08678ad`).
  - Turned off via "Save version history" in the Device Builder UI. Persisted in
    `.device-builder-preferences.json` as `version_history_enabled: false`. That
    store is RAM-canonical with a debounced write plus a shutdown flush, so
    patch the file only while the container is stopped; otherwise use the
    `config/set_preferences` API, which applies live.
  - If it is ever re-enabled, a clean `git status` no longer proves nothing was
    committed. After editing files here, run
    `git log --format='%h %G? %an <%ae>' origin/develop..HEAD` and confirm every
    commit is signed (`G`) and authored `ptr727@users.noreply.github.com`.
  - Never push commits failing that check, and never attribute them to yourself
    or to the maintainer. Check `%an`/`%ae` before claiming or denying
    authorship. Such commits are unpushed, so correcting them locally is not a
    history rewrite.

## Required validation before declaring a change "done"

Whenever a device YAML or a template that's included by a device YAML is
edited, run config validation for every affected device. If the change is in
a template, validate at least one device that uses it (and prefer all of them
if it's not obvious which ones consume it).

```bash
docker exec esphome esphome config /config/<device>.yaml
```

Look for `INFO Configuration is valid!` at the bottom. Any earlier `Failed
config` block means the change is broken even if the line count looks right.

`esphome config` only checks YAML schema + substitution resolution. It does
**not** catch compile errors. If a change touches lambdas, conditional
compilation, external components, or framework/platform versions, also run:

```bash
docker exec esphome esphome compile /config/<device>.yaml
```

Compile is slow (minutes). Reserve it for changes that could plausibly affect
generated code. For pure YAML-shape changes (renaming entities, adjusting
intervals, swapping substitution values that map to enum members) `config` is
usually enough - but if in doubt, compile.

### compile / upload / clean and sdkconfig (flashing gotchas)

Learned while flashing the office proxy over OTA:

- **`esphome upload` does NOT compile.** It flashes the last built binary. After editing YAML,
  run `esphome compile` first (or `esphome run`, which is compile + upload + logs), otherwise you
  OTA a stale binary and see no change. On a cleaned build tree `upload` fails with
  `FileNotFoundError: .../<device>.bin`.
- **sdkconfig changes need a clean build.** Options that map to esp-idf sdkconfig (`esp32_ble`
  `max_connections` -> `CONFIG_BTDM_CTRL_BLE_MAX_CONN` / `CONFIG_BT_ACL_CONNECTIONS`, or anything
  under `esp32: framework: sdkconfig_options:`) are NOT reliably regenerated by an incremental
  compile - the generated C++ updates but the controller keeps the cached sdkconfig, so the change
  silently has no effect at runtime. Run `esphome clean /config/<device>.yaml`, then a full
  `esphome compile`, and confirm the built value in `/cache/build/<device>/sdkconfig.<device>`
  before uploading.
- **Flash by IP when the name does not resolve** from the container:
  `docker exec esphome esphome upload /config/<device>.yaml --device <ip>`. Stream logs the same
  way with `esphome logs ... --device <ip>` (API port 6053; OTA is 3232).
- **`max_connections` lives on the `esp32_ble` component** (moved from `esp32_ble_tracker`) as of
  ESPHome 2026.7; the old location is deprecated and silently falls back to the default. It must be
  at least 3 (the `bluetooth_proxy` active default) plus one per `ble_client`.

### esphome logs and the API connection cap (do not leak sessions)

The device `api:` accepts only `max_connections` clients (ESP32 default **5**; Home Assistant and
the ESPHome dashboard each hold one, leaving a few spare). Crucially,
`timeout N docker exec esphome esphome logs ...` kills the `docker exec` client but **NOT** the
`esphome logs` process inside the container - it is orphaned and keeps retrying, holding a slot.
A handful of these saturate the cap, which shows as `[W][api:247]: Max connections (5), rejecting
<ip>` and makes every client (including your own logs and Home Assistant) flap with
`EOF received (SocketClosedAPIError)`. Run at most one short logs session at a time and clean up
leftovers. The busybox container has no `kill`/`pkill` binary, so use the `sh` builtin over
`/proc`:

```bash
docker exec esphome sh -c 'for d in /proc/[0-9]*; do tr "\0" " " <"$d/cmdline" 2>/dev/null \
  | grep -q "esphome logs" && kill -9 "${d#/proc/}"; done'
```

Do not raise `api: max_connections` to paper over leaked sessions; 5 is plenty (Home Assistant +
dashboard + one agent, with spares).

## Local source linting (matches CI)

The `Test pull request action` workflow gates on source linters. Run the same checks locally
before committing; nothing is needed on the host beyond Docker and `uv` (`uvx`), which is how
CI runs them too (the host has no `node`/`npm`, so use the Docker images, not `npx`).

- **Markdown** (all `.md`, reads `.markdownlint-cli2.jsonc`):

  ```bash
  docker run --rm -v "$PWD":/workdir davidanson/markdownlint-cli2:latest "**/*.md"
  ```

- **Spelling** (CI scope is every `README.md` plus `HISTORY.md`, reads `cspell.json`; fix real
  typos, add genuine project terms to `cspell.json` and keep it alphabetically sorted):

  ```bash
  docker run --rm -v "$PWD":/w -w /w ghcr.io/streetsidesoftware/cspell:latest \
    lint --no-progress --config cspell.json "**/README.md" "HISTORY.md"
  ```

- **EditorConfig** (LF endings, final newline; the exact command CI runs):

  ```bash
  docker run --rm -v "$PWD":/check --workdir /check mstruebing/editorconfig-checker:latest
  ```

- **Workflows** (`.github/workflows/*.yml`):

  ```bash
  docker run --rm -v "$PWD":/repo --workdir /repo rhysd/actionlint:latest -color
  ```

- **Python** (the `easystart/python` BLE monitor; ruff gates CI, pyright is editor parity via
  Pylance). Use the ruff version pinned in the workflow:

  ```bash
  cd easystart/python
  uvx ruff@0.15.22 check .
  uvx ruff@0.15.22 format --check .
  uvx pyright .
  ```

ESPHome config/compile validation is separate, see Required validation above.

## Verify component knobs before adding substitutions

When wiring up a substitution that maps to an ESPHome component field with a
constrained value set (an enum, an allowed-values list), verify the valid
values from the component source first. Grep the **running container's** copy,
which is the version that actually validates and compiles - the authoritative
source:

```bash
docker exec esphome sh -c 'D=$(python -c "import esphome,os;print(os.path.dirname(esphome.__file__))"); \
  grep -nE "<option>" "$D/components/<component>/__init__.py"'
```

Always grep the container, not any local ESPHome source checkout on the host: a
local copy can be **stale** relative to the running version (it lagged a
`max_connections` relocation, for example). `sensor.py` / `__init__.py` / `*.py`
contain the schema with the canonical enum. Do not rely on memory or external
docs alone: enum membership in the installed ESPHome version is the only
authority.

Example failure to avoid: `variant: AHT21` was suggested as a valid value for
the `aht10` platform. The component's `AHT10_VARIANTS` dict only contains
`AHT10` and `AHT20`. `esphome config` caught it, but the right move would
have been to grep the component first.

## Apollo PLT-1B template

[templates/apollo-plt-1b.yaml](templates/apollo-plt-1b.yaml) imports the full
upstream `github://ApolloAutomation/PLT-1/Integrations/ESPHome/PLT-1B.yaml@main`
package and surgically strips stock-provisioning. The upstream package is
cached at `/data/appdata/esphome/cache/data/packages/8bc80dd7/Integrations/ESPHome/`

- read those files when answering "where does Apollo set X" questions.

Substitutions exposed for per-plant override:

- `sleep_duration_hours` - first-boot value of HA "Sleep Duration" number.
  After first boot, HA owns the value via NVS (`restore_value: true`). Changing
  the substitution does **not** move an already-deployed device.
- `prevent_sleep_default` (`ON` / `OFF`) - first-boot state of the HA "Prevent
  Sleep" switch. Same NVS-wins semantics.
- `aht_variant` (`AHT10` / `AHT20`) - AHT chip init mode. Compile-time, takes
  effect on next flash.

NVS-vs-substitution semantics matter: for any of these knobs to actually
change behavior on a previously-deployed unit, NVS must be wiped (USB
`esptool.py erase_flash` + reflash). OTA reflash preserves NVS.

## SmartHome CeilSense template

[templates/smarthome-ceilsense.yaml](templates/smarthome-ceilsense.yaml)
assembles the device from SmartHomeShop's firmware **sub-packages**
`github://smarthomeshop/ceilsense/ceilsense-v1/{base.yaml, packages/ld2412.yaml,
packages/scd4x.yaml}@main` rather than the vendor's
`ceilsense-complete-wifi-ld2412.yaml` entry point. That entry point also pulls in
`wifi.yaml`, whose `on_boot` calls the `ble.disable` action (and brings in the
Improv/BLE provisioning stack). Because `on_boot` is an un-id'd list, that single
action can't be `!remove`d, so importing the entry point forces you to keep a
BLE stack alive just to satisfy the action. Importing the sub-packages and
supplying our own `wifi:` + boot phase 1 drops Bluetooth entirely (no
`esp32_ble`, no Improv, no captive portal). `base.yaml` and the two sensor
packages contain no BLE references.

From `base.yaml` it then strips the cloud/project machinery: the `http_request`
`update:` firmware-update entity, the cloud/local "Firmware Variant" `select`
and its glue `script`, the `ble_disable_after_boot` switch (now pointless), plus
`web_server`. `project: !remove` is safe here (unlike Konnected blaQ): nothing in
the sub-packages references the `ESPHOME_PROJECT_NAME/VERSION` compile-time
macros - the Software Version text sensor uses the `${project_version}`
*substitution*, which still resolves after the block is gone.

Consumed by [garage-presence-sensor.yaml](garage-presence-sensor.yaml). Tracks
`@main` on a `0.9.0-beta` upstream, so an upstream id rename surfaces as a
"Source for removal not found" error at `esphome config` - re-check the removed
ids if that appears, or pin a `@<sha>`. Note this trades the vendor's maintained
variant entry point for hand-assembling its parts: if upstream restructures
`base.yaml`/the packages, re-diff against the current
`ceilsense-complete-wifi-ld2412.yaml` to see what changed.

## Converting vendor cloud/project firmware to local (reusable pattern)

Pattern shared by Apollo PLT-1B, Konnected blaQ, and CeilSense. To convert a new
vendor device:

- **Import** the vendor's assembled *variant entry file* as a `github://...@<ref>`
  package; add the house `time.yaml` include (and `api.yaml`/`ota.yaml`/
  `logger.yaml` if the vendor doesn't already define those).
- **Whole-key `!remove`** each stock provisioning/cloud/web surface that is its
  own top-level key: `dashboard_import`, `captive_portal`, `esp32_improv`,
  `improv_serial`, `web_server`, `update`, `http_request`.
- **Remove-by-id** (`- id: !remove <id>`) when the unwanted thing is one item in
  a list shared with entities you keep (e.g. a cloud `select` item, a
  firmware-update `button`, the glue `script`, the `http_request` OTA platform).
  ESPHome's `merge_config` (`esphome/config_helpers.py`) matches the id; a
  dangling reference left behind only fails at `compile`, not `config`, so
  compile once after this kind of change.
- **Project identity / Update Manager:** prefer `esphome: project: !remove`
  (Apollo, CeilSense). Only fall back to overriding `project_version: "0.0.0"`
  when upstream lambdas reference the `ESPHOME_PROJECT_NAME/VERSION` macros
  (Konnected) - grep the upstream package before removing the block.
- **Override local env:** `wifi: ap: !remove` + `!secret` ssid/password/domain;
  `api.encryption.key`; OTA password via `- id: !extend <ota_id>`.
- **Keep templates minimal - identity + secrets + cloud-stripping only.** Nuanced
  per-device tuning (I2C frequency, sensor `variant`, etc.) was tried on the
  Apollo PLT-1B and made *no observable difference* (e.g. the SCD41/AHT humidity
  still tracks ambient/outdoor humidity and isn't tunable away). Don't add such
  knobs preemptively; add them only when a concrete problem demands it.

## Writing style (prose, comments, docs, commits)

Write like the developer who owns this repo, not like an AI assistant.

- **No em-dashes.** Use a hyphen with spaces (` - `), a comma, a colon, or a new
  sentence instead. Em-dashes read as AI-generated.
- **ASCII only in text you author.** Don't introduce non-ASCII characters
  (smart quotes, ellipsis glyphs, arrows, en/em-dashes, etc.) when writing prose,
  comments, or markdown. Use plain `"`, `'`, `...`, `->`.
- **Exception: characters that carry real meaning.** A symbol the value depends
  on is fine and should be preserved - e.g. an Ohm sign for resistance, a degree
  sign for temperature, or any Unicode the user deliberately added. Don't strip
  those.
- This applies to anything you generate: code comments, markdown, commit
  messages, PR text. If the user adds a Unicode symbol on purpose, leave it; just
  don't author em-dashes or decorative non-ASCII yourself.

### Comments are structured, not prose

Comment only where a comment is needed, and keep it scannable.

- Prefer a single-line comment.
- One sentence per line; never wrap prose across lines.
- No block paragraphs and no multi-sentence run-ons.
- Indent with sub-bullets (`# - point`) only for actual sub-topics, meaning parallel items
  hanging off a lead line. A continuation of the same topic stays unindented.

Continuation, so no indentation:

```yaml
# Change gate for the compile tests.
# An esp-idf build costs minutes, so gate on what each test covers.
# An undeterminable diff runs everything.
```

Sub-topics, so indented, because each line elaborates a distinct item named in the lead:

```yaml
# Source lint plus change-gated compile tests.
# - compile-test builds the easystart external component.
# - template-compile-test builds one example device per published template.
```

## Reverse-engineering and external tooling

BLE and device reverse-engineering work (for example the Micro-Air EasyStart soft-starter)
follows [easystart/BLE-RE-PLAYBOOK.md](easystart/BLE-RE-PLAYBOOK.md): the agent drives adb /
apktool / jadx and decodes the protocol, the human only plugs in the phone and runs the BLE
monitor. Project-specific notes stay in the project folder
([easystart/AGENTS.md](easystart/AGENTS.md), [easystart/PROTOCOL.md](easystart/PROTOCOL.md)).

When a CLI tool is needed, look for it first (PATH, then package-manager dirs, then a local copy
already in the repo); if it is missing, self-source the official GitHub release or vendor zip
locally. Do not auto-run `winget install` or other system package managers: sourcing a portable
zip or jar is fine, mutating installed system packages is not. Ask the maintainer if a tool
cannot be found or sourced.

## Things to avoid

- Don't claim a config change is working until `esphome config` (and, where
  appropriate, `esphome compile`) returns success.
- Don't invent enum values, component fields, or framework option names. Grep
  the component source if uncertain.
- Don't `!remove` blocks from Apollo's package without checking what depends
  on the IDs inside - Apollo's lambdas reference IDs across files, and a
  missing ID surfaces as a compile error, not a config error.
