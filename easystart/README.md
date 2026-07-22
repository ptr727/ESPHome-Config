# EasyStart <!-- omit from toc -->

Bluetooth protocol for EasyStart AC compressors soft-starters.

## About

I have two [Micro-Air EasyStart](https://www.microair.net/products/easystart-flex-home-ac-soft-starter) 368 (now called Flex) soft-start modules installed for my two HVAC compressors.
I installed these units in 2023 to reduce the inrush current and avoid middle of summer high demand brownouts triggering my server UPSs whenever the compressors turned on.

EasyStart supports a mobile app that connects over Bluetooth and shows status information like inrush current, line frequency, and load current.
I wanted to add this telemetry to Home Assistant, I could not find any existing protocol decoding, I contacted Micro-Air support to ask for the protocol details, they were not forthcoming, and after a while I lost interest.

In the meantime I've been watching [Matt Brown's YouTube Channel](https://www.youtube.com/@mattbrwn) with great info on BT/BLE reverse engineering, and with some spare time and help from Claude, I now have both modules monitored in Home Assistant using an ESPHome Bluetooth Proxy client.

Since completing the reverse engineering I have discovered similar work by [Keen-coffee](https://github.com/Keen-coffee/home_assistant/blob/main/easyStart) and [DerekSeaman](https://github.com/DerekSeaman/ESPHome-Micro-Air-EasyStart) (uses Keen-coffee's protocol).
My decoding adds the byte `[3]` = learned starts value, and I use ESPHome's Python codegen to create the sensor, but the remainder of the protocol decoding is similar.

## Reverse Engineering

### Tools

- Install [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools).
  - `winget install Google.PlatformTools`
- Install [JADX](https://github.com/skylot/jadx/releases/latest).
- Install [apktool](https://github.com/iBotPeaches/Apktool/releases/latest).
- Install [Wireshark](https://www.wireshark.org/download.html).
  - `winget install WiresharkFoundation.Wireshark`
- Install [Java](https://www.oracle.com/java/technologies/downloads/).
  - `winget install Microsoft.OpenJDK.25`
- Install [Claude Code](https://claude.com/product/claude-code).
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
  - See [PROTOCOL.md](./PROTOCOL.md).
- Validate live against a running module:
  - Eyeball the GATT table once in nRF Connect (to confirm which characteristic is write vs notify).
  - Capture with the Python monitor.
    - `uv run python/easystart_monitor.py --discover` to find units
    - `uv run python/easystart_monitor.py --name / --address` to connect.
  - Ground-truth every decoded field against the official app's on-screen numbers.
- Build the ESPHome integration:
  - Use external component, reusable template, and the Bluetooth-proxy config.
  - See [ESPHome integration](#esphome-integration).
- Cross-check against community work.
  - [Keen-coffee](https://github.com/Keen-coffee/home_assistant/blob/main/easyStart)
  - [DerekSeaman](https://github.com/DerekSeaman/ESPHome-Micro-Air-EasyStart)

### Claude Automation

I ran the whole reverse-engineering effort through [Claude Code](https://claude.com/product/claude-code) as the driver.
I started with manual steps learned from my online reverse engineering research, then asking Claude to automate that step, then the next manual step, automate, refine, repeat.
I asked Claude to create AGENTS.md instructions that describe the process allowing for future reuse, and refining the process documentation along the way based on actual work and gotchas.
The final validation was to delete all artifacts I manually created, and have Claude drive the complete protocol reverse engineering effort via a single prompt.
Claude ran every CLI and analysis step itself, `adb`, `pull-apk.sh`, `apktool`, `jadx`, grepping the decompiled source, decoding the byte layout, writing the monitor and the ESPHome component.

The method, the division of labor, and the gotchas are captured so it is repeatable:

- **[AGENTS.md](./AGENTS.md)** - session notes for the next agent:
  - Project status, the validated protocol cheat-sheet, verified tool invocations, and the tool-sourcing policy.
- **[BLE-RE-PLAYBOOK.md](./BLE-RE-PLAYBOOK.md)** - generalized, low-friction RE method:
  - Agent drives `adb`/`apktool`/`jadx`, the human only plugs in the phone and runs the monitor.
  - Reusable for the next BLE device.
- **[tools/pull-apk.sh](./tools/pull-apk.sh)** - one-command APK extraction:
  - Extract APK from phone and save with package name and version.
- **[python/easystart_monitor.py](./python/easystart_monitor.py)** - the `uv`-runnable `bleak`
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

Full detail with the validated byte-offset table is in [PROTOCOL.md](./PROTOCOL.md).

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
See [PROTOCOL.md section 7](./PROTOCOL.md) for the validation table.

- **[`python/easystart_monitor.py`](./python/easystart_monitor.py)** - a `uv`-runnable ([bleak](https://bleak.readthedocs.io/)) monitor that connects over your computer's Bluetooth, polls `ReadLive`, and prints each frame raw + decoded in real time. See [`python/README.md`](./python/README.md).

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

- [`components/easystart/easystart.h`](./components/easystart/easystart.h) - the C++ component (BLE + frame parsing).
- [`components/easystart/__init__.py`](./components/easystart/__init__.py) - ESPHome codegen / config schema (one instance per module).

Wire it into a Bluetooth proxy with the reusable template [`../templates/easystart.yaml`](../templates/easystart.yaml) (include once per module, with `vars` for the MAC + label).
A complete two-module example is [`../office-bluetooth-proxy.yaml`](../office-bluetooth-proxy.yaml). The office proxy sits near the HVAC units and attaches both compressors. Place the proxy close to the units: EasyStart BLE is very short range, it would not connect from across the room and needed the proxy relocated near the modules; an external-antenna ESP32 helps if the signal is marginal.

Two connection notes learned on hardware:

- The active `bluetooth_proxy` reserves 3 connection slots, so a proxy hosting two modules needs `esp32_ble: max_connections: 5` (3 + 2). Changing it requires a clean rebuild.
- The device's `api:` accepts a limited number of clients (5 on ESP32). Home Assistant and the ESPHome dashboard each hold one, so avoid leaving extra `esphome logs` sessions open or new clients get rejected.

The frame decode is logged at INFO (the `state=... current=...` line) and the raw hex frames at DEBUG. This repo's shared `logger.yaml` runs at DEBUG, so both are visible in `esphome logs` with no per-device override.

## References

- Ordered August 2023 (old product name): EasyStart 368 / ASY-368-X48-BLUE.
- [EasyStart Flex](https://www.micro-air.com/support-documents/installation_resources/EasyStart_Specification_Sheet.pdf)
- [EasyStart Flex Home AC Soft Starter / ASY-398-X1S-BL](https://www.microair.net/products/easystart-flex-home-ac-soft-starter)
- [EasyStart Home AC Wiring](https://www.micro-air.com/support-documents/residential/current/EasyStart_HomeResidential_Installation_Guide.pdf)
- [Bluetooth Operation Manual](https://www.micro-air.com/support-documents/installation_resources/EasyStart_Bluetooth_Manual.pdf)
- [Google Play EasyStart App](https://play.google.com/store/apps/details?id=net.microair.easystart&hl=en_US)
- [Matt Brown's YouTube Channel](https://www.youtube.com/@mattbrwn)
- [Reddit Thread](https://www.reddit.com/r/homeassistant/comments/1dm00lg/integration_for_microair_easystart/)
- [Keen-coffee GitHub](https://github.com/Keen-coffee/home_assistant/blob/main/easyStart)
- [DerekSeaman GitHub](https://github.com/DerekSeaman/ESPHome-Micro-Air-EasyStart)
- [ESPHome BLE Client](https://esphome.io/components/ble_client/)

## License

See [LICENSE][license].

[license]: ../LICENSE
