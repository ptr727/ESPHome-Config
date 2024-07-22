# ESPHome-Config

[ESPHome](https://esphome.io/index.html) configuration, templates, and projects.

## Templates

A [collection](./templates/) of utility and device specific configuration templates.
Some templates are customized based on other people's work, see YML files for source references.

### Device Templates

#### TuyaConvert

- Generic bootstrap [template](./tuya-convert.yaml) used when converting Tuya devices to ESPHome using TuyaConvert.
- See blog [post](https://blog.insanegenius.com/2020/09/10/tuya-to-tasmota-to-esphome/) for firmware conversion details.

#### Ayococr X5P WiFi Plug

- [Template](./templates/aoycocr-x5p.yaml) for the [Ayococr X5P](https://www.amazon.com/dp/B07R6CT3G7) US 120V AC WiFi wall plug.
- See blog [post](https://blog.insanegenius.com/2020/09/10/tuya-to-tasmota-to-esphome/) for firmware conversion details.

#### EFUN SH331 WiFi Power Monitoring Plug

- [Template](./templates/efun-sh331.yaml) for the [EFUN SH331W](https://www.amazon.com/gp/product/B07DCJ7TDR) US 120V AC WiFi power monitoring wall plug.
- See blog [post](https://blog.insanegenius.com/2020/09/10/tuya-to-tasmota-to-esphome/) for firmware conversion details.
- Note: No longer listed on Amazon.

#### Sonoff TH10/TH16 WiFi Relay

- [Template](/templates/sonoff-th10.yaml) for the [Sonoff TH10](https://www.amazon.com/Sonoff-Temperature-Monitoring-Assistant-DS18B20/dp/B08DFQ2NP3) and [Sonoff TH16](https://www.amazon.com/Sonoff-Temperature-Humidity-Monitoring-Assistant/dp/B07TF5SYGL) WiFi relay.
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
  - I am experiencing issues with PSU and ADC stability on several devices, see the [notes](./templates/norvi-enet-ae06-r.yaml) section in YML for details.
  - Norvi addressed the issues through a design change (May 2024 date code) and sent me replacement devices, that I still need to test and verify.

#### RocketController ASTRA DIN Controller

- [Template](./templates/rocket-astra.yaml) for the [RocketController / RocketDyn ASTRA](https://rocketcontroller.com/product-category/controllers/) ESP32 DIN form factor controllers.
- Follow the RocketController [guide](https://rocketcontroller.com/programming-astra-module-with-uart-serial-interface-for-arduino-ide-micropython-and-any-programming-language/) for flashing instructions.

#### Kincony KC868-ASR DIN Controller

- [Template](./templates/kincony-kc868-asr.yaml) for the [Kincony KC868-ASR](https://www.kincony.com/esp32-sd-card-rtc-ds3231.html) ESP32 DIN form factor controllers.
- Flash over USB.

#### GL-S10 POE Ethernet Bluetooth Proxy

- [Template](./templates/gls10-bluetooth-proxy.yaml) to use the [GL-S10 IoT Gateway](https://www.gl-inet.com/products/gl-s10/) as a Bluetooth proxy.
- Follow the Blakadder [guide](https://blakadder.com/gl-s10/) for flashing instructions.
- Warning: Do not connect USB power and POE power at the same time.

### Utility Templates

- [RGB LED Status](./templates/rgb-led-status.yaml) component. Useful for boards with only a RGB LED to use as [Status LED](https://esphome.io/components/status_led.html) component equivalent.
- [ESP32-S3-DevKitC](/templates//esp32-s3-devkitc.yaml) devkit template, and [ESP32-S3-WROOM-2-N32R8V](./templates//esp32-s3-wroom-2-n32r8v.yaml) and [ESP32-S3-WROOM-2-N16R8V](./templates/esp32-s3-wroom-2-n16r8v.yaml) board definitions for the [ESP32-S3-DevKitC](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/hw-reference/esp32s3/user-guide-devkitc-1.html) boards. The default [`esp32-s3-devkit-c-1`](https://docs.platformio.org/en/latest/boards/espressif32/esp32-s3-devkitc-1.html) board only supports the `ESP32-S3-WROOM-1-N8` with 8MB Quad Flash and no PSRAM, any other board requires some customization, especially for the Octal memory boards. Includes the on-chip temperature sensor and RGB LED as status LED.
- [WEMOS LOLIN32 Lite](./templates//wemos-lolin32-lite.yaml) devkit template for [WEMOS LOLIN32 Lite](https://web.archive.org/web/20191002041532/https://wiki.wemos.cc/products:lolin32:lolin32_lite) and clone boards. Includes the LED as status LED.
- [Adafruit ESP32-S3 Feather](./templates//adafruit-esp32-s3-feather.yaml) devkit template for the [Adafruit ESP32-S3 Feather](https://www.adafruit.com/product/5323) board. Includes the on-chip temperature sensor, RGB LED as status LED, and [MAX17048](https://www.analog.com/en/products/max17048.html) I2C battery charge monitor.

## Projects

### Garage Fan Thermostat

- Project [`garage-gate-fan.yaml`](./garage-gate-fan.yaml) and [`garage-door-fan.yaml`](./garage-door-fan.yaml) configs are used to control Sonoff TH10's as thermostats for cool air ventilation in my garage.
- See blog [post](https://blog.insanegenius.com/2021/08/11/trying-to-keep-my-garage-cool/) for project details.

### Utility Gas and Water Meter Pulse Counter

- Project [`utility-pulse-counter.yaml`](./utility-pulse-counter.yaml) config is used to measure water and gas consumption from my utility meter pulse counters.
- See blog [post](https://blog.insanegenius.com/2021/08/09/esp32-water-and-gas-utility-meter/) for project details.

### Hot Water Recirculation Pump

- Project [`hot-water-recirc-pump.yaml`](./hot-water-recirc-pump.yaml) config is used to control my whole home hot water recirculation pump using a Sonoff TH10 and several temperature probes.
- See blog [post](https://blog.insanegenius.com/2020/10/11/hot-water-recirculation-pump-controller/) for project details.

### TubesZB Ethernet Zigbee Coordinator

- Project [`zigbee-coordinator.yaml`](./zigbee-coordinator.yaml) is used as my Zigbee Coordinator.
- Customized version of the [TubesZB Ethernet Zigbee Coordinator](https://github.com/tube0013/tube_gateways/blob/main/models/current/tubeszb-cc2652-eth_usb/firmware/esphome/tubezb-cc2652p2-ethusb-2022.yaml).

### RatGDO LiftMaster Garage Door Controller

- Project [`garage-door-controller.yaml`](./garage-door-controller.yaml) is used as to control my LiftMaster garage door opener.
- Customized version of the [RatGDO Garage Door Controller](https://github.com/ratgdo/esphome-ratgdo/blob/main/static/v25board_esp8266_d1_mini_lite.yaml).

### Garage Fan Thermostat and Utility Gas and Water Meter Pulse Counter

- Project [`utility-counter-gate-fan.yaml`](./utility-counter-gate-fan.yaml) is used as thermostat for cool air ventilation in my garage, and to measure water and gas consumption from my utility meter pulse counters.

## Docker Deployment

- The standard [ESPHome](https://hub.docker.com/r/esphome/esphome) container does not support running as non-root.
- Deploy the [ESPHome-NonRoot](https://github.com/ptr727/ESPHome-NonRoot) container for non-root operation.
- Set directory permissions:
  - `sudo chown -R nonroot:users /data/appdata/esphome`
  - `sudo chmod -R ugo=rwx /data/appdata/esphome`
- Clone Git repository in ESPHome config folder.
  - `cd /data/appdata/esphome/config`
  - `git clone -b develop https://github.com/ptr727/ESPHome-Config .`
- Deploy `secrets.yaml`, use `secrets._yaml` as template.
- In VSCode open remote SSH workspace on docker host, and open workspace from config directory.

## Notes

### General

- Not all [templates](./templates/) are documented here.
- I deployed Zigbee in my home using [Z2M](https://www.zigbee2mqtt.io/) and [TubesZB](https://tubeszb.com/) Zigbee Ethernet coordinator, and no longer use ESPHome flashed smart plugs. For US smart plugs I highly recommend the [Sengled](https://www.amazon.com/gp/product/B092DBFFBY/) Zigbee power monitoring smart plugs.

### Renaming a Device in Home Assistant

- Rename HA entities:
  - Stop HA container using `docker stop home-assistant`.
  - Reset config permissions:
    - `sudo chown -R nobody:users /data/appdata/home-assistant/config`
    - `sudo chmod -R ugo=rwx /data/appdata/home-assistant/config`
  - Edit `core.config_entries` and rename `title` and `host`.
  - Edit `core.device_registry` and rename `name`.
  - Edit `core.entity_registry` and rename `unique_id` and `original_name`.
- Set new ESPHome device name:
  - Set `use_address` in `wifi` config, see [notes](https://esphome.io/components/esphome.html#changing-esphome-node-name).
  - Update firmware.
  - Delete or uncomment `use_address`.
  - Update firmware.
- Restart HA container using `docker start home-assistant`.
- Troubleshooting:
  - Look at ESPHome integration entities, fix incorrect entries.
  - E.g. search for entities named `foo_2`, delete `foo`, and rename `foo_2` to `foo`.
  - E.g. replace short entity names with fully qualified names.
- Note: ESPHome + HA v2024+ made improvements in device and entity naming changes and conflicts, and the listed steps may no longer be required.

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

## TODO

- Norvi issue testing.
- Add `pio system prune` to docker startup.
