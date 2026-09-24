# EasyStart <!-- omit from toc -->

Bluetooth protocol, BLE monitor, and ESPHome integration for the Micro-Air EasyStart AC compressor soft-starter.

## About

The [Micro-Air EasyStart][microair-products-easystart-flex-home-ac-soft-starter-link] soft-starter (the EasyStart 368, ASY-368-X48-BLUE, now sold as the EasyStart Flex, ASY-398-X1S-BL) limits compressor inrush current and reports status over Bluetooth LE to a vendor mobile app: live current, line frequency, last-start peak current, fault state, and start counters.

This folder holds:

- The reverse-engineered BLE protocol, [PROTOCOL.md][protocol].
- A reusable, agent-driven BLE reverse-engineering method, [BLE-RE-PLAYBOOK.md][ble-re-playbook].
- A command-line BLE monitor for validating the decode from a computer, see [BLE Monitor](#ble-monitor).
- An ESPHome external component that exposes the telemetry to Home Assistant through a Bluetooth proxy, see [ESPHome Integration](#esphome-integration).

## Reverse Engineering

### Tools

- Install [Android Platform Tools][android-platform-tools-link].
  - `winget install Google.PlatformTools`
- Install [JADX][github-skylot-jadx-link].
- Install [apktool][github-ibotpeaches-apktool-link].
- Install [Wireshark][wireshark-download-link].
  - `winget install WiresharkFoundation.Wireshark`
- Install [Java][oracle-java-technologies-link].
  - `winget install Microsoft.OpenJDK.25`
- Install [uv][docs-uv-link], see [BLE Monitor](#ble-monitor).
- Install [Claude Code][claude-product-claude-code-link], to drive the process per the [playbook][ble-re-playbook].
  - `winget install Anthropic.ClaudeCode`
- Android phone.
- Computer in physical proximity to the EasyStart modules, since their BLE range is very limited.

### Process

- Enable Android developer options:
  - Settings -> About phone
    - Tap Build number 7 times
  - Settings -> System -> Developer options
    - Enable USB debugging
  - Plug the phone into the computer and approve the one-time USB-debugging prompt.
- Extract the APK from the phone.
  - `tools/pull-apk.sh easystart` -> `net.microair.easystart-<version>.apk`.
- Decompile the APK.
  - `apktool d <apk> -o app-apktool` -> smali + resources.
  - `jadx <apk> -d app-jadx` -> readable Java.
- Statically analyze the decompiled source:
  - Grep for the service / characteristic **UUIDs**, `writeCharacteristic` / `onCharacteristicChanged`, and the command / response strings and byte-offset parsing.
  - This alone yields the transport, the `{"Cmd": ReadLive}` command, and the 18-byte frame layout, before touching any hardware.
  - See [PROTOCOL.md][protocol].
- Validate live against a running module:
  - Eyeball the GATT table once in nRF Connect (to confirm which characteristic is write vs notify).
  - Capture with the [BLE monitor](#ble-monitor).
  - Ground-truth every decoded field against the official app's on-screen numbers.
- Build the ESPHome integration:
  - Use external component, reusable template, and the Bluetooth-proxy config.
  - See [ESPHome integration][esphome-integration].
- Cross-check against community work.
  - [Keen-coffee][github-keen-coffee-home-assistant-link]
  - [DerekSeaman][github-derekseaman-esphome-micro-air-easystart-link]

### Tooling

- **[BLE-RE-PLAYBOOK.md][ble-re-playbook]** - generalized, agent-driven RE method:
  - The agent drives `adb`/`apktool`/`jadx`, the human only plugs in the phone and runs the monitor.
  - Reusable for other BLE devices.
- **[tools/pull-apk.sh][pull-apk]** - one-command APK extraction:
  - Extract APK from phone and save with package name and version.
- **[easystart_monitor][easystart-monitor]** - the `bleak` BLE monitor, see [BLE Monitor](#ble-monitor).

### Decompiled App Classes

To locate the protocol in the decompiled app, the key classes are:

- `Status` and `Status$onCreateView$$inlined$scheduleAtFixedRate$1` poll `ReadLive` and parse the live frame (byte offsets -> current, state, frequency, counters).
- `MainActivityKt$gattCallBack$1` is the GATT callback, covering response framing and buffer accumulation.
- `Connect` is the connection sequence, service and characteristic discovery, and notify subscription.

## Protocol Summary

Full detail with the validated byte-offset table is in [PROTOCOL.md][protocol].

- Transport is the **Laird VSP** service `d973f2e0-...`, no pairing / PIN / handshake:
  - `d973f2e1-...` = **notify** characteristic (module -> host, has the `0x2902` CCCD)
  - `d973f2e2-...` = **write** characteristic (host -> module, write-no-response)
  - Note: `e1` and `e2` are the opposite of the usual Laird convention, confirmed via nRF Connect.
- Poll by writing the ASCII string `{"Cmd": ReadLive}` to the write characteristic.
- Each poll yields two notifications on the notify characteristic:
  - An **18-byte binary live frame**.
  - And an ASCII `{"Sts": Success}` acknowledgment.
- Live-frame highlights (little-endian):
  - `[2]` = system/fault state,
  - `[3]` = learned starts, which the community decodes do not read,
  - `[4]+[5]*256 /10` = **live current (A)** (the compressor power signal),
  - `[6]+[7]*256` -> `500000 / value` = line frequency (Hz),
  - `[8]+[9]*256 /10` = last-start peak (A),
  - `[14...17]` (u32) = total starts.
- The module powers its BLE radio only **while the compressor runs**, so BLE presence itself is a reliable running/off signal.
- Every decoded field matches the official app's on-screen values, see [PROTOCOL.md section 7][protocol].

## BLE Monitor

[`easystart_monitor`][easystart-monitor] is a [bleak][bleak-link] monitor that connects to a module over the computer's Bluetooth, polls `{"Cmd": ReadLive}`, and prints each frame raw and decoded in real time.
It validates the protocol without flashing ESPHome firmware.
It is a member of the repository's uv workspace, so [uv][docs-uv-link] is the only requirement, and `uv run` installs Python, `bleak`, and the monitor on first use.

Install uv:

- Windows: `winget install astral-sh.uv`
- macOS: `brew install uv`
- Linux or macOS: `curl -LsSf https://astral.sh/uv/install.sh | sh`

Run from anywhere in the repository:

```shell
uv run easystart-monitor --discover             # list EasyStart_* units (name + MAC or UUID), then exit
uv run easystart-monitor --name EasyStart_A1B2  # pick a unit by advertised name (macOS)
uv run easystart-monitor --address <mac|uuid>   # pick by MAC (Windows) / UUID (macOS)
uv run easystart-monitor --interval 0.5         # poll period in seconds (default 1.0)
uv run easystart-monitor --raw                  # raw bytes only, no decode
uv run easystart-monitor --once                 # exit after the first disconnect
```

- Start with **`--discover`** to find your own units.
  It scans for `EasyStart_*` devices (or the Laird VSP service) and prints each one's name, MAC or UUID, and signal.
  The monitor hard-codes no addresses, and `EasyStart_A1B2` above is a made-up placeholder.
- With more than one module, pass `--name` or `--address`, since a bare run connects to the first one seen.
- The **compressor must be running**, because the module powers its BLE radio only while on.
  The monitor scans until the module appears and reconnects automatically after each compressor cycle.
- **Close the phone app first**, because only one BLE central can connect at a time.
- Store real device MACs only in the git-ignored ESPHome `secrets.yaml` (read by `hvac-compressor-sensor.yaml` via `!secret`), never in the repository.

Each sample prints the raw bytes, a per-index breakdown (`[4]=137/0x89 ...`), and the decoded values.
Compare the decoded current, frequency, and state against the official app to confirm the byte offsets and scaling.
For validation, capture a few samples at steady run and one right after a compressor start, when the current changes.

macOS:

- The first run prompts for Bluetooth permission.
  Grant the terminal app Bluetooth access under **System Settings -> Privacy & Security -> Bluetooth**, then restart the terminal.
- macOS hides the hardware MAC, so devices are identified by a CoreBluetooth **UUID**.
  Use `--name`, or pass the UUID the scan prints to `--address`.

HCI snoop logs are not a substitute: on a stock (non-rooted) Pixel, "Enable Bluetooth HCI snoop log" runs in `FILTERED` mode (`SnoopLogMode=FILTERED`), and the `bugreport` `btsnooz_hci.log` keeps only the first few bytes of each ATT payload.
It confirms the characteristic handles and the `{"Cmd": ReadLive}` write, but loses the live current and frequency bytes, so use the monitor or nRF Connect for full payloads.

## ESPHome Integration

A hardware-validated ESPHome external component uses `ble_client`, derives compressor-running from the BLE connection, and publishes current, an estimated power (`current * line_voltage * power_factor`, defaults 240 V / 1.0), line frequency, last-start peak, short-cycle delay, system state, and start/fault/learned-start counters:

- [`components/easystart/easystart.h`][easystart-header] is the C++ component, covering BLE and frame parsing.
- [`components/easystart/__init__.py`][easystart-init] is the ESPHome codegen and config schema, one instance per module.

Wire it into a Bluetooth proxy with the reusable template [`../templates/easystart.yaml`][easystart-template] (include once per module, with `vars` for the MAC + label).
A complete two-module example is [`../hvac-compressor-sensor.yaml`][hvac-compressor-sensor], a dedicated proxy sited at the units that attaches both compressors.
EasyStart BLE is very short range, so place the proxy close to the modules, and use an external-antenna ESP32 if the signal is marginal.

The template also adds a **signal-strength diagnostic** per module, using ESPHome's built-in [`ble_client` RSSI sensor][esphome-ble-client-sensor-link] (`type: rssi`, `entity_category: diagnostic`, default 60s).
It reads the RSSI of the **live connection** (`esp_ble_gap_read_rssi`), not of advertisements, which matters because a module stops advertising once connected.
It publishes NAN on disconnect, so Home Assistant reads `unknown` rather than a stale value (which on its own does not separate "compressor off" from "out of range", since `running` is also derived from BLE presence).
Its value is the **link margin while connected**: around -60 dBm is healthy, and approaching -90 dBm means the link is barely viable, which turns an intermittent "everything unavailable" into a diagnosable placement problem.
Use it to site a proxy, dropping `easystart_rssi_update_interval` to a few seconds while walking the location.

Connection notes:

- The active `bluetooth_proxy` reserves 3 connection slots, so a proxy hosting two modules needs `esp32_ble: max_connections: 5` (3 + 2). Changing it requires a clean rebuild. The RSSI sensor attaches to an existing `ble_client` and does not consume an extra slot.
- The device's `api:` accepts a limited number of clients (5 on ESP32). Home Assistant and the ESPHome dashboard each hold one, so avoid leaving extra `esphome logs` sessions open or new clients get rejected.

The frame decode is logged at INFO (the `state=... current=...` line) and the raw hex frames at DEBUG. This repo's shared `logger.yaml` runs at DEBUG, so both are visible in `esphome logs` with no per-device override.

## References

- [EasyStart Flex][easystart-spec-sheet-link]
- [EasyStart Flex Home AC Soft Starter / ASY-398-X1S-BL][microair-products-easystart-flex-home-ac-soft-starter-link]
- [EasyStart Home AC Wiring][micro-air-support-documents-residential-link]
- [Bluetooth Operation Manual][easystart-bluetooth-manual-link]
- [Google Play EasyStart App][play-store-easystart-link]
- [Reddit Thread][reddit-r-homeassistant-link]
- [Keen-coffee GitHub][github-keen-coffee-home-assistant-link]
- [DerekSeaman GitHub][github-derekseaman-esphome-micro-air-easystart-link]
- [ESPHome BLE Client][esphome-components-ble-client-link]

## License

See [LICENSE][license].

<!-- Repo -->

[ble-re-playbook]: ./BLE-RE-PLAYBOOK.md
[easystart-header]: ./components/easystart/easystart.h
[easystart-init]: ./components/easystart/__init__.py
[easystart-monitor]: ./python/src/easystart_monitor/monitor.py
[easystart-template]: ../templates/easystart.yaml
[esphome-integration]: #esphome-integration
[hvac-compressor-sensor]: ../hvac-compressor-sensor.yaml
[license]: ../LICENSE
[protocol]: ./PROTOCOL.md
[pull-apk]: ./tools/pull-apk.sh

<!-- External -->

[android-platform-tools-link]: https://developer.android.com/tools/releases/platform-tools
[bleak-link]: https://bleak.readthedocs.io/
[claude-product-claude-code-link]: https://claude.com/product/claude-code
[docs-uv-link]: https://docs.astral.sh/uv/
[easystart-bluetooth-manual-link]: https://www.micro-air.com/support-documents/installation_resources/EasyStart_Bluetooth_Manual.pdf
[easystart-spec-sheet-link]: https://www.micro-air.com/support-documents/installation_resources/EasyStart_Specification_Sheet.pdf
[esphome-ble-client-sensor-link]: https://esphome.io/components/sensor/ble_client/
[esphome-components-ble-client-link]: https://esphome.io/components/ble_client/
[github-derekseaman-esphome-micro-air-easystart-link]: https://github.com/DerekSeaman/ESPHome-Micro-Air-EasyStart
[github-ibotpeaches-apktool-link]: https://github.com/iBotPeaches/Apktool/releases/latest
[github-keen-coffee-home-assistant-link]: https://github.com/Keen-coffee/home_assistant/blob/main/easyStart
[github-skylot-jadx-link]: https://github.com/skylot/jadx/releases/latest
[micro-air-support-documents-residential-link]: https://www.micro-air.com/support-documents/residential/current/EasyStart_HomeResidential_Installation_Guide.pdf
[microair-products-easystart-flex-home-ac-soft-starter-link]: https://www.microair.net/products/easystart-flex-home-ac-soft-starter
[oracle-java-technologies-link]: https://www.oracle.com/java/technologies/downloads/
[play-store-easystart-link]: https://play.google.com/store/apps/details?id=net.microair.easystart&hl=en_US
[reddit-r-homeassistant-link]: https://www.reddit.com/r/homeassistant/comments/1dm00lg/integration_for_microair_easystart/
[wireshark-download-link]: https://www.wireshark.org/download.html
