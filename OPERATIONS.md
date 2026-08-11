# ESPHome Operations

How to work in this repository: reaching the ESPHome CLI, validating and flashing a change, the template and vendor-firmware patterns, the tooling hazards, and the traps that have cost time before. [`AGENTS.md`][agents] carries the cross-cutting rules every repository in the fleet shares. Read this file before editing any YAML under this tree, and read [Repository Tooling Hazards][repository-tooling-hazards] before driving `gh` or the repo-config script.

`AGENTS.md` is carried fleet law and byte-locked, so a durable rule specific to this repository cannot live there. It goes in whichever local doc owns the subject: ESPHome operations and repository tooling here, code and documentation style in [`CODESTYLE.md`][codestyle], the CI/CD workflow contract in [`WORKFLOW.md`][workflow].

## Keeping This File Current

An operational discovery is written down as part of the change that surfaced it, never left in a session note or an agent's memory. This is the local routing for the self-improvement rule in [`AGENTS.md`][agents], which owns the principle.

- **A mechanism that stopped working, and whatever replaced it**, goes in the section that owns the subject. Record the replacement and the reason the old route failed, so the next agent does not retry it.
- **A procedure carried out for the first time** gets a section describing how, not that it happened. Write the recipe someone would follow, and name the command or the file rather than narrating the session.
- **A fact established by running something** is recorded with what proved it, since a claim nobody can re-derive gets doubted and re-tested. Prefer the observed output over an assertion.
- **A defect in the carried fleet content** - `AGENTS.md`, `CODESTYLE.md`, `WORKFLOW.md`, `.github/copilot-instructions.md`, `repo-config/`, `spec/`, `AUDIT.md` - is reported upstream rather than patched here, because a local edit registers as drift and fails the audit. Filing that report is a **cross-repository write and needs the maintainer's explicit permission for that specific repository in the current session**, per [Repository Boundaries and Write Safety][agents-write-safety]. Ask, do not assume.
- **Nothing here is a changelog.** State the current mechanism in the present tense, per the documentation rules in `AGENTS.md`. The before-and-after belongs in the commit message.
- **`git blame` does not establish who wrote a line.** Agent commits carry the maintainer's `noreply` identity by policy, so blame attributes agent-authored prose to the maintainer just as it does their own. The `AGENTS.md` carve-out for Unicode the developer deliberately typed cannot be claimed from blame output, and a review flagging non-ASCII is answered by removing it rather than by defending it with an authorship claim the repository cannot support.

## External Package Usage

Templates are consumed two ways. Inside this repository a device config composes them with a local `!include`, which is what [`test/`][test] exercises. Outside it, an adopter composes them as a remote `github://` package, and every template opens with an `External usage:` comment block carrying that form plus whatever it needs from the including config.

The mechanics below were confirmed against ESPHome 2026.7.3 by validating a scratch config that pulled [`templates/common.yaml`][common-template] from `@main`.

- **The package is cloned, not read from the working tree.** `esphome config` logs `INFO Cloning https://github.com/ptr727/ESPHome-Config.git@main` and resolves the files under `/cache/data/packages/<hash>/`. A relative `!include` inside a template therefore resolves against that cache, so sibling includes such as `common.yaml` pulling `wifi.yaml` work unchanged.
- **`!secret` falls back to the consuming config's own directory.** Resolution tries the package's `templates/secrets.yaml` first, whose `<<: !include ../secrets.yaml` fails because the repository root `secrets.yaml` is git-ignored, then tries a `secrets.yaml` beside the including config. An adopter supplies their own under the names in [`secrets._yaml`][secrets-example], and both paths appear in the error when neither exists.
- **`test/` cannot use the remote form**, and the reason is the clone above. A `github://` package fetches the named ref rather than the working tree, so a compile test written that way would build `@main`'s copy of a template and pass while the change under test is broken. It also cannot work for a template that does not exist on the ref yet. Local `!include` is the only form that gates a diff.

Four templates deviate from the plain shorthand, and each says so in its own block:

- [`easystart.yaml`][easystart-template] is parameterized, so it takes the `url` / `ref` / `files` form with `vars` rather than the one-line shorthand.
- The `esp32-s3-wroom-*` board definitions are overlays, so they are composed on [`esp32-s3-devkitc.yaml`][devkitc-template] as a second package entry.
- [`norvi-enet-ae06-r.yaml`][norvi-template] reaches `Utils.h` through `esphome: includes:`, which resolves against the *including* config's directory rather than the package cache, so an adopter copies that file locally and points `templates_dir` at it.
- [`templates/secrets.yaml`][secrets-template] is repository-internal plumbing and is not externally usable, since it re-exports a path that exists only in this tree.

Renaming or moving a template breaks every one of these blocks and the [`README.md`][readme] paths, and nothing in CI notices, because the local test config is renamed alongside it and stays green. Re-check the block whenever a template's filename changes.

## Documenting a Device

This is a public repository whose primary audience is people reusing the templates, and it is also the live config directory of one specific home. Two human-facing docs keep those apart, and a change that adds prose picks between them before it picks a section.

- **[`README.md`][readme] documents the reusable surface**: what each template in [`templates/`][templates] is for, the hardware it targets, its substitutions, its flashing route, and the gotchas that follow the template to whoever adopts it. It is written for a reader who owns none of these devices.
- **[`DEVICES.md`][devices] documents the deployed fleet**: one section per device or device family, naming the template it composes and carrying the siting, status, and maintenance state of the physical unit. A reader who is not the maintainer has no use for it.
- **The test is whether a stranger reusing the template needs it.** Knowledge that generalizes to any instance of the hardware belongs in `README.md`. Anything true only of this installation - where a unit is mounted, what signal it sees there, why one is powered off, which ones await a reflash - belongs in `DEVICES.md`. A device-specific fact does not migrate to `README.md` by being interesting.
- **Agent-facing depth stays here** in [Template Notes][template-notes]. `README.md` and `DEVICES.md` are both written for humans, so a mechanism an agent needs in order to change a config safely is documented in this file and linked from there rather than expanded inline.

## Container and CLI

This directory is the `/config` mount of a running ESPHome instance, so the tree you are editing is live state, not a checkout that gets deployed later.

- Top-level `*.yaml` files are the per-device configs. [`templates/`][templates] holds the shared device and utility templates they include via `packages:`.
- ESPHome runs in Docker under the container name `esphome`, from the [`ptr727/esphome-nonroot`][esphome-nonroot-link] image. The host path `/data/appdata/esphome/config` is mounted at `/config` inside the container.
- Every ESPHome CLI invocation runs **inside the container** and takes `/config/<file>.yaml` as its path argument. A host-side `esphome` binary, if one exists at all, is a different version from the one that actually validates and compiles.

```shell
docker exec esphome esphome config /config/<device>.yaml
```

## Config and Compile Validation

Whenever a device YAML, or a template included by one, changes, run config validation for every affected device. When the change is in a template, validate at least one device that uses it, and prefer all of them when it is not obvious which ones consume it.

```shell
docker exec esphome esphome config /config/<device>.yaml
```

Look for `INFO Configuration is valid!` at the bottom. An earlier `Failed config` block means the change is broken even when the line count looks right.

`esphome config` checks YAML schema and substitution resolution only. It does **not** catch compile errors. When a change touches lambdas, conditional compilation, external components, or framework and platform versions, also compile:

```shell
docker exec esphome esphome compile /config/<device>.yaml
```

A compile costs minutes, so reserve it for changes that can plausibly affect generated code. For pure YAML-shape changes - renaming entities, adjusting intervals, swapping substitution values that map to enum members - `config` is usually enough, but compile when in doubt.

## Flashing and sdkconfig

- **`esphome upload` does not compile.** It flashes the last built binary, so after editing YAML run `esphome compile` first, or `esphome run`, which is compile plus upload plus logs. Skipping the compile flashes a stale binary and shows no change. On a cleaned build tree `upload` fails with `FileNotFoundError: .../<device>.bin`.
- **sdkconfig changes need a clean build.** Options that map to an esp-idf sdkconfig entry - `esp32_ble` `max_connections` mapping to `CONFIG_BTDM_CTRL_BLE_MAX_CONN` and `CONFIG_BT_ACL_CONNECTIONS`, or anything under `esp32: framework: sdkconfig_options:` - are not reliably regenerated by an incremental compile. The generated C++ updates while the controller keeps the cached sdkconfig, so the change has no effect at runtime and nothing reports an error. Run `esphome clean /config/<device>.yaml`, then a full `esphome compile`, and confirm the built value in `/cache/build/<device>/sdkconfig.<device>` before uploading.
- **A device answers to its FQDN, not to `<name>.local`.** DHCP hands out a default domain that the local DNS serves, and [`templates/wifi.yaml`][wifi-template] passes it to the `wifi` component as the `wifi_domain` secret, so a WiFi device is `<device_name><wifi_domain>`. Read the current value from `secrets.yaml` rather than assuming, and note that an Ethernet device such as the GL-S10 sets no domain of its own and is reachable only by whatever DHCP registered for it.
- **Flash by IP when the name does not resolve** from the container: `docker exec esphome esphome upload /config/<device>.yaml --device <ip>`. Stream logs the same way with `esphome logs ... --device <ip>`. The API port is 6053 and OTA is 3232. Home Assistant carries each device's current address in its `IP Address` text sensor, which is the quickest way to look one up.
- **`max_connections` lives on the `esp32_ble` component**, not `esp32_ble_tracker`. The `esp32_ble_tracker` location is deprecated and falls back to the default without warning. The value is one per `ble_client`, plus 3 more when the device also runs a `bluetooth_proxy`, whose active default claims 3.

## Logs and the API Connection Cap

A device's `api:` accepts only `max_connections` clients, defaulting to **5** on ESP32. Home Assistant and the ESPHome dashboard each hold one, which leaves a few spare.

`timeout N docker exec esphome esphome logs ...` kills the `docker exec` client but **not** the `esphome logs` process inside the container. That process is orphaned and keeps retrying, holding a slot. A handful of these saturate the cap, which shows as `[W][api:247]: Max connections (5), rejecting <ip>` and makes every client, including Home Assistant, flap with `EOF received (SocketClosedAPIError)`.

Put the timeout **inside** the container and give the output a file rather than a pipe, which reaps the session on its own and exits 124:

```shell
docker exec esphome timeout 45 esphome logs /config/<device>.yaml --device <ip> > /tmp/<device>.log 2>&1
```

Anything that closes the client's stdout early detaches it the same way the outer-timeout form does, so a trailing `| head -N` leaves the in-container process running until its own timeout expires. Capture to a file and read the file.

To see a device's boot banner and `dump_config`, attach first and then restart it from Home Assistant's `Restart` button. Early boot output predates the API connection and is only ever on the serial console.

Run at most one short logs session at a time and clean up leftovers. The container has no `kill` or `pkill` binary, so use the `sh` builtin over `/proc`:

```shell
docker exec esphome sh -c 'self=$$; for d in /proc/[0-9]*; do
  p=${d#/proc/}; [ "$p" = "$self" ] && continue
  c=$(tr "\0" " " <"$d/cmdline" 2>/dev/null)
  case "$c" in *"esphome logs"*) [ "${c#*sh -c}" = "$c" ] && kill -9 "$p" ;; esac
done'
```

**The reaper must exclude itself.** Its own `sh -c` argument contains the string it scans for, so a naive `grep -q "esphome logs"` over every `/proc/*/cmdline` matches the scanning shell. That inflates the session count, which reads as a cap problem that is not there, and it is actively destructive in a keep-the-newest variant: the scanning shell is always the newest process, so "keep the highest PID" keeps the reaper and kills the live capture. Skipping the current PID and any `sh -c` wrapper is what makes the count and the kill correct.

Do not raise `api: max_connections` to paper over leaked sessions. Five is plenty for Home Assistant, the dashboard, and one agent, with spares.

## Bluetooth Proxies and BLE Clients

- **Scan parameters stay at the ESPHome defaults.** `interval` 320ms, `window` 30ms, and `active: true` are what upstream's own proxy configs ship. The [`bluetooth_proxy` docs][bluetooth-proxy-link] name a full duty cycle, `interval` and `window` both 1100ms, as an anti-pattern that adds CPU load and heat for no gain, and on a WiFi-connected board it also fights the shared radio. It competes with the connection events of any `ble_client` on the same device, so the cost lands where it hurts most.
- **Passive scanning is enough to reach a known MAC.** A device whose only BLE job is connecting to `ble_client` targets parses no advertisement payloads, so `active: false` drops the scan-request transmissions with nothing lost.
- **`ble_client` depends on `esp32_ble_tracker`, and needs it scanning.** The tracker is a hard dependency, and a client only connects once a scan discovers its address. Continuous scanning is the sole path back after a disconnect, so `continuous: false` strands a dropped module until something else starts a scan.
- **A `ble_client` automation action registers itself as a BLE node, and most never report `ESTABLISHED`.** `ble_client.disconnect`, `ble_client.connect`, and the other actions in ESPHome's `ble_client/automation.h` call `register_ble_node(this)` from their constructors, and their handlers return early while `num_running_ == 0`. `BLEClientDisconnectAction` never assigns `node_state` at all. Since `BLEClient` releases its cached services only once *every* node reports `ESTABLISHED`, a single such action anywhere in a config suppresses that release for the whole client, so the service memory is never reclaimed. Use a `lambda` calling `id(client)->disconnect()` when the action's own completion semantics are not needed. This also masks the crash described in [`easystart/ESPHOME-BLE-ISSUE.md`][ble-issue], which is why it took a component without any such action to surface it.
- **A flashing status LED on a device with a `ble_client` is usually not a fault.** The `ble_client` RSSI sensor calls `status_set_warning()` on `ESP_GATTC_CLOSE_EVT`, and `status_led` blinks on any component warning. An EasyStart module holds its BLE link only while its compressor runs, so the LED flashes for as long as a compressor is idle, which is most of the time. Judge link quality by the RSSI value and its history, never by the LED.

## Strapping Pin Warnings

A pin ESPHome considers a strapping pin warns at every validation. Where the wiring is fixed by the board and known good, silence it at the pin rather than letting the noise train you to ignore validation output.

- **`ignore_strapping_warning: true` belongs inside the pin schema**, so the shorthand `pin: GPIO15` has to expand to a `pin:` mapping with `number:` first. Placing the key beside `pin:` is accepted by no schema and silences nothing, which is the usual reason it "does not work".
- **A component that takes a bare pin number still accepts the pin mapping.** `ethernet` validates `mdc_pin`, `mdio_pin`, `power_pin`, and `clk.pin` with `pins.internal_gpio_pin_number`, and `esp32_camera` validates `data_pins` and `external_clock.pin` the same way. That validator rejects only `mode` and `inverted`, then runs the full pin schema and returns just the number, so expanding the pin to a `number:` mapping carrying `ignore_strapping_warning: true` validates and silences the warning.
- **A pin owned by an upstream package** warns from that package's own schema, so silencing it means overriding the upstream pin rather than editing this repo's YAML.

## Verifying Component Knobs

When wiring up a substitution that maps to an ESPHome component field with a constrained value set - an enum or an allowed-values list - verify the valid values from the component source first. Grep the **running container's** copy, which is the version that actually validates and compiles:

```shell
docker exec esphome sh -c 'D=$(python -c "import esphome,os;print(os.path.dirname(esphome.__file__))"); \
  grep -nE "<option>" "$D/components/<component>/__init__.py"'
```

Always grep the container, never a local ESPHome source checkout on the host. A local copy can be **stale** relative to the running version, and one lagged a `max_connections` relocation. The schema with the canonical enum lives in `sensor.py`, `__init__.py`, or another `*.py` under the component directory. Enum membership in the installed ESPHome version is the only authority, so do not rely on memory or external docs alone.

For a concrete failure this prevents: `variant: AHT21` looks like a valid value for the `aht10` platform, but the component's `AHT10_VARIANTS` dict contains only `AHT10` and `AHT20`. `esphome config` catches it, and grepping the component first catches it sooner.

## Vendor Firmware Conversion Pattern

Apollo PLT-1B, Konnected blaQ, and CeilSense all follow one pattern for converting a vendor's cloud and project firmware to a local configuration. To convert a new vendor device:

- **Import** the vendor's assembled *variant entry file* as a `github://...@<ref>` package, then add the house `time.yaml` include, plus `api.yaml`, `ota.yaml`, and `logger.yaml` when the vendor does not already define those.
- **Whole-key `!remove`** each stock provisioning, cloud, and web surface that is its own top-level key: `dashboard_import`, `captive_portal`, `esp32_improv`, `improv_serial`, `web_server`, `update`, `http_request`.
- **Remove by id** with `- id: !remove <id>` when the unwanted thing is one item in a list shared with entities you keep, such as a cloud `select` item, a firmware-update `button`, the glue `script`, or the `http_request` OTA platform. ESPHome's `merge_config` in `esphome/config_helpers.py` matches on the id. A dangling reference left behind fails at `compile` rather than `config`, so compile once after this kind of change.
- **Project identity and Update Manager:** prefer `esphome: project: !remove`, as Apollo and CeilSense do. Fall back to overriding `project_version: "0.0.0"` only when upstream lambdas reference the `ESPHOME_PROJECT_NAME` or `ESPHOME_PROJECT_VERSION` macros, as Konnected's do. Grep the upstream package before removing the block.
- **Override local environment:** `wifi: ap: !remove` plus `!secret` ssid, password, and domain, then `api.encryption.key`, and the OTA password via `- id: !extend <ota_id>`.
- **Keep templates minimal, covering identity, secrets, and cloud-stripping only.** Nuanced per-device tuning such as I2C frequency or a sensor `variant` was tried on the Apollo PLT-1B and made no observable difference: the SCD41 and AHT humidity still tracks ambient and outdoor humidity and is not tunable away. Add such knobs only when a concrete problem demands one.

## Template Notes

### Apollo PLT-1B

[`templates/apollo-plt-1b.yaml`][apollo-template] imports the full upstream `github://ApolloAutomation/PLT-1/Integrations/ESPHome/PLT-1B.yaml@main` package and surgically strips stock provisioning. The upstream package is cached at `/data/appdata/esphome/cache/data/packages/8bc80dd7/Integrations/ESPHome/`, so read those files to answer "where does Apollo set X" questions.

Three substitutions are exposed for per-plant override:

- `sleep_duration_hours` - the first-boot value of the Home Assistant "Sleep Duration" number. After first boot Home Assistant owns the value via NVS with `restore_value: true`, so changing the substitution does not move an already-deployed device.
- `prevent_sleep_default`, either `ON` or `OFF` - the first-boot state of the Home Assistant "Prevent Sleep" switch, with the same NVS-wins semantics.
- `aht_variant`, either `AHT10` or `AHT20` - the AHT chip init mode. It is compile-time and takes effect on the next flash.

The NVS-versus-substitution semantics matter: for any of these knobs to change behavior on a previously deployed unit, NVS must be wiped with a USB `esptool.py erase_flash` plus a reflash. An OTA reflash preserves NVS.

Do not `!remove` blocks from Apollo's package without checking what depends on the ids inside. Apollo's lambdas reference ids across files, and a missing id surfaces as a compile error rather than a config error.

### GL-S10 Bluetooth Proxy

- **The board has no PSRAM.** GL-iNet's datasheet and the community pages claim 8MB, and the hardware does not have it. Treat the 8MB figure as wrong for this board revision and do not add `psram:` back.
- **The status LED convention is deliberate.** The `status_led` pin is intentionally not inverted, so a lit globe LED means healthy and a flashing one means a warning or error, which is the reverse of what upstream's own `gl-s10.yaml` produces. A sync with upstream must not "fix" it.
- **Its GPIO0 and GPIO5 strapping warnings are silenced at the pin**, since the `ethernet` clock and power wiring is fixed by the board, see [Strapping Pin Warnings][strapping-pin-warnings].

### Waveshare ESP32-S3-ETH

[`templates/waveshare-esp32-s3-eth.yaml`][waveshare-template] is a board template, so a device config composing it supplies its own job, the way [`office-bluetooth-proxy.yaml`][office-bluetooth-proxy] adds `esp32_ble_tracker` and `bluetooth_proxy` on top.

- **It cannot include `common.yaml`.** The `ethernet` component declares `CONFLICTS_WITH = ["wifi"]`, and `common.yaml` carries [`wifi.yaml`][wifi-template], so the template composes the individual includes instead. Anything else added to the tree that pulls in a `wifi:` key breaks it, which is the reason [`rgb-led-status.yaml`][rgb-led-status-template] carries its own status logic rather than the upstream package, see [RGB LED Status][rgb-led-status].
- **The W5500 pins carry no strapping warnings.** None of GPIO9 through GPIO14 is an ESP32-S3 strapping pin, so validation output for this board should be clean and a new warning means something actually changed.
- **The `ethernet` component owns its SPI bus outright.** An SPI based PHY does not go through the `spi` component, so those four pins cannot be shared, and the TF card slot on GPIO4 through GPIO7 is a separate bus.
- **The antenna is a solder change, not a config one.** Moving the resistor from the ceramic antenna to the IPEX Gen 1 connector has no GPIO behind it, so there is no equivalent of the ProS3D's `external_antenna` switch to flip.
- **PSRAM is octal.** The ESP32-S3R8 part carries 8MB in package. Waveshare's own `IO_Test` demo contradicts this by listing GPIO33 through GPIO37 as free GPIO, and those pins are the octal PSRAM bus. Trust the part number and the boot banner over the demo.

### Waveshare ESP32-S3-ETH Camera

[`templates/waveshare-esp32-s3-eth-camera.yaml`][waveshare-camera-template] is an overlay on the board template above, composed as a second `packages:` entry the way the WROOM module templates compose onto [`esp32-s3-devkitc.yaml`][devkitc-template].

- **The power down pin is GPIO8, and Waveshare's pin table omits it.** Without `power_down_pin: GPIO8` the sensor never leaves power down, `esp_camera_init` returns `ESP_ERR_NOT_FOUND`, and `esp32_camera` marks itself failed. This is the first thing to check on any camera failure on this board. The board exposes no camera reset pin.
- **The sensor's register bus is a dedicated `i2c:` list entry**, `id: camera_i2c` on GPIO48 and GPIO47, referenced by `i2c_id`. The `i2c_pins:` shorthand is deprecated and is rejected outright once any `i2c:` block exists anywhere in the merged config, so it is a trap that fires when a device later adds a sensor. It is a list entry rather than the mapping shorthand because `i2c` sets `MULTI_CONF`, and a list merges with a device's own bus where a mapping collides with it.
- **GPIO3, GPIO45, and GPIO46 are strapping pins on the camera bus**, silenced at the pin, see [Strapping Pin Warnings][strapping-pin-warnings].
- **The OV2640 tops out at UXGA.** The larger entries in ESPHome's `FRAME_SIZES` are OV5640 sizes, and the widely copied community config for this board sets `QHD`, a size the OV2640 cannot produce. That same config uses `i2c_pins:` and puts a `switch:` on GPIO8 beside `power_down_pin: GPIO8`, which fails the pin reuse check. Do not re-derive from it.
- **Exposure is left at the ESPHome defaults.** The overlay is a board template and exposure is a property of the room, so a dark image is tuned at the device. Community reports for this board blame `agc_gain_ceiling` defaulting to `2X` rather than the auto exposure, and nothing here has measured that, so treat it as a starting point rather than as a finding.
- **Take the protective film off the lens before judging an image.** The bench frame that prompted the exposure note above was dark for that reason and for no other, which is worth eliminating first since every other explanation costs a reflash.

### RGB LED Status

[`templates/rgb-led-status.yaml`][rgb-led-status-template] derives from [Flo-R1der's package][flo-r1der-link] but does not import it, because that version binds its state to `wifi:` `on_connect` triggers and so cannot run on an Ethernet board.

- **The status source is polled, deliberately.** ESPHome has a `wifi:` `on_connect` and an `ethernet:` `on_connect` but no network-level trigger, and YAML has no conditionals, so no single event-driven form covers both interfaces. A 1s `interval` edge-detects instead and runs the script only on a change.
- **`network::is_connected()` is the interface-agnostic helper.** It resolves Ethernet, modem, WiFi, and OpenThread behind their own `USE_*` defines, so the C++ already does the conditional compilation that the YAML cannot. Its header is in the generated `src/esphome.h` for both WiFi and Ethernet builds, so a lambda needs no include. Do not "fix" this back to a `wifi:` trigger.
- **The API state is read live, never latched into a global.** `api:` accepts `max_connections` clients, so a flag set by `on_client_connected` and cleared by `on_client_disconnected` goes false the moment any one of them leaves and stays false while Home Assistant is still connected. That is a white LED on a device Home Assistant reports online, and the earlier version of this template had exactly that bug. The `api.connected` condition reads `APIServer::is_connected()`, the live connection count, and upstream fires the disconnect trigger *after* removing the client so the condition sees the true state from inside it. The two triggers stay, but only to re-run the script.
- **Any second client is enough to trip it**, a leaked `esphome logs` session included, so see [Logs and the API Connection Cap][api-connection-cap] for reaping them.
- **It is remotely consumable**, needing only the `rgb_led_pin` substitution, so it must stay free of repo-local `!include` entries.
- **It contributes its own `api:` block** for the client triggers and the `api.connected` condition, which enables the API server rather than requiring one. A config composing this package alone validates with an unencrypted API, so an encryption key comes from `api.yaml` or from the composing config.

### Bootloader Age and USB Flashing

An ESP32 flashed before ESP-IDF 5.2 keeps that bootloader through every OTA, because OTA writes the app partition and never the bootloader. ESPHome checks it at boot with `esp_ota_get_bootloader_description()` and warns when the call fails:

```text
[W][app:190]: Bootloader too old for OTA rollback and SRAM1 as IRAM (+40KB). Flash via USB once to update the bootloader
```

- **Every ESP32 variant can report it**, only the wording differs, and the classic ESP32 adds the SRAM1 clause. It is not an ESP8266 concern.
- **Never enable `sram1_as_iram` before the USB flash lands.** ESPHome's own source notes that combination hard bricks the device, recovering only by USB reflash. Take the USB flash first, then the option.
- **A device confirms itself fixed on the next boot** by dropping the warning. The absence of the warning is the test, not the `safe_mode` line below it.
- **`Bootloader rollback: support unknown` is the normal state after a serial flash**, and is not a fault. `safe_mode.cpp` reports it whenever the running partition is `ESP_OTA_IMG_NEW`, which is what `esptool` leaves behind, and only an OTA moves the partition to `ESP_OTA_IMG_PENDING_VERIFY` and the line to `supported`. A freshly USB-flashed device therefore reads `support unknown` with a current bootloader, which is a different state from the old-bootloader `not supported`.
- Checking one means attaching to its logs and restarting it, since the banner prints once at boot. A deep-sleeping device cannot be checked outside its wake window.

### MAX17048 Fuel Gauge

[`templates/max17048.yaml`][max17048-template] carries the gauge for every board that has one, and the ProS3D and Adafruit Feather templates include it as a package. It needs nothing from the including board but an `i2c` bus. The [Option-Zero][option-zero-link] `max17048` external component it wraps is read-only: it reads VCELL, SOC, and CRATE and writes nothing.

The gauge is a ModelGauge part, so it infers state of charge by fitting cell voltage to a model of lithium cell behavior rather than counting charge. It runs that fit once, at **its own** power-on, and it is powered from VBAT. An ESP32 reboot, an OTA, or a `restart` button therefore never re-fits it, and a cell attached after boot is measured against whatever model the gauge fit beforehand.

- **With no cell attached the SOC and rate readings are meaningless**, and the numbers do not look obviously broken forever. The charger oscillates between charge and terminate with nothing to hold the rail, which shows as a fast-blinking charge LED and a bouncing voltage that can exceed LiPo float. SOC saturates above 100 percent and then decays for hours, passing through entirely plausible values on the way down.
- **The `Battery Gauge Reset` button forces the re-fit** by writing the QuickStart bit `0x4000` to the MODE register `0x06`, reaching the chip through `id(battery_gauge)->write_byte_16(...)` because `MAX17048Component` inherits `i2c::I2CDevice` publicly. A successful press shows as a single-sample discontinuity in SOC plus the rate register collapsing toward zero.
- **Press it with the cell resting.** QuickStart fits from the instantaneous terminal voltage, which charge current elevates above the true open-circuit voltage, so a press taken while charging reads optimistic.
- **A long state string is a float32 artifact, not a missing rounding**, and a `round` filter makes it worse. The gauge reports state of charge in 1/256 steps, so `4.12890625` is exactly `1057/256` and survives the API's 32-bit float intact. Rounding that to `4.13` lands on a value binary32 cannot represent, and Home Assistant's double-precision expansion then prints `4.13000011444092`.
- **`accuracy_decimals` reaches Home Assistant as `suggested_display_precision`** and the frontend honors it, so the dashboard already shows two decimals. It is an entity-registry option rather than a state attribute, so read it with the entity registry and do not conclude from its absence in the state attributes that it was never sent.
- **A template reading the raw state bypasses all of that.** A `Battery low ... (4.12890625%)` notification is a defect in the notifying template, which rounds with a Jinja `| round(2)`, not in the device config.
- **A mains-powered device drops the gauge by removing both ids**, `- id: !remove battery_gauge` under `sensor:` and `- id: !remove battery_gauge_reset` under `button:`. Removing only the sensor fails validation, because the button's lambda still references the gauge id. The `external_components` entry survives either way and instantiates nothing.

### SmartHome CeilSense

[`templates/smarthome-ceilsense.yaml`][ceilsense-template] assembles the device from SmartHomeShop's firmware **sub-packages** `github://smarthomeshop/ceilsense/ceilsense-v1/{base.yaml, packages/ld2412.yaml, packages/scd4x.yaml}@main` rather than the vendor's `ceilsense-complete-wifi-ld2412.yaml` entry point.

That entry point also pulls in `wifi.yaml`, whose `on_boot` calls the `ble.disable` action and brings in the Improv and BLE provisioning stack. Because `on_boot` is an un-id'd list, that single action cannot be `!remove`d, so importing the entry point forces a live BLE stack just to satisfy the action. Importing the sub-packages and supplying our own `wifi:` plus boot phase 1 drops Bluetooth entirely, leaving no `esp32_ble`, no Improv, and no captive portal. `base.yaml` and the two sensor packages contain no BLE references.

From `base.yaml` the template then strips the cloud and project machinery: the `http_request` `update:` firmware-update entity, the cloud and local "Firmware Variant" `select` with its glue `script`, the now-pointless `ble_disable_after_boot` switch, and `web_server`. `project: !remove` is safe here, unlike Konnected blaQ, because nothing in the sub-packages references the `ESPHOME_PROJECT_NAME` or `ESPHOME_PROJECT_VERSION` compile-time macros. The Software Version text sensor uses the `${project_version}` *substitution*, which still resolves after the block is gone.

[`garage-presence-sensor.yaml`][garage-presence-sensor] consumes it. It tracks `@main` on a `0.9.0-beta` upstream, so an upstream id rename surfaces as a `Source for removal not found` error at `esphome config`. Re-check the removed ids when that appears, or pin a `@<sha>`. This trades the vendor's maintained variant entry point for hand-assembling its parts, so when upstream restructures `base.yaml` or the packages, re-diff against the current `ceilsense-complete-wifi-ld2412.yaml` to see what changed.

### LD2412 Siting and Tuning

The CeilSense carries an LD2412 24 GHz radar, and every control it offers is expressed in **gates** rather than meters. Distance resolution sets the gate width, so changing it silently redefines what every other control means.

- **Fourteen gates, always, and resolution picks the width.** `0.2m` reaches 2.8 m, `0.5m` reaches 7.0 m, `0.75m` reaches 10.5 m. Choose the narrowest width that still covers the room. A wider gate buys range the room does not have and spends spatial resolution to get it.
- **Measure the room before touching a threshold.** Measure slant range, sensor face to object, because that is the path the radar reports, and a floor-plan distance is not it. A reported return beyond the largest dimension of the room is not in the room, and no amount of threshold tuning makes it real.
- **Bound the radar to the room with `Maximum Distance Gate`.** It is the cheapest control, it needs no firmware change, and it applies to the moving and still paths alike. Reach past the walls and the sensor reports what is past them, because drywall and glass are both effectively transparent at 24 GHz. A glass garage door does not stop the sightline at the door.
- **Changing `Distance Resolution` invalidates any background correction.** The learn is stored per gate, so re-binning leaves it describing bands that no longer exist. Run `Start Dynamic Background Correction` **after** a resolution change, never before. A stale background shows up as a strong still target at a range where nothing is, and it clears the moment a valid learn replaces it.
- **Dynamic background correction needs a static scene for the whole learn**, which runs 50 to 90 seconds. It subtracts static clutter, so it never cancels a moving target, and a learn taken while something moved is worse than no learn at all. Attach to the logs and confirm no moving-target events fall inside the window rather than assuming the room was still.
- **Separate a nuisance from a real target by energy, not by distance.** A real target inside the room saturates move energy at 100 percent, while a nuisance sits in a narrow band well below it. A per-gate move threshold placed between the two removes the nuisance with margin, where a distance cut would cost real coverage.
- **The vendor package exposes no gate thresholds at all**, so tuning one costs a firmware change. The template carries the vendor entity set, and a device that needs thresholds declares them in its own config.
- **Declare all fourteen gates or none.** `LD2412Component::set_gate_threshold()` writes the whole array and dereferences every entry, and its early-out tests `.empty()` on a `std::array`, which is never true. A partial declaration leaves null entries and crashes the device on the first threshold write.

## Linting the Python Utility

The EasyStart BLE monitor under `easystart/python` is a lint-only subtree: ruff gates CI, and pyright is editor parity via Pylance. There is no packaged project, no lockfile, and no test suite, so the script runs and lints through `uvx` with no install step. Use the ruff version pinned in [`test-pull-request.yml`][test-workflow] so a local run matches CI:

```shell
cd easystart/python
uvx ruff@0.15.22 check .
uvx ruff@0.15.22 format --check .
uvx pyright .
```

The generic linters - editorconfig-checker, actionlint, markdownlint, and cspell - are the fleet set, invoked as documented in [`AGENTS.md`][agents] under "Running the Linters Locally". ESPHome config and compile validation is separate, covered above.

## Device Builder Auto-Commits

ESPHome Device Builder's version history feature is **disabled**, and it needs to stay that way.

This directory is the `/config` mount of the running `esphome` container. Device Builder's version history polls the tree for changes in `controllers/_device_scanner.py`, stat-based on `(inode, dev, mtime, size)` rather than inotify, and commits every changed YAML as `Edit <file>.yaml`, authored `ESPHome Device Builder <device-builder@esphome.io>` and unsigned. It shells out to `git -c user.email=... -c commit.gpgsign=false commit --no-verify`, and a command-line `-c` outranks the host gitconfig, so neither the host signing policy nor a hook can stop it. It hit this repository twice: on 2026-07-14, amended away, and on 2026-07-18, five commits, reset and re-committed as `08678ad`.

- It is turned off via "Save version history" in the Device Builder UI, persisted in `.device-builder-preferences.json` as `version_history_enabled: false`. That store is RAM-canonical with a debounced write plus a shutdown flush, so patch the file only while the container is stopped, otherwise use the `config/set_preferences` API, which applies live.
- Were it ever re-enabled, a clean `git status` would no longer prove nothing was committed. After editing files here, run `git log --format='%h %G? %an <%ae>' origin/develop..HEAD` and confirm every commit is signed with `G` and authored `ptr727@users.noreply.github.com`.
- Never push commits that fail that check, and never attribute them to yourself or to the maintainer. Check `%an` and `%ae` before claiming or denying authorship. Such commits are unpushed, so correcting them locally is not a history rewrite.

## Reverse Engineering and External Tooling

BLE and device reverse-engineering work, the Micro-Air EasyStart soft-starter for one, follows [`easystart/BLE-RE-PLAYBOOK.md`][ble-re-playbook]: the agent drives adb, apktool, and jadx and decodes the protocol, while the human only plugs in the phone and runs the BLE monitor. Project-specific notes stay in the project folder, in [`easystart/PROTOCOL.md`][easystart-protocol].

When a CLI tool is needed, look for it first on `PATH`, then in package-manager directories, then for a local copy already in the repository. When it is missing, self-source the official GitHub release or vendor zip locally. Do not auto-run `winget install` or another system package manager: sourcing a portable zip or jar is fine, mutating installed system packages is not. Ask the maintainer when a tool cannot be found or sourced.

## Framework and Platform Versions

- The PlatformIO version is determined by the ESPHome release and cannot be updated independently.
- `framework:` `type:` is either `arduino` or `esp-idf`. Use [`esp-idf`][esp-idf-framework-link] for ESP32 devices.
- `platform_version` specifies the `platformio/espressif32` [version][espressif32-versions-link]. `latest` is not supported, so use an exact version number.
- `version` specifies the `platformio/framework-espidf` [version][framework-espidf-link]. `latest` resolves to the version supported by `platformio/espressif32` at release time, not the current latest version.

## Building Against Patched ESPHome Core Components

Testing a candidate fix to an ESPHome core component does not need a custom image, a venv, or a container change. `external_components` shadows a built-in component of the same name, because `loader.install_meta_finder()` inserts its finder at the front of `sys.meta_path`.

- **Confirm the installed sources match the branch you are patching before trusting the result.** Compare the container's `/opt/venv/lib/python*/site-packages/esphome/components/<name>/` against the upstream ref. When they are identical, a build in the live instance is a valid test of that ref.
- **A git source pulls a fork branch**, and needs `components:` listed explicitly because a full fork exceeds the loader's 100-component limit. Use `refresh: 0s` so an amended branch is re-fetched rather than served from `/cache/data/external_components/`.

  ```yaml
  external_components:
    - source:
        type: git
        url: https://github.com/<owner>/esphome
        ref: <branch>
      components: [ble_client, esp32_ble_client]
      refresh: 0s
  ```

- **A local source is better for iterating**, since it needs no push per attempt. Copy the components out of the image into a path under `/config` and patch them there, then point `type: local` at the parent directory. Copy whole component directories: a stray `.cpp` landing beside the wrong headers fails the build with a confusing missing-header error rather than a path error.
- **Add temporary diagnostics to the core component this way too.** An `ESP_LOGW` inside the code under investigation settles a question that reading the source cannot, and the copy is deleted afterwards.
- **Remember that `esphome upload` does not compile.** After a failed compile it happily flashes the previous binary, so a failed build followed by a successful upload means the device is running the *old* firmware. Check the compile result before reading anything into the device's behavior.

## Contributing Upstream to ESPHome

Core-component fixes are developed in the fork clone at `/home/pieter/esphome-esphome`, whose `origin` is [`ptr727/esphome-esphome`][esphome-fork-link] and whose `upstream` is [`esphome/esphome`][esphome-upstream-link]. An upstream pull request is opened from a branch on the fork, so `git push origin <branch>` is what updates it and nothing is ever pushed to `esphome/esphome` directly. Confirm that with `gh pr view <n> --repo esphome/esphome --json headRepositoryOwner` before assuming a push target.

### Staging on the Fork First

There is **one** fork, renamed from `ptr727/esphome`, so the old name still redirects and `gh` resolves it happily. Do not conclude from that there are two forks. It carries two branch families per change:

- **`fix/<topic>`** is the staging branch, with real working history, opened as a self-PR against the fork's own `dev`. This is where the Copilot round happens.
- **`upstream-<topic>`** is the curated branch that is the actual head of the `esphome/esphome` PR, same tree as its `fix/` counterpart with squashed history.

A change is committed to the `fix/*` branch and reviewed there before it touches the `upstream-*` branch. The fork PR is where Copilot comments without an audience, and it is the only place a bot review can be requested at all. Once the change survives that round, cherry-pick it onto `upstream-*` and push. Prefer adding commits on top of `upstream-*` over a force-push while codeowners are mid-review: ESPHome squash-merges anyway, so tidy history buys nothing and a force-push breaks their review anchors. The two branches carry different histories, so verify the trees agree rather than the commits:

```shell
git diff fix/<topic> upstream-<topic> --stat
```

- **Keep the fork's own `dev` current before branching.** A `fix/*` branch cut from `upstream/dev` while the fork's `dev` lags shows every intervening upstream commit in the fork PR, which drowns the real change and makes a bot review worthless. Fast-forward first: `git fetch upstream dev && git checkout dev && git merge --ff-only upstream/dev && git push origin dev`.
- **Moving the base branch does not always re-diff an open PR.** GitHub recomputes the merge base reliably when the *head* is pushed, not when the *base* moves, so a PR can keep showing the stale diff after the fix. `gh api repos/<o>/<r>/compare/<base>...<head>` reports the true `merge_base_commit` and file list; when that disagrees with `gh pr view --json changedFiles`, close and reopen the PR to force the recompute.

### Fork CI Does Not Run the Real Linters

On a fork's pull requests the lint and build jobs report `Run: skipping`, and `label` and `External component comment` fail outright because they need write tokens a fork does not have. Green-ish checks there mean nothing at all. Run the gates locally from the fork clone, in its venv:

```shell
source venv/bin/activate
script/ci-custom.py
script/build_codeowners.py --check
script/build_language_schema.py --check
script/generate-esp32-boards.py --check
script/generate-rp2-boards.py --check
script/ci_check_duplicate_test_ids.py
script/ci_check_test_fixture_list_form.py
script/clang-format --changed -i
script/clang-tidy --all-headers --changed --environment esp32-idf-tidy
script/clang-tidy --all-headers --changed --environment esp32-arduino-tidy
script/test_build_components.py -c <component>,<component> -t esp32-idf
```

- **`clang-format` reports nothing and rewrites in place**, so confirm it produced no diff rather than reading its exit code as a pass.
- **`clang-tidy-nosplit` is the CI job that covers ESP32**, not the obviously named `clang-tidy-single`, which greps for `USE_ARDUINO` and `USE_ESP8266` and matches zero files in an ESP32 change. The `esp32-idf-tidy` invocation above is what that job runs.
- **The first clang-tidy run builds an ESP-IDF compile database**, about four minutes, and needs clang-tidy 22.1.8 on `PATH`. Later runs reuse the cache.
- **`generate-rp2-boards.py --check` fails with a bare `CalledProcessError` when ruff is missing** from the venv, which reads as a real failure and is not. Install it with `uv pip install ruff`, since plain `pip` hits PEP 668 in a venv without pip.
- **A `tests/components/<x>/test.*.yaml` fixture cannot be compiled directly.** It carries no `esphome:` section because the harness injects one, so go through `test_build_components.py`.
- **`clang-format` does not reflow comments**, but the 120-column limit still applies to them. Check a long comment with `awk 'length > 120'` instead of assuming the formatter would have caught it.

### The `gh` CLI Is Too Old for `gh pr edit`

`gh` is 2.46.0 from the Debian package. `gh pr edit` fetches PR metadata including `projectCards`, a Projects-classic field GitHub has retired, and the API now answers that field with an error rather than null, so the command fails before writing anything:

```text
GraphQL: Projects (classic) is being deprecated in favor of the new Projects experience ... (repository.pullRequest.projectCards)
```

This is a client-version problem and nothing else. It is not the repo-scope rule in [`AGENTS.md`][agents] and not a change in the Copilot or agent instructions: writes aimed at the correct repo succeed, and a read-only probe of `projectCards` by itself reproduces the identical error. Edit a PR body through REST instead, always from a file:

```shell
gh api -X PATCH repos/<owner>/<repo>/pulls/<number> -F body=@body.md
```

The same age accounts for `gh pr checks --json` not existing; poll CI with `gh pr view <n> --json statusCheckRollup` instead. Upgrading `gh` past the Debian package retires both workarounds. Until then, treat any `gh` subcommand failure whose message names a GraphQL field as a version problem to route around, not as a permissions or policy signal, and **verify whether the write landed before retrying it**. In the failures seen so far the PR body was unchanged, so the error came from the lookup that precedes the write, but that is something to confirm each time rather than assume.

### Bot Reviewers

Upstream runs two automated reviewers, and they differ enough to need handling separately.

- **Copilot** (`copilot-pull-request-reviewer`) posts inline threads. **Its low-confidence notes never become threads.** They are folded into a `<details>` block in the review body, so the comments endpoint returns nothing and a review reporting "generated no new comments" can still carry substantive objections. Read the review body itself, via `gh api repos/<o>/<r>/pulls/<n>/reviews`. In one round those suppressed notes were the only findings, and all of them were correct.
- **Filtering REST reviews by the GraphQL login silently returns nothing.** REST reports `copilot-pull-request-reviewer[bot]`, GraphQL reports it without the suffix, so `select(.user.login=="copilot-pull-request-reviewer")` on a REST payload yields an empty list that reads as "no review yet" rather than as a bad filter. Match the API, and cross-check with `gh pr view --json reviews`, which uses the unsuffixed form.
- **Never hand-complete a commit SHA when filtering.** A poll filtered on a full SHA reconstructed from a short one matched nothing and expired silently while the review had in fact landed. Take it from `git rev-parse`, the same rule the [`AGENTS.md`][agents] id policy applies to writes.
- **esphbot** posts a summary comment plus a formal review, quotes replies back point by point, and concedes with evidence when it is wrong. It re-reviews on push by itself, so there is nothing to trigger and nothing to nudge.
- **A review cannot be requested on an upstream PR.** The `requestReviews` mutation answers `FORBIDDEN: ptr727 does not have the correct permissions to execute RequestReviews` on `esphome/esphome`, because an outside contributor cannot assign reviewers. It works on the fork, which is the only place it is needed.
- **Confirm a review covers the current head by commit oid**, never by timestamp, filtering on author and oid together. A thread reply posts as a review authored by the maintainer at the head SHA, which otherwise reads as coverage.

### The Repo's Own AGENTS.md Is the Style Authority

ESPHome carries contributor rules in its own `AGENTS.md`, and they move. Grep it before arguing a style point, in either direction.

- **Config validators need type hints**, `def validate_x(config: ConfigType) -> ConfigType:`, with `ConfigType` imported from `esphome.types`. Older validators in the same file often lack them; new code is still expected to have them.
- **Prefer an existing validator from `config_validation.py`** over a hand-rolled one, composed in `cv.All(...)`. `cv.has_at_most_one_key` is the named choice for mutually-exclusive keys, but it tests key *presence*, so it does not fit a key carrying a schema default, which is always present after validation. When the shared one genuinely does not fit, say why in a comment at the validator, because a reviewer following the same rule will ask.
- **A PR title must start with a `[tag]` prefix**, the component name or `[core]`, and the pull request template must be filled out without removing sections.

### Negative Validation Belongs in a Component Test

A schema rejection is testable, and `tests/component_tests/<component>/` is where it goes. `tests/component_tests/bk72xx_ble_tracker/test_scan_parameter_validation.py` is the model: accepted cases and rejected cases in separate blocks, rejections via `pytest.raises(cv.Invalid, match=...)`.

- **Drive the full platform `CONFIG_SCHEMA`, not the validator function.** Testing the function alone still passes when someone unwires it from the `cv.All` chain, which is the regression worth catching. An autouse `reset_core` fixture clears entity state between tests, but names must still be unique within a single test.
- **Confirm the test can fail.** Temporarily remove the validator from the chain and check that exactly the rejection tests fail. A test that passes both with and without the code under test is not coverage.
- **The venv ships without the test dependencies.** `uv pip install pytest pytest-asyncio pytest-cov pytest-mock`, and run with `--no-cov` unless the coverage args in `pyproject.toml` are wanted.

### Answering a Review

Disagreement lands well when it carries evidence, and both bots have accepted well-supported pushback. Cite file and line as they read at the PR's base commit, not as they read in the working tree, since a diff shifts them. Quote the source that settles the point, and state plainly what was applied and what was declined. Check a style objection against the tree before accepting it: an ask for `override` beside `final` died against 54 bare `) final {` and zero `override final` in the codebase. Never build a comment body in a shell string, see [Repository Tooling Hazards][repository-tooling-hazards].

## Debugging

The steps below run ESPHome outside the live instance, on a workstation, which is how a device gets flashed over USB and how a config gets debugged without touching the running controller.

### VSCode Setup

- Install VSCode.
- Clone this repository and open the workspace.
- Upload `secrets.yaml`.
- Install the recommended extensions from the workspace.
- Associate YAML files with ESPHome, from the ESPHome extension.
- Select the default Python interpreter and create a virtual environment, via Ctrl-Shift-P then Python.
- Install ESPHome in the venv terminal: `pip install --upgrade [--pre] setuptools wheel platformio esphome`.
- Confirm the [ESPHome CLI][esphome-cli-link] is installed: `esphome version`.
- Compile a project: `esphome compile test/esp32-s3-devkitc.yaml`.
- Launch the dashboard with `esphome dashboard .` and open [localhost:6052][dashboard-link].

### Debugging in the DevContainer

- Complete the [VSCode setup][vscode-setup].
- Open the workspace and clone into the devcontainer volume.
- TODO: serial port forwarding configuration.

### Debugging on Windows

- Install Python from the Microsoft Store.
- Complete the [VSCode setup][vscode-setup].
- Compile a project: `esphome compile test/adafruit-esp32-s3-feather.yaml`.
- Plug in the device, holding Boot and pressing Reset when required.
- List COM ports from PowerShell:
  - Serial ports: `[System.IO.Ports.SerialPort]::getportnames()`
  - Microsoft drivers: `Get-CimInstance -Class Win32_SerialPort | Select-Object Name, Description, DeviceID`
  - Custom drivers: `Get-CimInstance -ClassName Win32_PnPEntity | Where-Object { $_.Name -match '.*\(COM(\d)\)' } Select-Object Caption`
- Upload firmware: `esphome run --device COM4 test/adafruit-esp32-s3-feather.yaml`.
- Stream logs: `esphome logs [--device COM5] test/adafruit-esp32-s3-feather.yaml`.

### Debugging on Windows WSL

- Install Ubuntu or Debian from the Microsoft Store.
- Install [USBIPD-WIN][usbipd-link] from [GitHub Releases][usbipd-releases-link].
- Bind the serial port. Open PowerShell as Admin in Terminal, referred to as Windows, and open Ubuntu in Terminal, referred to as WSL.
  - Windows: `usbipd list`, for example `7-1    303a:1001  USB Serial Device (COM4), USB JTAG/serial debug unit          Not shared`
  - Windows: `usbipd bind --busid 7-1`
  - Windows: `usbipd attach --wsl --busid 7-1`
  - WSL: `sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y`
  - WSL: `sudo apt install python3 python3-venv usbutils -y`
  - WSL: `lsusb`, for example `Bus 001 Device 002: ID 303a:1001 Espressif USB JTAG/serial debug unit`
  - WSL: `dmesg | grep tty`, for example `cdc_acm 1-1:1.0: ttyACM0: USB ACM device`
  - WSL: `ls /dev/tty*`, for example `/dev/ttyACM0`, `/dev/ttyUSB0`
- Install VSCode and the Remote Explorer extension.
- Open a VSCode Remote WSL Ubuntu session.
  - Complete the [VSCode setup][vscode-setup] in the remote WSL session.
  - List ports: `ls /dev/tty*`.
  - Upload firmware: `esphome run --device /dev/ttyUSB0 test/esp32-s3-devkitc.yaml`
- Unbind the serial port.
  - Windows: `usbipd detach --busid 7-1`
  - Windows: `usbipd unbind --all`

### Debugging in PlatformIO

- Complete the [VSCode setup][vscode-setup] and install the PlatformIO extension.
- Compile the project with `esphome compile [project]`.
- Launch the PlatformIO extension and open the project folder, for example `./.esphome/build/esp32-s3-test`.
- PlatformIO opens a new instance of VSCode for that project.
- Select the default Python interpreter and create a virtual environment, via Ctrl-Shift-P then Python.
- PlatformIO Core installs into the virtual environment and uses that environment's Python.

## Repository Tooling Hazards

Sharp edges in the tooling around this repository, each one learned by tripping over it.

- **Never build a GitHub comment or reply body inside a double-quoted shell string.** Write it to a file and pass `--body-file`, or `-F body=@file` on a REST call. Backticks in a double-quoted string are command substitution, so a body that mentions a path in code formatting **executes that path**. This is not theoretical: a review reply naming the ruleset apply script in code formatting **executed** it, back when this repository carried its own copy, and that script writes by default, so the posted comment came out with its code spans replaced by command output. Escaping each backtick works and is one missed backslash from repeating the incident. The hazard is the shell's, not that script's, so it survives the copy being retired.
- **The ruleset apply script writes unless told otherwise, and it is hub-hosted rather than carried here.** Run it from a hub checkout and name this repository explicitly, since it otherwise targets whichever repository the shell is sitting in. Its default mode PATCHes repository settings, toggles Dependabot features, and PUTs both branch rulesets. Pass its `check` mode for read-only validation, which is what you almost always want; the payloads it compares against are the committed [`repo-config/`][repo-config] files.
- **Markdown links are reference-style everywhere except [`AGENTS.md`][agents] and `.github/copilot-instructions.md`**, which keep inline links because they are agent-instruction files. Definitions live at the bottom of the file, grouped under `<!-- Repo -->` and `<!-- External -->` and alphabetized within each group. A reference name encodes what it points at, so `analog-max17048-link`, never `analog-en-products-link` after a URL path segment. Removing a link also removes its definition, since an orphan fails the lint.
- **Inline HTML is limited to `<details>` and `<summary>`.** Those two are allowed because a collapsible has no markdown equivalent. Every other element still fails `MD033`, and that includes a `<code>` nested inside a `<summary>` - use a markdown code span there instead.
- **The spell-check gate covers `**/README.md` plus [`DEVICES.md`][devices] and `HISTORY.md`**, wider than the fleet default, so a nested README fails CI like any other. The CI workflow and the `Lint: Spelling` task carry the identical list.
- **The installed `gh` is old enough that `gh pr edit` always fails**, on every repository, and the message names a GraphQL field rather than a permission. See [The `gh` CLI Is Too Old for `gh pr edit`][gh-cli-too-old] for the cause and the REST workaround.
- **A pull request targeting `develop` runs no CI at all.** The workflow triggers are `push` on `develop`, `pull_request` on `main`, and `workflow_dispatch`, so a feature branch aimed at `develop` matches none of them and sits with an empty check list rather than a pending one. That follows from the operational model, where `develop` takes direct signed commits and the push is what runs advisory CI. Dispatch the run by hand when a feature branch needs gating: `gh workflow run test-pull-request.yml --ref <branch>`.
- **A compile job that fails in about 18 seconds is a registry timeout, not a template defect.** The compile jobs pull the [`ptr727/esphome-nonroot`][esphome-nonroot-link] image, and a slow Docker Hub kills the job with `registry-1.docker.io ... context deadline exceeded` before any ESPHome work starts. A real esp-idf compile runs for minutes, so the duration tells the two apart at a glance. Re-run the job rather than reading the template for a fault that is not there.
- **Check an esphome.io link by page title, not HTTP status.** The site answers an unknown path with `200` and a `404 - Page Not Found | ESPHome` title, so a status-code sweep reports a dead link as healthy. The current link form carries no `.html` suffix and no trailing slash, the `guides/configuration-types` anchors have moved to the dedicated [`components/substitutions`][substitutions-link] and [`components/packages`][packages-link] pages, and the per-board pages live on [devices.esphome.io][devices-esphome-link]. An anchor is verified by fetching the page and matching the `id` attribute, since a renamed anchor silently lands the reader at the top of the page.

## Things to Avoid

- Do not claim a config change works until `esphome config`, and where appropriate `esphome compile`, returns success.
- Do not invent enum values, component fields, or framework option names. Grep the component source in the running container when uncertain.
- Do not `!remove` blocks from a vendor package without checking what depends on the ids inside. A missing id surfaces as a compile error, not a config error.
- Do not raise `api: max_connections` to work around leaked logs sessions.
- Do not run an ESPHome CLI command against a host-side install. The container's version is the one that validates and compiles.

<!-- Repo -->

[agents-write-safety]: ./AGENTS.md#repository-boundaries-and-write-safety
[agents]: ./AGENTS.md
[api-connection-cap]: #logs-and-the-api-connection-cap
[apollo-template]: ./templates/apollo-plt-1b.yaml
[ble-issue]: ./easystart/ESPHOME-BLE-ISSUE.md
[ble-re-playbook]: ./easystart/BLE-RE-PLAYBOOK.md
[ceilsense-template]: ./templates/smarthome-ceilsense.yaml
[codestyle]: ./CODESTYLE.md
[common-template]: ./templates/common.yaml
[devices]: ./DEVICES.md
[devkitc-template]: ./templates/esp32-s3-devkitc.yaml
[easystart-protocol]: ./easystart/PROTOCOL.md
[easystart-template]: ./templates/easystart.yaml
[garage-presence-sensor]: ./garage-presence-sensor.yaml
[gh-cli-too-old]: #the-gh-cli-is-too-old-for-gh-pr-edit
[max17048-template]: ./templates/max17048.yaml
[norvi-template]: ./templates/norvi-enet-ae06-r.yaml
[office-bluetooth-proxy]: ./office-bluetooth-proxy.yaml
[readme]: ./README.md
[repo-config]: ./repo-config/
[repository-tooling-hazards]: #repository-tooling-hazards
[rgb-led-status-template]: ./templates/rgb-led-status.yaml
[rgb-led-status]: #rgb-led-status
[secrets-example]: ./secrets._yaml
[secrets-template]: ./templates/secrets.yaml
[strapping-pin-warnings]: #strapping-pin-warnings
[template-notes]: #template-notes
[templates]: ./templates/
[test-workflow]: ./.github/workflows/test-pull-request.yml
[test]: ./test/
[vscode-setup]: #vscode-setup
[waveshare-camera-template]: ./templates/waveshare-esp32-s3-eth-camera.yaml
[waveshare-template]: ./templates/waveshare-esp32-s3-eth.yaml
[wifi-template]: ./templates/wifi.yaml
[workflow]: ./WORKFLOW.md

<!-- External -->

[bluetooth-proxy-link]: https://esphome.io/components/bluetooth_proxy
[dashboard-link]: http://localhost:6052/
[devices-esphome-link]: https://devices.esphome.io
[esp-idf-framework-link]: https://esphome.io/components/esp32#esp-idf-framework
[esphome-cli-link]: https://esphome.io/guides/cli
[esphome-fork-link]: https://github.com/ptr727/esphome-esphome
[esphome-nonroot-link]: https://github.com/ptr727/ESPHome-NonRoot
[esphome-upstream-link]: https://github.com/esphome/esphome
[espressif32-versions-link]: https://registry.platformio.org/platforms/platformio/espressif32/versions
[flo-r1der-link]: https://github.com/Flo-R1der/ESPHome_RGB-Status-LED_Package
[framework-espidf-link]: https://registry.platformio.org/tools/platformio/framework-espidf
[option-zero-link]: https://github.com/Option-Zero/esphome-components
[packages-link]: https://esphome.io/components/packages
[substitutions-link]: https://esphome.io/components/substitutions
[usbipd-link]: https://learn.microsoft.com/en-us/windows/wsl/connect-usb
[usbipd-releases-link]: https://github.com/dorssel/usbipd-win/releases/latest
