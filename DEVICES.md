# ESPHome Devices

The devices I run in my own home automation setup.

Each per-device config lives in the repository root, one per physical device. Each sets `substitutions:` (device name, friendly name, and any per-device overrides) and pulls in a [template][templates] via `packages:`.

## Plant Sensors (Apollo PLT-1B)

- [`music-room-plant-sensor.yaml`][music-room-plant-sensor], [`patio-plant-sensor.yaml`][patio-plant-sensor], [`stairs-plant-sensor.yaml`][stairs-plant-sensor], and [`upstairs-hallway-plant-sensor.yaml`][upstairs-hallway-plant-sensor] use the [Apollo PLT-1B template][apollo-plt-1b].

## Garage Presence and Air Sensor (CeilSense)

- [`garage-presence-sensor.yaml`][garage-presence-sensor] uses the [SmartHomeShop CeilSense template][smarthome-ceilsense] for presence, CO2, temperature, humidity, lux, and pressure in the garage.

## Garage Door Controller (Konnected blaQ)

- [`garage-door-controller.yaml`][garage-door-controller] uses the [Konnected blaQ template][konnected-blaq].
- Note: currently powered off pending an upstream investigation into self-opening incidents, see the status block in the config and [issue #29][issue-29-link].

## Bluetooth Proxies

- [`office-bluetooth-proxy.yaml`][office-bluetooth-proxy] uses the [Waveshare ESP32-S3-ETH template][waveshare-esp32-s3-eth], adding the `esp32_ble_tracker` and `bluetooth_proxy` blocks the board template leaves to the device. It is powered over PoE, so a single Ethernet run carries both power and network.
- The enclosure is Fabrion365's [Waveshare ESP32-S3-ETH PoE case][makerworld-esp32-s3-eth-poe-case-link] on MakerWorld.
- [`pantry-bluetooth-proxy.yaml`][pantry-bluetooth-proxy] uses the [GL-S10 Bluetooth Proxy template][gls10-bluetooth-proxy].
- Both run at the ESPHome connection-slot defaults, so the two proxies differ only in hardware.

## HVAC Compressor Sensor (ProS3D)

- [`hvac-compressor-sensor.yaml`][hvac-compressor-sensor] uses the [Unexpected Maker ProS3D template][unexpectedmaker-pros3d] and the [EasyStart template][easystart-template] once per module, reporting both HVAC compressors.
- It is deliberately **not** a Bluetooth proxy. It runs no `bluetooth_proxy`, sets `esp32_ble: max_connections: 2` for its two `ble_client` entries, and scans passively, since it only ever connects to two known addresses and reads no advertisement payloads.
- It is installed outside beside the two compressors, on the u.FL antenna (`external_antenna_restore_mode: ALWAYS_ON`).
- Each module powers its BLE radio only while its compressor runs, so between cycles the live measurements read `unknown` and the RSSI diagnostic drops out. That is the module losing power, not a link fault.

## Garage Fan Thermostats

- [`garage-door-fan-controller.yaml`][garage-door-fan-controller] (Sonoff TH10) and [`garage-gate-fan-controller.yaml`][garage-gate-fan-controller] (Norvi) control cool air ventilation fans in the garage based on temperature.
- See blog [post][blog-garage-cooling-link] for project details.

## Hot Water Recirculation Pump

- [`recirculation-pump-controller.yaml`][recirculation-pump-controller] (Sonoff TH10) controls the whole home hot water recirculation pump using temperature probes on an interval / duration schedule.
- See blog [post][blog-recirculation-pump-link] for project details.

## Maintenance

Work the fleet is carrying, tracked here rather than as issues because none of it is a defect.

### Pending USB Reflash

Two devices still run a bootloader older than ESP-IDF 5.2. OTA writes the app partition and never the bootloader, so only a serial flash clears it. Until then they log `Bootloader too old for OTA rollback and SRAM1 as IRAM (+40KB)` at every boot, have no OTA rollback, and cannot use the extra 40KB of IRAM. Setting `sram1_as_iram` before the reflash hard bricks the device, so that option waits. The mechanism is documented in [OPERATIONS.md][operations-bootloader-age-and-usb-flashing].

Nothing here is urgent. Each device works, and the cost is access rather than risk.

| Device | Access needed |
|---|---|
| [`pantry-bluetooth-proxy.yaml`][pantry-bluetooth-proxy] | Open the case, flash via the UART pads, no USB port on the GL-S10 |
| [`garage-gate-fan-controller.yaml`][garage-gate-fan-controller] | Mounted in an enclosure |

The remaining ESP32 devices are clear: the [garage presence sensor][garage-presence-sensor] and the [HVAC compressor sensor][hvac-compressor-sensor] both report a current bootloader. The [office Bluetooth proxy][office-bluetooth-proxy] is not a candidate: its Waveshare board flashes over USB-C, so a serial flash costs a cable rather than an enclosure teardown. The [garage door controller][garage-door-controller] is powered off and the plant sensors sleep on a 12-hour cycle, so none of them have been checked. The ESP8266 devices are unaffected.

<!-- Repo -->

[apollo-plt-1b]: ./templates/apollo-plt-1b.yaml
[easystart-template]: ./templates/easystart.yaml
[garage-door-controller]: ./garage-door-controller.yaml
[garage-door-fan-controller]: ./garage-door-fan-controller.yaml
[garage-gate-fan-controller]: ./garage-gate-fan-controller.yaml
[garage-presence-sensor]: ./garage-presence-sensor.yaml
[gls10-bluetooth-proxy]: ./templates/gls10-bluetooth-proxy.yaml
[hvac-compressor-sensor]: ./hvac-compressor-sensor.yaml
[konnected-blaq]: ./templates/konnected-blaq.yaml
[music-room-plant-sensor]: ./music-room-plant-sensor.yaml
[office-bluetooth-proxy]: ./office-bluetooth-proxy.yaml
[operations-bootloader-age-and-usb-flashing]: ./OPERATIONS.md#bootloader-age-and-usb-flashing
[pantry-bluetooth-proxy]: ./pantry-bluetooth-proxy.yaml
[patio-plant-sensor]: ./patio-plant-sensor.yaml
[recirculation-pump-controller]: ./recirculation-pump-controller.yaml
[smarthome-ceilsense]: ./templates/smarthome-ceilsense.yaml
[stairs-plant-sensor]: ./stairs-plant-sensor.yaml
[templates]: ./templates/
[unexpectedmaker-pros3d]: ./templates/unexpectedmaker-pros3d.yaml
[upstairs-hallway-plant-sensor]: ./upstairs-hallway-plant-sensor.yaml
[waveshare-esp32-s3-eth]: ./templates/waveshare-esp32-s3-eth.yaml

<!-- External -->

[blog-garage-cooling-link]: https://blog.insanegenius.com/2021/08/11/trying-to-keep-my-garage-cool/
[blog-recirculation-pump-link]: https://blog.insanegenius.com/2020/10/11/hot-water-recirculation-pump-controller/
[issue-29-link]: https://github.com/ptr727/ESPHome-Config/issues/29
[makerworld-esp32-s3-eth-poe-case-link]: https://makerworld.com/en/models/1536469-waveshare-esp32-s3-eth-poe-case-opendtu
