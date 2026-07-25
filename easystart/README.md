# EasyStart <!-- omit from toc -->

Bluetooth protocol for EasyStart AC compressors soft-starters.

## About

I have two [Micro-Air EasyStart][microair-products-easystart-flex-home-ac-soft-starter-link] 368 (now called Flex) soft-start modules installed for my two HVAC compressors.
I installed these units in 2023 to reduce the inrush current and avoid middle of summer high demand brownouts triggering my server UPSs whenever the compressors turned on.

EasyStart supports a mobile app that connects over Bluetooth and shows status information like inrush current, line frequency, and load current.
I wanted to add this telemetry to Home Assistant, I could not find any existing protocol decoding, I contacted Micro-Air support to ask for the protocol details, they were not forthcoming, and after a while I lost interest.

In the meantime I've been watching [Matt Brown's YouTube Channel][youtube-mattbrwn-link] with great info on BT/BLE reverse engineering, and with some spare time and help from Claude, I now have both modules monitored in Home Assistant using an ESPHome Bluetooth Proxy client.

Since completing the reverse engineering I have discovered similar work by [Keen-coffee][github-keen-coffee-home-assistant-link] and [DerekSeaman][github-derekseaman-esphome-micro-air-easystart-link] (uses Keen-coffee's protocol).
My decoding adds the byte `[3]` = learned starts value, and I use ESPHome's Python codegen to create the sensor, but the remainder of the protocol decoding is similar.

## Reverse Engineering

### Tools

- Install [Android Platform Tools][developer-tools-releases-link].
  - `winget install Google.PlatformTools`
- Install [JADX][github-skylot-jadx-link].
- Install [apktool][github-ibotpeaches-apktool-link].
- Install [Wireshark][wireshark-download-link].
  - `winget install WiresharkFoundation.Wireshark`
- Install [Java][oracle-java-technologies-link].
  - `winget install Microsoft.OpenJDK.25`
- Install [Claude Code][claude-product-claude-code-link].
  - `winget install Anthropic.ClaudeCode`
- Android phone.
- Computer with physical proximity near the EasyStart modules, their BT range is very limited.

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
  - Capture with the Python monitor.
    - `uv run python/easystart_monitor.py --discover` to find units
    - `uv run python/easystart_monitor.py --name / --address` to connect.
  - Ground-truth every decoded field against the official app's on-screen numbers.
- Build the ESPHome integration:
  - Use external component, reusable template, and the Bluetooth-proxy config.
  - See [ESPHome integration][esphome-integration].
- Cross-check against community work.
  - [Keen-coffee][github-keen-coffee-home-assistant-link]
  - [DerekSeaman][github-derekseaman-esphome-micro-air-easystart-link]

### Claude Automation

I ran the whole reverse-engineering effort through [Claude Code][claude-product-claude-code-link] as the driver.
I started with manual steps learned from my online reverse engineering research, then asking Claude to automate that step, then the next manual step, automate, refine, repeat.
I asked Claude to create AGENTS.md instructions that describe the process allowing for future reuse, and refining the process documentation along the way based on actual work and gotchas.
The final validation was to delete all artifacts I manually created, and have Claude drive the complete protocol reverse engineering effort via a single prompt.
Claude ran every CLI and analysis step itself, `adb`, `pull-apk.sh`, `apktool`, `jadx`, grepping the decompiled source, decoding the byte layout, writing the monitor and the ESPHome component.

The method, the division of labor, and the gotchas are captured so it is repeatable:

- **[AGENTS.md][agents]** - session notes for the next agent:
  - Project status, the validated protocol cheat-sheet, verified tool invocations, and the tool-sourcing policy.
- **[BLE-RE-PLAYBOOK.md][ble-re-playbook]** - generalized, low-friction RE method:
  - Agent drives `adb`/`apktool`/`jadx`, the human only plugs in the phone and runs the monitor.
  - Reusable for the next BLE device.
- **[tools/pull-apk.sh][pull-apk]** - one-command APK extraction:
  - Extract APK from phone and save with package name and version.
- **[python/easystart_monitor.py][easystart-monitor]** - the `uv`-runnable `bleak`
  monitor:
  - Discover EasyStart devices with the `--discover` command.
  - Connect to and monitor devices with `--name` or `--address` command.

For static analysis Claude also fans work out to sub-agents (e.g. an `Explore` agent to sweep the decompiled tree for UUIDs and characteristic handles) so the search stays fast without dumping whole files into the main context.

The kickoff was essentially one prompt, from there the agent drove end to end:

> I have the Micro-Air EasyStart app installed on my Android phone, developer options and USB debugging are on, and it's plugged into this computer.
> Extract the APK, decompile it, and reverse-engineer its Bluetooth protocol.
> Then write me a `uv`-runnable `bleak` monitor to validate the decode against the live module.
> And finally write an ESPHome `ble_client` component to expose it to Home Assistant.

### Protocol Summary

Full detail with the validated byte-offset table is in [PROTOCOL.md][protocol].

- Transport is the **Laird VSP** service `d973f2e0-...`, no pairing / PIN / handshake:
  - `d973f2e1-...` = **notify** characteristic (module -> host, has the `0x2902` CCCD)
  - `d973f2e2-...` = **write** characteristic (host -> module, write-no-response)
  - Note: `e1`/`e2` are the opposite of the usual Laird convention - confirmed via nRF Connect.
- Poll by writing the ASCII string `{"Cmd": ReadLive}` to the write characteristic.
- Each poll yields two notifications on the notify characteristic:
  - An **18-byte binary live frame**.
  - And an ASCII `{"Sts": Success}` acknowledgment.
- Live-frame highlights (little-endian):
  - `[2]` = system/fault state,
  - `[4]+[5]*256 /10` = **live current (A)** (the compressor power signal),
  - `[6]+[7]*256` -> `500000 / value` = line frequency (Hz),
  - `[8]+[9]*256 /10` = last-start peak (A),
  - `[14...17]` (u32) = total starts.
- The module powers its BLE radio only **while the compressor runs**, so BLE presence itself is a reliable running/off signal.

To locate this in the decompiled app, the key classes are:

- `Status` / `Status$onCreateView$$inlined$scheduleAtFixedRate$1` - polls `ReadLive`, parses the live frame (byte offsets -> current, state, frequency, counters).
- `MainActivityKt$gattCallBack$1` - GATT callback; response framing and buffer accumulation.
- `Connect` - connection sequence, service/characteristic discovery, notify subscription.

### Live Validation (nRF Connect + Python monitor)

The decode was confirmed end-to-end against real modules.
Every field matched the official app's on-screen values (current, last-start-peak `24.5 A`, line frequency `59.8 Hz`, total starts `4947`).\
See [PROTOCOL.md section 7][protocol] for the validation table.

- **[`python/easystart_monitor.py`][easystart-monitor]** - a `uv`-runnable ([bleak][bleak-link]) monitor that connects over your computer's Bluetooth, polls `ReadLive`, and prints each frame raw + decoded in real time. See [`python/README.md`][python-readme].

  ```shell
  uv run python/easystart_monitor.py --discover              # discover your units (name + MAC)
  uv run python/easystart_monitor.py --name EasyStart_XXXX   # monitor one
  ```

- Real device MACs are kept out of the repo, discover your own with `--discover` and store them only in the git-ignored ESPHome `secrets.yaml` (read by `office-bluetooth-proxy.yaml` via `!secret`).
- Only one BLE central can connect at a time - close the phone app before running the monitor.

#### Note: HCI snoop logs are filtered on stock Pixel

On a stock (non-rooted) Pixel, "Enable Bluetooth HCI snoop log" runs in `FILTERED` mode (`SnoopLogMode=FILTERED`), which truncates ATT payloads.
The `bugreport`'s `btsnooz_hci.log` keeps only the first few bytes of each notification, so the live current/frequency bytes are lost.
It does still confirm the characteristic handles and that a write of `{"Cmd": ReadLive}` occurs, but for full payloads use nRF Connect or the Python monitor above.
An unfiltered `btsnoop_hci.log` would need root or a different device.

## ESPHome Integration

A hardware-validated ESPHome external component (uses `ble_client`, derives compressor-running from the BLE connection, publishes current, an estimated power (`current * line_voltage * power_factor`,
defaults 240 V / 1.0), line frequency, last-start peak, short-cycle delay, system state, and start/fault/learned-start counters). Flashed on a GL-S10 proxy and confirmed against both live modules: both clients connect, every decoded field matches, and both `running` sensors report `on` in Home Assistant:

- [`components/easystart/easystart.h`][easystart-header] - the C++ component (BLE + frame parsing).
- [`components/easystart/__init__.py`][init] - ESPHome codegen / config schema (one instance per module).

Wire it into a Bluetooth proxy with the reusable template [`../templates/easystart.yaml`][easystart-template] (include once per module, with `vars` for the MAC + label).
A complete two-module example is [`../office-bluetooth-proxy.yaml`][office-bluetooth-proxy]. The office proxy sits near the HVAC units and attaches both compressors. Place the proxy close to the units: EasyStart BLE is very short range, it would not connect from across the room and needed the proxy relocated near the modules; an external-antenna ESP32 helps if the signal is marginal.

The template also adds a **signal-strength diagnostic** per module, using ESPHome's built-in [`ble_client` RSSI sensor][esphome-components-sensor-link] (`type: rssi`, `entity_category: diagnostic`, default 60s). It reads the RSSI of the **live connection** (`esp_ble_gap_read_rssi`), not of advertisements, which matters because a module stops advertising once connected. It reads blank while disconnected (which on its own does not separate "compressor off" from "out of range", since `running` is also derived from BLE presence). Its value is the **link margin while connected**: around -60 dBm is healthy, and approaching -90 dBm means the link is barely viable, which is what turns an intermittent "everything unavailable" into a diagnosable placement problem. The office proxy measured -93 dBm on a live connection, effectively at the sensitivity floor. Use it to site a proxy, dropping `easystart_rssi_update_interval` to a few seconds while walking the location.

Two connection notes learned on hardware:

- The active `bluetooth_proxy` reserves 3 connection slots, so a proxy hosting two modules needs `esp32_ble: max_connections: 5` (3 + 2). Changing it requires a clean rebuild. The RSSI sensor attaches to an existing `ble_client` and does not consume an extra slot.
- The device's `api:` accepts a limited number of clients (5 on ESP32). Home Assistant and the ESPHome dashboard each hold one, so avoid leaving extra `esphome logs` sessions open or new clients get rejected.

The frame decode is logged at INFO (the `state=... current=...` line) and the raw hex frames at DEBUG. This repo's shared `logger.yaml` runs at DEBUG, so both are visible in `esphome logs` with no per-device override.

## References

- Ordered August 2023 (old product name): EasyStart 368 / ASY-368-X48-BLUE.
- [EasyStart Flex][easystart-spec-sheet-link]
- [EasyStart Flex Home AC Soft Starter / ASY-398-X1S-BL][microair-products-easystart-flex-home-ac-soft-starter-link]
- [EasyStart Home AC Wiring][micro-air-support-documents-residential-link]
- [Bluetooth Operation Manual][easystart-bluetooth-manual-link]
- [Google Play EasyStart App][play-store-apps-link]
- [Matt Brown's YouTube Channel][youtube-mattbrwn-link]
- [Reddit Thread][reddit-r-homeassistant-link]
- [Keen-coffee GitHub][github-keen-coffee-home-assistant-link]
- [DerekSeaman GitHub][github-derekseaman-esphome-micro-air-easystart-link]
- [ESPHome BLE Client][esphome-components-ble-client-link]

## License

See [LICENSE][license].

<!-- Repo -->

[agents]: ./AGENTS.md
[ble-re-playbook]: ./BLE-RE-PLAYBOOK.md
[easystart-header]: ./components/easystart/easystart.h
[easystart-monitor]: ./python/easystart_monitor.py
[easystart-template]: ../templates/easystart.yaml
[esphome-integration]: #esphome-integration
[init]: ./components/easystart/__init__.py
[license]: ../LICENSE
[office-bluetooth-proxy]: ../office-bluetooth-proxy.yaml
[protocol]: ./PROTOCOL.md
[pull-apk]: ./tools/pull-apk.sh
[python-readme]: ./python/README.md

<!-- External -->

[bleak-link]: https://bleak.readthedocs.io/
[claude-product-claude-code-link]: https://claude.com/product/claude-code
[developer-tools-releases-link]: https://developer.android.com/tools/releases/platform-tools
[easystart-bluetooth-manual-link]: https://www.micro-air.com/support-documents/installation_resources/EasyStart_Bluetooth_Manual.pdf
[easystart-spec-sheet-link]: https://www.micro-air.com/support-documents/installation_resources/EasyStart_Specification_Sheet.pdf
[esphome-components-ble-client-link]: https://esphome.io/components/ble_client/
[esphome-components-sensor-link]: https://esphome.io/components/sensor/ble_client/
[github-derekseaman-esphome-micro-air-easystart-link]: https://github.com/DerekSeaman/ESPHome-Micro-Air-EasyStart
[github-ibotpeaches-apktool-link]: https://github.com/iBotPeaches/Apktool/releases/latest
[github-keen-coffee-home-assistant-link]: https://github.com/Keen-coffee/home_assistant/blob/main/easyStart
[github-skylot-jadx-link]: https://github.com/skylot/jadx/releases/latest
[micro-air-support-documents-residential-link]: https://www.micro-air.com/support-documents/residential/current/EasyStart_HomeResidential_Installation_Guide.pdf
[microair-products-easystart-flex-home-ac-soft-starter-link]: https://www.microair.net/products/easystart-flex-home-ac-soft-starter
[oracle-java-technologies-link]: https://www.oracle.com/java/technologies/downloads/
[play-store-apps-link]: https://play.google.com/store/apps/details?id=net.microair.easystart&hl=en_US
[reddit-r-homeassistant-link]: https://www.reddit.com/r/homeassistant/comments/1dm00lg/integration_for_microair_easystart/
[wireshark-download-link]: https://www.wireshark.org/download.html
[youtube-mattbrwn-link]: https://www.youtube.com/@mattbrwn
