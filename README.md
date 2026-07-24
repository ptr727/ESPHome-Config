# ESPHome-Config

ESPHome configuration templates and projects.

## About

A collection of ESPHome hardware templates and projects I use in my home automation setup.

## Templates

A [collection](./templates/) of utility and device-specific configuration templates.

Note that for devices with native ESPHome factory firmware, I opt to strip out the generic project and [Improv](https://www.improv-wifi.com/) configuration in favor of a custom configuration specific to my environment. This also cuts down on resource utilization by removing unused features.

Every device template has an example configuration in [test](./test/) that CI compiles against the current ESPHome release, so a published template is known to build. The examples also serve as minimal usage samples.

### Device Templates

#### Ayococr X5P WiFi Plug

- [Template](./templates/aoycocr-x5p.yaml) for the [Ayococr X5P](https://www.amazon.com/dp/B07R6CT3G7) US 120V AC WiFi wall plug.
- See blog [post](https://blog.insanegenius.com/2020/09/10/tuya-to-tasmota-to-esphome/) for firmware conversion details.

#### EFUN SH331 WiFi Power Monitoring Plug

- [Template](./templates/efun-sh331.yaml) for the [EFUN SH331W](https://www.amazon.com/gp/product/B07DCJ7TDR) US 120V AC WiFi power monitoring wall plug.
- See blog [post](https://blog.insanegenius.com/2020/09/10/tuya-to-tasmota-to-esphome/) for firmware conversion details.
- Note: No longer listed on Amazon.

#### Sonoff TH10/TH16 WiFi Relay

- [Template](./templates/sonoff-th10.yaml) for the [Sonoff TH10](https://www.amazon.com/Sonoff-Temperature-Monitoring-Assistant-DS18B20/dp/B08DFQ2NP3) and [Sonoff TH16](https://www.amazon.com/Sonoff-Temperature-Humidity-Monitoring-Assistant/dp/B07TF5SYGL) WiFi relay.
- Follow the Tasmota [guide](https://tasmota.github.io/docs/devices/Sonoff-TH/) for flashing instructions.
- Note: Sonoff TH10 and TH16 have been replaced by the [SONOFF TH Origin](https://itead.cc/product/sonoff-th/), see the [Tasmota Templates](https://templates.blakadder.com/sonoff_THR316.html) for pin layouts.

#### Sonoff S31 WiFi Power Monitoring Plug

- [Template](./templates/sonoff-s31.yaml) for the [Sonoff S31](https://www.amazon.com/Sonoff-Monitoring-Certified-Assistant-Supporting/dp/B08GKGS197) US 120V AC WiFi power monitoring wall plug.
- Follow the Tasmota [guide](https://tasmota.github.io/docs/devices/Sonoff-S31/) for flashing instructions.

#### Norvi NORVI-ENET-AE06-R DIN Controller

- [Template](./templates/norvi-enet-ae06-r.yaml) for the [Norvi NORVI-ENET-AE06-R](https://shop.norvi.lk/products/norvi-enet-ae06-r) or [SensOper SC-EN-I6-RO4](https://sensoper.com/shop/sc-en-i6-ro4/) ESP32 DIN form factor controllers.
- Flash over USB.
- Note:
  - Norvi devices are sold under the [SensOper Controls](https://sensoper.com/) brand in the US and available at the [SensOper store](https://sensoper.com/shop).
  - Norvi branded devices can be shipped to the US from the Sri Lanka based [Norvi store](https://shop.norvi.lk), or the Germany based [CarTFT store](https://www.cartft.com).
  - Norvi addressed PSU interference and drifting ADC issues through a design change (May 2024 date code), see the [notes](./templates/norvi-enet-ae06-r.yaml) section in YML for details.
  - There is an ongoing issue where enabling output on GPIO15 turns the status LED's on and could interfere with input sensors, see the [notes](./templates/norvi-enet-ae06-r.yaml) section in YML for details.

#### RocketController ASTRA DIN Controller

- [Template](./templates/rocket-astra.yaml) for the [RocketController / RocketDyn ASTRA](https://www.rocketcontroller.com) ESP32 DIN form factor controllers.
- Follow the RocketController [guide](https://www.rocketcontroller.com/docs/esphome) for flashing instructions.

#### Kincony KC868-ASR DIN Controller

- [Template](./templates/kincony-kc868-asr.yaml) for the [Kincony KC868-ASR](https://www.kincony.com/esp32-sd-card-rtc-ds3231.html) ESP32 DIN form factor controllers.
- Flash over USB.

#### GL-S10 POE Ethernet Bluetooth Proxy

- [Template](./templates/gls10-bluetooth-proxy.yaml) to use the [GL-S10 IoT Gateway](https://www.gl-inet.com/products/gl-s10/) as a Bluetooth proxy.
- Follow the Blakadder [guide](https://blakadder.com/gl-s10/) for flashing instructions.
- Warning: Do not connect USB power and POE power at the same time.

#### Konnected blaQ Smart Garage Door Controller

- [Template](./templates/konnected-blaq.yaml) for the [Konnected blaQ](https://konnected.io/products/smart-garage-door-opener-blaq-myq-alternative) smart garage door controller.
- This is a Home Assistant friendly alternative to the Chamberlain myQ that [cut off HA access](https://www.home-assistant.io/blog/2023/11/06/removal-of-myq-integration/).
- Imports Konnected's upstream [firmware package](https://github.com/konnected-io/konnected-esphome/blob/master/garage-door-GDOv2-Q.yaml) and surgically strips stock provisioning, see the [template](./templates/konnected-blaq.yaml) for details.

#### Apollo PLT-1B Plant Sensor

- [Template](./templates/apollo-plt-1b.yaml) for the [Apollo PLT-1B](https://apolloautomation.com/products/plt-1) plant soil sensor.
- Imports Apollo's upstream [firmware package](https://github.com/ApolloAutomation/PLT-1/blob/main/Integrations/ESPHome/PLT-1B.yaml) and surgically strips the stock provisioning, see the [template](./templates/apollo-plt-1b.yaml) for details.

#### SmartHomeShop CeilSense Presence and Air Sensor

- [Template](./templates/smarthome-ceilsense.yaml) for the [SmartHomeShop CeilSense v1 Complete](https://ceilsense.nl/en/) presence sensor.
- Imports SmartHomeShop's upstream [firmware package](https://github.com/smarthomeshop/ceilsense/blob/main/ceilsense-v1/ceilsense-complete-wifi-ld2412.yaml) and surgically strips the stock provisioning, see the [template](./templates/smarthome-ceilsense.yaml) for details.

#### Micro-Air EasyStart Soft-Starter

- [Template](./templates/easystart.yaml) to attach a [Micro-Air EasyStart](https://www.microair.net) AC compressor soft-starter to a Bluetooth proxy as a `ble_client`, exposing live current, estimated power, line frequency, last-start peak, short-cycle delay, system state, running state, and start / fault / learned-start counters in Home Assistant, plus a BLE signal-strength diagnostic for the link.
- Used by [`office-bluetooth-proxy.yaml`](./office-bluetooth-proxy.yaml), which sits near the HVAC units and attaches both compressors.
- The reverse-engineered Bluetooth protocol, the ESPHome external component, and a live BLE monitor utility are in [easystart/](./easystart/), see [easystart/README.md](./easystart/README.md) for details.

### Utility Templates

Shared building-block includes, composed via `packages:` by the device templates and per-device configs:

- [`api.yaml`](./templates/api.yaml) - API with encryption and a configurable `api_reboot_timeout`.
- [`ota.yaml`](./templates/ota.yaml) - ESPHome OTA with password.
- [`logger.yaml`](./templates/logger.yaml) - logger configuration.
- [`time.yaml`](./templates/time.yaml) - Home Assistant time source.
- [`wifi.yaml`](./templates/wifi.yaml) - managed WiFi credentials from secrets.
- [`basic.yaml`](./templates/basic.yaml) - restart button plus status, uptime, and version sensors.
- [`common.yaml`](./templates/common.yaml) - bundles the api / ota / logger / time / wifi / basic includes for a typical device.
- [`debug.yaml`](./templates/debug.yaml) - debug component and debug text sensors.
- [`temperature.yaml`](./templates/temperature.yaml) - on-chip internal temperature sensor.
- [`ethernet-sensor.yaml`](./templates/ethernet-sensor.yaml) - Ethernet IP / MAC info text sensors.
- [`secrets.yaml`](./templates/secrets.yaml) - re-exports the root `secrets.yaml` so templates can resolve secrets.

Board and component helpers:

- [RGB LED Status](./templates/rgb-led-status.yaml) component. Useful for boards with only a RGB LED to use as [Status LED](https://esphome.io/components/status_led.html) component equivalent.
- [ESP32-S3-DevKitC](./templates/esp32-s3-devkitc.yaml) devkit template, and [ESP32-S3-WROOM-2-N32R8V](./templates/esp32-s3-wroom-2-n32r8v.yaml) and [ESP32-S3-WROOM-2-N16R8V](./templates/esp32-s3-wroom-2-n16r8v.yaml) board definitions for the [ESP32-S3-DevKitC](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/hw-reference/esp32s3/user-guide-devkitc-1.html) boards. The default [`esp32-s3-devkit-c-1`](https://docs.platformio.org/en/latest/boards/espressif32/esp32-s3-devkitc-1.html) board only supports the `ESP32-S3-WROOM-1-N8` with 8MB Quad Flash and no PSRAM, any other board requires some customization, especially for the Octal memory boards. Includes the on-chip temperature sensor and RGB LED as status LED.
- [WEMOS LOLIN32 Lite](./templates/wemos-lolin32-lite.yaml) devkit template for [WEMOS LOLIN32 Lite](https://web.archive.org/web/20191002041532/https://wiki.wemos.cc/products:lolin32:lolin32_lite) and clone boards. Includes the LED as status LED.
- [Adafruit ESP32-S3 Feather](./templates/adafruit-esp32-s3-feather.yaml) devkit template for the [Adafruit ESP32-S3 Feather](https://www.adafruit.com/product/5323) board. Includes the on-chip temperature sensor, RGB LED as status LED, and [MAX17048](https://www.analog.com/en/products/max17048.html) I2C battery charge monitor.

## Projects

Per-device configs live in the repository root. Each sets `substitutions:` (device name, friendly name, and any per-device overrides) and pulls in a template via `packages:`.

### Plant Sensors (Apollo PLT-1B)

- [`music-room-plant-sensor.yaml`](./music-room-plant-sensor.yaml), [`patio-plant-sensor.yaml`](./patio-plant-sensor.yaml), [`stairs-plant-sensor.yaml`](./stairs-plant-sensor.yaml), and [`upstairs-hallway-plant-sensor.yaml`](./upstairs-hallway-plant-sensor.yaml) use the [Apollo PLT-1B template](./templates/apollo-plt-1b.yaml).

### Garage Presence and Air Sensor (CeilSense)

- [`garage-presence-sensor.yaml`](./garage-presence-sensor.yaml) uses the [SmartHomeShop CeilSense template](./templates/smarthome-ceilsense.yaml) for presence, CO2, temperature, humidity, lux, and pressure in the garage.

### Garage Door Controller (Konnected blaQ)

- [`garage-door-controller.yaml`](./garage-door-controller.yaml) uses the [Konnected blaQ template](./templates/konnected-blaq.yaml).
- Note: currently powered off pending an upstream investigation into self-opening incidents, see the status block in the config and [issue #29](https://github.com/ptr727/ESPHome-Config/issues/29).

### Bluetooth Proxies (GL-S10)

- [`office-bluetooth-proxy.yaml`](./office-bluetooth-proxy.yaml) and [`pantry-bluetooth-proxy.yaml`](./pantry-bluetooth-proxy.yaml) use the [GL-S10 Bluetooth Proxy template](./templates/gls10-bluetooth-proxy.yaml).

### Garage Fan Thermostats

- [`garage-door-fan-controller.yaml`](./garage-door-fan-controller.yaml) (Sonoff TH10) and [`garage-gate-fan-controller.yaml`](./garage-gate-fan-controller.yaml) (Norvi) control cool air ventilation fans in the garage based on temperature.
- See blog [post](https://blog.insanegenius.com/2021/08/11/trying-to-keep-my-garage-cool/) for project details.

### Hot Water Recirculation Pump

- [`recirculation-pump-controller.yaml`](./recirculation-pump-controller.yaml) (Sonoff TH10) controls the whole home hot water recirculation pump using temperature probes on an interval / duration schedule.
- See blog [post](https://blog.insanegenius.com/2020/10/11/hot-water-recirculation-pump-controller/) for project details.

## Usage

- The standard [ESPHome](https://hub.docker.com/r/esphome/esphome) container does not support running as non-root. Deploy the [ESPHome-NonRoot](https://github.com/ptr727/ESPHome-NonRoot) container for non-root operation if desired.
- Set directory permissions:
  - `sudo chown -R nonroot:users /data/appdata/esphome`
  - `sudo chmod -R ug=rwx,o=rx /data/appdata/esphome`
- Clone Git repository in ESPHome config folder, or copy files.
  - `cd /data/appdata/esphome/config`
  - `git clone -b develop https://github.com/ptr727/ESPHome-Config .`
- Deploy `secrets.yaml`, use `secrets._yaml` as a template for required secrets.
- In VSCode open remote SSH workspace on the docker host, and open the workspace from config directory.

## Notes

### Issues

- For general ESPHome support visit the [ESPHome Discord `#general-support`](https://discord.gg/dbwxp5R3).
- Only file an [issue](https://github.com/ptr727/ESPHome-Config/issues) if you believe there is a bug in a [template](./templates/) or one of my projects.

### Espressif32 and Framework Versions

- PlatformIO version is determined by the ESPHome release, it cannot be updated independently.
- `framework:` `type:` can be `arduino` or `esp-idf`, use [`esp-idf`](https://esphome.io/components/esp32#esp-idf-framework) for ESP32 devices.
- `platform_version` specifies the `platformio/espressif32` [version](https://registry.platformio.org/platforms/platformio/espressif32/versions).
  - Using `latest` is not supported, use an exact version number.
- `version` specifies the `platformio/framework-espidf` [version](https://registry.platformio.org/tools/platformio/framework-espidf).
  - Using `latest` will use the version supported by `platformio/espressif32` at release time, not the current latest version.

## Debugging

### VSCode Setup

- Install VSCode.
- Clone `ptr727/ESPHome-Config` repo and open workspace.
- Upload `secrets.yaml`.
- Open `ESPHome-Config` workspace.
- Install recommended extensions (from workspace).
- Associate YAML files with ESPHome (from the ESPHome extension).
- Select default Python interpreter and create virtual environment (Ctrl-Shift-P Python...).
- Install ESPHome (in venv terminal): `pip install --upgrade [--pre] setuptools wheel platformio esphome`.
- Make sure [ESPHome](https://esphome.io/guides/cli) is installed: `esphome version`.
- Compile ESPHome project: `esphome compile esp32-s3-test.yaml`.
- Launch Dashboard: `esphome dashboard .`, open [http://localhost:6052/](http://localhost:6052/).

### Debugging in DevContainer

- Setup [VSCode](#vscode-setup).
- Open workspace and clone in devcontainer volume.
- TODO: Serial port forwarding config.

### Debugging on Windows

- Install Python from the Microsoft Store.
- Setup [VSCode](#vscode-setup).
- Compile ESPHome project: `esphome compile esp32-s3-feather-test.yaml`.
- Plugin device, hold Boot and press Reset if required.
- List COM ports from PowerShell:
  - Serial ports: `[System.IO.Ports.SerialPort]::getportnames()`
  - Msft drivers: `Get-CimInstance -Class Win32_SerialPort | Select-Object Name, Description, DeviceID`.
  - Custom drivers: `Get-CimInstance -ClassName Win32_PnPEntity | Where-Object { $_.Name -match '.*\(COM(\d)\)' } Select-Object Caption`.
- Upload firmware: `esphome run --device COM4 esp32-s3-feather-test.yaml`.
- Log output: `esphome logs [--device COM5] esp32-s3-feather-test.yaml`.

### Debugging on Windows WSL

- Install Ubuntu or Debian from the Microsoft Store.
- Install [USBIPD-WIN](https://learn.microsoft.com/en-us/windows/wsl/connect-usb) from [GitHub Releases](https://github.com/dorssel/usbipd-win/releases/latest).
- Bind serial port.
  - Open PowerShell as Admin in Terminal, referred to as Windows.
  - Open Ubuntu in Terminal, referred to as WSL.
  - Windows: `usbipd list`, e.g. `7-1    303a:1001  USB Serial Device (COM4), USB JTAG/serial debug unit          Not shared`
  - Windows: `usbipd bind --busid 7-1`
  - Windows: `usbipd attach --wsl --busid 7-1`
  - WSL: `sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y`
  - WSL: `sudo apt install python3 python3-venv usbutils -y`
  - WSL: `lsusb`, e.g. `Bus 001 Device 002: ID 303a:1001 Espressif USB JTAG/serial debug unit`
  - WSL: `dmesg | grep tty`, e.g. `cdc_acm 1-1:1.0: ttyACM0: USB ACM device`
  - WSL: `ls /dev/tty*`, e.g. `/dev/ttyACM0`, `/dev/ttyUSB0`
- Install VSCode and the Remote Explorer extension.
- Open VSCode Remote WSL Ubuntu session.
  - Setup [VSCode](#vscode-setup) in remote WSL session.
  - List COM ports: `ls /dev/tty*`.
  - Upload firmware: `esphome run --device /dev/ttyUSB0 esp32-s3-test.yaml`
- Unbind serial port.
  - Windows: `usbipd detach --busid 7-1`
  - Windows: `usbipd unbind --all`

### Debugging in PlatformIO

- Setup [VSCode](#vscode-setup) and install the PlatformIO extension.
- Compile the project using `esphome compile [project]`.
- Launch the PlatformIO extension and open the project folder, e.g. `./.esphome/build/esp32-s3-test`
- PlatformIO will open a new instance of VSCode for that project.
- Select default Python interpreter and create virtual environment (Ctrl-Shift-P Python...).
- PlatformIO Core will be installed in the virtual environment and use the environment Python.
