# ESPHome-Config

ESPHome configuration templates and projects.

## About

A collection of ESPHome hardware templates and projects I use in my home automation setup.

## Templates

A [collection][templates] of utility and device-specific configuration templates.

Note that for devices with native ESPHome factory firmware, I opt to strip out the generic project and [Improv][improv-wifi-link] configuration in favor of a custom configuration specific to my environment. This also cuts down on resource utilization by removing unused features.

Every device template has an example configuration in [test][test] that CI compiles against the current ESPHome release, so a published template is known to build. The examples also serve as minimal usage samples, composing the template with a local `!include`.

Every template also opens with an `External usage:` comment block showing how to compose it from outside this repository as a remote `github://` package, along with whatever that particular template needs from the including config. Relative includes resolve inside the fetched package, and `!secret` falls back to a `secrets.yaml` beside the including config, so an adopter supplies their own secrets under the names in [`secrets._yaml`][secrets-example].

### Device Templates

#### Ayococr X5P WiFi Plug

- [Template][aoycocr-x5p] for the [Ayococr X5P][amazon-dp-b07r6ct3g7-link] US 120V AC WiFi wall plug.
- See blog [post][blog-tuya-to-esphome-link] for firmware conversion details.

#### EFUN SH331 WiFi Power Monitoring Plug

- [Template][efun-sh331] for the [EFUN SH331W][efun-sh331w-link] US 120V AC WiFi power monitoring wall plug.
- See blog [post][blog-tuya-to-esphome-link] for firmware conversion details.
- Note: No longer listed on Amazon.

#### Sonoff TH10/TH16 WiFi Relay

- [Template][sonoff-th10] for the [Sonoff TH10][amazon-sonoff-temperature-monitoring-assistant-ds18b20-dp-link] and [Sonoff TH16][amazon-sonoff-temperature-humidity-monitoring-assistant-dp-link] WiFi relay.
- Follow the Tasmota [guide][tasmota-sonoff-th-link] for flashing instructions.
- Note: Sonoff TH10 and TH16 have been replaced by the [SONOFF TH Origin][itead-product-sonoff-th-link], see the [Tasmota Templates][templates-sonoff-thr316-link] for pin layouts.

#### Sonoff S31 WiFi Power Monitoring Plug

- [Template][sonoff-s31] for the [Sonoff S31][amazon-sonoff-monitoring-certified-assistant-supporting-dp-link] US 120V AC WiFi power monitoring wall plug.
- Follow the Tasmota [guide][tasmota-sonoff-s31-link] for flashing instructions.

#### Norvi NORVI-ENET-AE06-R DIN Controller

- [Template][norvi-enet-ae06-r] for the [Norvi NORVI-ENET-AE06-R][shop-products-norvi-enet-ae06-r-link] or [SensOper SC-EN-I6-RO4][sensoper-shop-sc-en-i6-ro4-link] ESP32 DIN form factor controllers.
- Flash over USB.
- Note:
  - Norvi devices are sold under the [SensOper Controls][sensoper-link] brand in the US and available at the [SensOper store][sensoper-shop-link].
  - Norvi branded devices can be shipped to the US from the Sri Lanka based [Norvi store][shop-link], or the Germany based [CarTFT store][cartft-link].
  - Norvi addressed PSU interference and drifting ADC issues through a design change (May 2024 date code), see the [notes][norvi-enet-ae06-r] section in YML for details.
  - There is an ongoing issue where enabling output on GPIO15 turns the status LEDs on and could interfere with input sensors, see the [notes][norvi-enet-ae06-r] section in YML for details.

#### RocketController ASTRA DIN Controller

- [Template][rocket-astra] for the [RocketController / RocketDyn ASTRA][rocketcontroller-link] ESP32 DIN form factor controllers.
- Follow the RocketController [guide][rocketcontroller-docs-esphome-link] for flashing instructions.

#### Kincony KC868-ASR DIN Controller

- [Template][kincony-kc868-asr] for the [Kincony KC868-ASR][kincony-esp32-sd-card-rtc-ds3231-link] ESP32 DIN form factor controllers.
- Flash over USB.

#### GL-S10 POE Ethernet Bluetooth Proxy

- [Template][gls10-bluetooth-proxy] to use the [GL-S10 IoT Gateway][gl-inet-products-gl-s10-link] as a Bluetooth proxy.
- Follow the Blakadder [guide][blakadder-gl-s10-link] for flashing instructions.
- Warning: Do not connect USB power and POE power at the same time.

#### Konnected blaQ Smart Garage Door Controller

- [Template][konnected-blaq] for the [Konnected blaQ][konnected-products-smart-garage-door-opener-blaq-myq-alternative-link] smart garage door controller.
- This is a Home Assistant friendly alternative to the Chamberlain myQ that [cut off HA access][home-assistant-blog-2023-link].
- Imports Konnected's upstream [firmware package][github-konnected-io-konnected-esphome-link] and surgically strips stock provisioning, see the [template][konnected-blaq] for details.

#### Apollo PLT-1B Plant Sensor

- [Template][apollo-plt-1b] for the [Apollo PLT-1B][apolloautomation-products-plt-1-link] plant soil sensor.
- Imports Apollo's upstream [firmware package][github-apolloautomation-plt-1-link] and surgically strips the stock provisioning, see the [template][apollo-plt-1b] for details.

#### SmartHomeShop CeilSense Presence and Air Sensor

- [Template][smarthome-ceilsense] for the [SmartHomeShop CeilSense v1 Complete][ceilsense-en-link] presence sensor.
- Imports SmartHomeShop's upstream [firmware package][github-smarthomeshop-ceilsense-link] and surgically strips the stock provisioning, see the [template][smarthome-ceilsense] for details.

#### Micro-Air EasyStart Soft-Starter

- [Template][easystart-template] to attach a [Micro-Air EasyStart][microair-link] AC compressor soft-starter to a Bluetooth proxy as a `ble_client`, exposing live current, estimated power, line frequency, last-start peak, short-cycle delay, system state, running state, and start / fault / learned-start counters in Home Assistant, plus a BLE signal-strength diagnostic for the link.
- Used by [`hvac-compressor-sensor.yaml`][hvac-compressor-sensor], which sits outside next to the HVAC units and attaches both compressors.
- The reverse-engineered Bluetooth protocol, the ESPHome external component, and a live BLE monitor utility are in [easystart/][easystart], see [easystart/README.md][easystart-readme] for details.

### Utility Templates

Shared building-block includes, composed via `packages:` by the device templates and per-device configs:

- [`api.yaml`][api] - API with encryption and a configurable `api_reboot_timeout`.
- [`ota.yaml`][ota] - ESPHome OTA with password.
- [`logger.yaml`][logger] - logger configuration.
- [`time.yaml`][time] - Home Assistant time source.
- [`wifi.yaml`][wifi] - managed WiFi credentials from secrets.
- [`basic.yaml`][basic] - restart button plus status, uptime, and version sensors.
- [`common.yaml`][common] - bundles the api / ota / logger / time / wifi / basic includes for a typical device.
- [`debug.yaml`][debug] - debug component and debug text sensors.
- [`temperature.yaml`][temperature] - on-chip internal temperature sensor.
- [`ethernet-sensor.yaml`][ethernet-sensor] - Ethernet IP / MAC info text sensors.
- [`secrets.yaml`][secrets] - re-exports the root `secrets.yaml` so templates can resolve secrets.

### Board and Component Helpers

#### RGB LED Status Component

- [Template][rgb-led-status] for boards that have an addressable RGB LED but no plain status LED.
- Serves as the [Status LED][esphome-components-status-led-link] component equivalent.
- Drives the LED from boot, network, and API state: green for a connected API client, white for a network link with no client, yellow for booted with no link, red for still booting.
- Interface agnostic, it reads ESPHome's own [network helper][github-esphome-network-util-link] rather than binding to WiFi, so it works on a WiFi board, an Ethernet board, or one carrying both.
- A consumer can claim the LED itself with `script.execute` on `led_working_status` (red, green, blue, effect) or `led_feedback_blink` (red, green, blue, count).
- Needs only the `rgb_led_pin` substitution and the including config's own `api`, so besides a local `!include` it also composes as a remote package from `github://ptr727/ESPHome-Config/templates/rgb-led-status.yaml@main`.

#### MAX17048 Battery Fuel Gauge

- [Template][max17048] for boards carrying the [MAX17048][analog-max17048-link] I2C fuel gauge, shared by the ProS3D and the Adafruit Feather. It needs only an `i2c` bus from the including board.
- Exposes battery voltage, charge level, and discharge rate, plus a `Battery Gauge Reset` button.
- The gauge fits its charge model once, at its own power-on, and it is powered from the cell rather than from the ESP32. A cell attached after boot is therefore measured against a stale model, and neither a reboot nor an OTA re-fits it. The button issues the QuickStart command that does, and it should be pressed with the cell resting, since a charging voltage biases the fit high.
- A mains-powered device with no cell fitted can drop the gauge entirely, see the header of the [template][max17048].

#### Espressif ESP32-S3-DevKitC-1 Devkit

- [Template][esp32-s3-devkitc] for the [ESP32-S3-DevKitC-1][espressif-esp32-s3-devkitc-link] and clone boards.
- Includes the on-chip temperature sensor and the RGB LED as status LED.
- The default [`esp32-s3-devkitc-1`][platformio-esp32-s3-devkitc-link] board is the `ESP32-S3-WROOM-1-N8`, 8MB Quad Flash and no PSRAM.
- Compose the devkit template with the board definition matching the fitted module:
  - [ESP32-S3-WROOM-1-N16R8][esp32-s3-wroom-1-n16r8]: 16MB Quad Flash, 8MB Octal PSRAM, 3.3V.
  - [ESP32-S3-WROOM-2-N16R8V][esp32-s3-wroom-2-n16r8v]: 16MB Octal Flash, 8MB Octal PSRAM, 1.8V.
  - [ESP32-S3-WROOM-2-N32R8V][esp32-s3-wroom-2-n32r8v]: 32MB Octal Flash, 8MB Octal PSRAM, 1.8V.
- Note:
  - The RGB LED moved from GPIO48 to GPIO38 at board revision v1.1, override the `rgb_led_pin` substitution if the LED stays dark.
  - WROOM-1 and WROOM-1U modules differ only in PCB antenna versus IPEX connector, and are identical to program.
  - See the OTA and Octal flash mode notes in [esp32-s3-wroom-2-n32r8v.yaml][esp32-s3-wroom-2-n32r8v] before choosing a 32MB module.

#### WEMOS LOLIN32 Lite Devkit

- [Template][wemos-lolin32-lite] for the [WEMOS LOLIN32 Lite][web-web-20191002041532-link] and clone boards.
- Includes the LED as status LED.

#### Adafruit ESP32-S3 Feather Devkit

- [Template][adafruit-esp32-s3-feather] for the [Adafruit ESP32-S3 Feather][adafruit-product-5323-link] board.
- Includes the on-chip temperature sensor and the RGB LED as status LED.
- Includes the [MAX17048 fuel gauge helper][max17048].

#### Unexpected Maker ProS3D Devkit

- [Template][unexpectedmaker-pros3d] for the [Unexpected Maker ProS3D][unexpectedmaker-pros3d-link] board.
- Includes the on-chip temperature sensor and the RGB LED as status LED.
- Includes the [MAX17048 fuel gauge helper][max17048] and a USB power presence sensor.
- Optional substitutions:
  - `external_antenna_restore_mode`: `ALWAYS_OFF` selects the onboard PCB antenna, `ALWAYS_ON` selects the u.FL connector.
  - `ldo2_power_restore_mode`: `ALWAYS_ON` powers the `3V3_2` rail, which feeds the RGB LED and the `3V3_2` header pin, `ALWAYS_OFF` leaves both off.

#### Waveshare ESP32-S3-ETH Board

- [Template][waveshare-esp32-s3-eth] for the [Waveshare ESP32-S3-ETH][waveshare-esp32-s3-eth-link] board, an ESP32-S3R8 with 16MB Quad Flash and 8MB Octal PSRAM.
- Wired networking through the onboard [W5500][waveshare-esp32-s3-eth-wiki-link] SPI Ethernet controller, with an optional IEEE 802.3af PoE module that claims no GPIO.
- Includes the on-chip temperature sensor and the RGB LED as status LED.
- Configures `ethernet` rather than `wifi`. The two [cannot be used together][esphome-components-ethernet-link], so this template composes the `api` / `basic` / `debug` / `logger` / `ota` / `time` includes directly instead of [`common.yaml`][common], which carries [`wifi.yaml`][wifi].
- Sets no `domain`, so the device is reachable only by whatever address DHCP registered for it.
- Flash over USB-C. The port is the chip's native USB with no UART bridge, so no adapter and no case opening is needed for the first flash or a later bootloader refresh.
- The onboard ceramic antenna is selected by a resistor, and reaching the IPEX Gen 1 connector means moving it. There is no antenna select GPIO, so this is a soldering change rather than a config one.
- Documented in the [template][waveshare-esp32-s3-eth] header but deliberately not configured:
  - The camera DVP pins, for anyone fitting an OV5640.
  - The TF card slot, since ESPHome has no SD card component, tracked as [feature request 513][github-esphome-feature-requests-513-link].

## Devices

The templates above run on my own devices, whose per-device configs live in the repository root. They are documented in [DEVICES.md][devices].

## Usage

- The standard [ESPHome][docker-hub-esphome-link] container does not support running as non-root. Deploy the [ESPHome-NonRoot][github-ptr727-esphome-nonroot-link] container for non-root operation if desired.
- Set directory permissions:
  - `sudo chown -R nonroot:users /data/appdata/esphome`
  - `sudo chmod -R ug=rwx,o=rx /data/appdata/esphome`
- Clone Git repository in ESPHome config folder, or copy files.
  - `cd /data/appdata/esphome/config`
  - `git clone -b develop https://github.com/ptr727/ESPHome-Config .`
- Deploy `secrets.yaml`, use `secrets._yaml` as a template for required secrets.
- In VSCode open remote SSH workspace on the docker host, and open the workspace from config directory.

## Issues

- For general ESPHome support visit the [ESPHome Discord `#general-support`][discord-dbwxp5r3-link].
- Only file an [issue][issues-link] if you believe there is a bug in a [template][templates] or one of my projects.

## Debugging

Building, flashing, and debugging a device outside the live ESPHome instance is documented in [OPERATIONS.md][operations-debugging]: VSCode setup, the devcontainer, Windows, Windows WSL, and PlatformIO. The framework and platform version notes are in [the same file][operations-framework-and-platform-versions].

<!-- Repo -->

[adafruit-esp32-s3-feather]: ./templates/adafruit-esp32-s3-feather.yaml
[aoycocr-x5p]: ./templates/aoycocr-x5p.yaml
[api]: ./templates/api.yaml
[apollo-plt-1b]: ./templates/apollo-plt-1b.yaml
[basic]: ./templates/basic.yaml
[common]: ./templates/common.yaml
[debug]: ./templates/debug.yaml
[devices]: ./DEVICES.md
[easystart-readme]: ./easystart/README.md
[easystart-template]: ./templates/easystart.yaml
[easystart]: ./easystart/
[efun-sh331]: ./templates/efun-sh331.yaml
[esp32-s3-devkitc]: ./templates/esp32-s3-devkitc.yaml
[esp32-s3-wroom-1-n16r8]: ./templates/esp32-s3-wroom-1-n16r8.yaml
[esp32-s3-wroom-2-n16r8v]: ./templates/esp32-s3-wroom-2-n16r8v.yaml
[esp32-s3-wroom-2-n32r8v]: ./templates/esp32-s3-wroom-2-n32r8v.yaml
[ethernet-sensor]: ./templates/ethernet-sensor.yaml
[gls10-bluetooth-proxy]: ./templates/gls10-bluetooth-proxy.yaml
[hvac-compressor-sensor]: ./hvac-compressor-sensor.yaml
[kincony-kc868-asr]: ./templates/kincony-kc868-asr.yaml
[konnected-blaq]: ./templates/konnected-blaq.yaml
[logger]: ./templates/logger.yaml
[max17048]: ./templates/max17048.yaml
[norvi-enet-ae06-r]: ./templates/norvi-enet-ae06-r.yaml
[operations-debugging]: ./OPERATIONS.md#debugging
[operations-framework-and-platform-versions]: ./OPERATIONS.md#framework-and-platform-versions
[ota]: ./templates/ota.yaml
[rgb-led-status]: ./templates/rgb-led-status.yaml
[rocket-astra]: ./templates/rocket-astra.yaml
[secrets-example]: ./secrets._yaml
[secrets]: ./templates/secrets.yaml
[smarthome-ceilsense]: ./templates/smarthome-ceilsense.yaml
[sonoff-s31]: ./templates/sonoff-s31.yaml
[sonoff-th10]: ./templates/sonoff-th10.yaml
[temperature]: ./templates/temperature.yaml
[templates]: ./templates/
[test]: ./test/
[time]: ./templates/time.yaml
[unexpectedmaker-pros3d]: ./templates/unexpectedmaker-pros3d.yaml
[waveshare-esp32-s3-eth]: ./templates/waveshare-esp32-s3-eth.yaml
[wemos-lolin32-lite]: ./templates/wemos-lolin32-lite.yaml
[wifi]: ./templates/wifi.yaml

<!-- External -->

[adafruit-product-5323-link]: https://www.adafruit.com/product/5323
[amazon-dp-b07r6ct3g7-link]: https://www.amazon.com/dp/B07R6CT3G7
[amazon-sonoff-monitoring-certified-assistant-supporting-dp-link]: https://www.amazon.com/Sonoff-Monitoring-Certified-Assistant-Supporting/dp/B08GKGS197
[amazon-sonoff-temperature-humidity-monitoring-assistant-dp-link]: https://www.amazon.com/Sonoff-Temperature-Humidity-Monitoring-Assistant/dp/B07TF5SYGL
[amazon-sonoff-temperature-monitoring-assistant-ds18b20-dp-link]: https://www.amazon.com/Sonoff-Temperature-Monitoring-Assistant-DS18B20/dp/B08DFQ2NP3
[analog-max17048-link]: https://www.analog.com/en/products/max17048.html
[apolloautomation-products-plt-1-link]: https://apolloautomation.com/products/plt-1
[blakadder-gl-s10-link]: https://blakadder.com/gl-s10/
[blog-tuya-to-esphome-link]: https://blog.insanegenius.com/2020/09/10/tuya-to-tasmota-to-esphome/
[cartft-link]: https://www.cartft.com
[ceilsense-en-link]: https://ceilsense.nl/en/
[discord-dbwxp5r3-link]: https://discord.gg/dbwxp5R3
[docker-hub-esphome-link]: https://hub.docker.com/r/esphome/esphome
[efun-sh331w-link]: https://www.amazon.com/gp/product/B07DCJ7TDR
[esphome-components-ethernet-link]: https://esphome.io/components/ethernet/
[esphome-components-status-led-link]: https://esphome.io/components/status_led/
[espressif-esp32-s3-devkitc-link]: https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/index.html
[github-apolloautomation-plt-1-link]: https://github.com/ApolloAutomation/PLT-1/blob/main/Integrations/ESPHome/PLT-1B.yaml
[github-esphome-feature-requests-513-link]: https://github.com/esphome/feature-requests/issues/513
[github-esphome-network-util-link]: https://github.com/esphome/esphome/blob/dev/esphome/components/network/util.h
[github-konnected-io-konnected-esphome-link]: https://github.com/konnected-io/konnected-esphome/blob/master/garage-door-GDOv2-Q.yaml
[github-ptr727-esphome-nonroot-link]: https://github.com/ptr727/ESPHome-NonRoot
[github-smarthomeshop-ceilsense-link]: https://github.com/smarthomeshop/ceilsense/blob/main/ceilsense-v1/ceilsense-complete-wifi-ld2412.yaml
[gl-inet-products-gl-s10-link]: https://www.gl-inet.com/products/gl-s10/
[home-assistant-blog-2023-link]: https://www.home-assistant.io/blog/2023/11/06/removal-of-myq-integration/
[improv-wifi-link]: https://www.improv-wifi.com/
[issues-link]: https://github.com/ptr727/ESPHome-Config/issues
[itead-product-sonoff-th-link]: https://itead.cc/product/sonoff-th/
[kincony-esp32-sd-card-rtc-ds3231-link]: https://www.kincony.com/esp32-sd-card-rtc-ds3231.html
[konnected-products-smart-garage-door-opener-blaq-myq-alternative-link]: https://konnected.io/products/smart-garage-door-opener-blaq-myq-alternative
[microair-link]: https://www.microair.net
[platformio-esp32-s3-devkitc-link]: https://docs.platformio.org/en/latest/boards/espressif32/esp32-s3-devkitc-1.html
[rocketcontroller-docs-esphome-link]: https://www.rocketcontroller.com/docs/esphome
[rocketcontroller-link]: https://www.rocketcontroller.com
[sensoper-link]: https://sensoper.com/
[sensoper-shop-link]: https://sensoper.com/shop
[sensoper-shop-sc-en-i6-ro4-link]: https://sensoper.com/shop/sc-en-i6-ro4/
[shop-link]: https://shop.norvi.lk
[shop-products-norvi-enet-ae06-r-link]: https://shop.norvi.lk/products/norvi-enet-ae06-r
[tasmota-sonoff-s31-link]: https://tasmota.github.io/docs/devices/Sonoff-S31/
[tasmota-sonoff-th-link]: https://tasmota.github.io/docs/devices/Sonoff-TH/
[templates-sonoff-thr316-link]: https://templates.blakadder.com/sonoff_THR316.html
[unexpectedmaker-pros3d-link]: https://esp32s3.com/pros3.html
[waveshare-esp32-s3-eth-link]: https://www.waveshare.com/esp32-s3-eth.htm
[waveshare-esp32-s3-eth-wiki-link]: https://www.waveshare.com/wiki/ESP32-S3-ETH
[web-web-20191002041532-link]: https://web.archive.org/web/20191002041532/https://wiki.wemos.cc/products:lolin32:lolin32_lite
