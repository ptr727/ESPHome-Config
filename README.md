# ESPHome-Config

ESPHome configuration.

## Deployment

- I run [ESPHome](https://hub.docker.com/r/esphome/esphome) in a Docker container.
  - Run the container as `root`, running as a regular user may result in permission [problems](https://github.com/esphome/issues/issues/3558).
  - Run using `macvlan` and a static IP to support automatic device discovery.
  - Make sure the container user has correct file and directory permissions, e.g.:
    - `sudo chown -R nobody:users /data/appdata/esphome/config`
    - `sudo chmod -R ugo+rwx /data/appdata/esphome/config`
  - Make sure the container user has Git permissions for mixed user file permissions.
    - See Git error [`fatal: detected dubious ownership in repository`](https://github.com/esphome/issues/issues/4519).
    - Run `git config --system --add safe.directory '*'` in the container using e.g. `docker exec -it esphome /bin/bash`.
- Sync this Git repository in ESPHome config folder.
  - `cd /data/appdata/esphome/config`
  - `git pull https://github.com/ptr727/ESPHome-Config .`
- Deploy `secrets.yaml`, use `secrets._yaml` as template.
- Use VSCode and open remote SSH folder.

## Device Templates

### TuyaConvert

- Generic bootstrap [template](./tuya-convert.yaml) used when converting Tuya devices to ESPHome using TuyaConvert.
- See blog [post](https://blog.insanegenius.com/2020/09/10/tuya-to-tasmota-to-esphome/) for firmware conversion details.

### Ayococr X5P WiFi Plug

- [Template](./templates/aoycocr-x5p.yaml) for the [Ayococr X5P](https://www.amazon.com/dp/B07R6CT3G7) US 120V AC WiFi wall plug.
- See blog [post](https://blog.insanegenius.com/2020/09/10/tuya-to-tasmota-to-esphome/) for firmware conversion details.

### EFUN SH331 WiFi Power Monitoring Plug

- [Template](./templates/efun-sh331.yaml) for the [EFUN SH331W](https://www.amazon.com/gp/product/B07DCJ7TDR) US 120V AC WiFi power monitoring wall plug.
- See blog [post](https://blog.insanegenius.com/2020/09/10/tuya-to-tasmota-to-esphome/) for firmware conversion details.

### Sonoff TH10/TH16 WiFi Relay

- [Template](/templates/sonoff-th10.yaml) for the [Sonoff TH10](https://www.amazon.com/Sonoff-Temperature-Monitoring-Assistant-DS18B20/dp/B08DFQ2NP3) and [Sonoff TH16](https://www.amazon.com/Sonoff-Temperature-Humidity-Monitoring-Assistant/dp/B07TF5SYGL) WiFi relay.
- Follow the Tasmota [guide](https://tasmota.github.io/docs/devices/Sonoff-TH/) for flashing instructions, but use the ESPHome firmware.

### Sonoff S31 WiFi Power Monitoring Plug

- [Template](./templates/sonoff-s31.yaml) for the [Sonoff S31](https://www.amazon.com/Sonoff-Monitoring-Certified-Assistant-Supporting/dp/B08GKGS197) US 120V AC WiFi power monitoring wall plug.
- Follow the Tasmota [guide](https://tasmota.github.io/docs/devices/Sonoff-S31/) for flashing instructions, but use the ESPHome firmware.

### Norvi NORVI-ENET-AE06-R DIN Controller

- [Template](./templates/norvi-enet-ae06-r.yaml) for the [Norvi NORVI-ENET-AE06-R](https://shop.norvi.lk/products/norvi-enet-ae06-r) or [SensOper SC-EN-I6-RO4](https://sensoper.com/shop/sc-en-i6-ro4/) ESP32 DIN form factor controllers.
- *Note*: I am experiencing issues with instability in several units, see [the notes](./templates/norvi-enet-ae06-r.yaml) section for details.

### RocketController ASTRA DIN Controller

- [Template](./templates/rocket-astra.yaml) for the [RocketController / RocketDyn ASTRA](https://rocketcontroller.com/product-category/controllers/) ESP32 DIN form factor controllers.

### Kincony KC868-ASR DIN Controller

- [Template](./templates/kincony-kc868-asr.yaml) for the [Kincony KC868-ASR](https://www.kincony.com/esp32-sd-card-rtc-ds3231.html) ESP32 DIN form factor controllers.

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

## Notes

### Hardware Availability

- The Sonoff TH10 and TH16 have been replaced by the [SONOFF TH Origin](https://itead.cc/product/sonoff-th/), see the [Tasmota Templates](https://templates.blakadder.com/sonoff_THR316.html) for pin layouts.
- EFUN SH331W is no longer listed on Amazon.
- I have switched away from WiFi smart plugs and now use [Sengled](https://www.amazon.com/gp/product/B092DBFFBY/) Zigbee power monitoring smart plugs, much easier to deploy.
- Norvi devices were historically not available for purchase in the US at the [Norvi online store](https://shop.norvi.lk), and US users could buy the equivalent SensOper branded products at the [SensOper online store](https://sensoper.com/shop).
- As of November 2023 Norvi does ship to the US from their Sri Lanka based [online store](https://shop.norvi.lk), and Norvi devices can be be shipped to the US from the Germany based [CarTFT](https://www.cartft.com) online store.

### Renaming a Device in Home Assistant

- Rename HA entities:
  - Stop HA container using `docker stop home-assistant`.
  - Reset config permissions:
    - `sudo chown -R nobody:users /data/appdata/home-assistant/config`
    - `sudo chmod -R ugo+rwx /data/appdata/home-assistant/config`
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

### Debugging on Windows WSL

- Install Ubuntu from Microsoft Store.
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
- Install VSCode and Remote Explorer extension.
- Open VSCode Remote WSL Ubuntu session.
  - Install extensions: Python, PlatformIO
  - Clone `ptr727/ESPHome-Config` repo and open workspace.
  - Upload `secrets.yaml`
  - Select default Python interpreter and create virtual environment (Ctrl-Shift-P Python...).
  - Open terminal, make sure venv is active.
  - Install ESPHome (in venv terminal): `pip install wheel esphome`
  - Make sure [ESPHome](https://esphome.io/guides/cli) is installed: `esphome version`
  - Compile ESPHome project: `esphome compile esp32-s3-test.yaml`
  - Upload firmware: `esphome run --device /dev/ttyUSB0 esp32-s3-test.yaml`
- Unbind serial port.
  - Windows: `usbipd detach --busid 7-1`
  - Windows: `usbipd unbind --all`

TODO: No reset after upload?

```console
$ esphome run --device /dev/ttyACM0 esp32-s3-test.yaml
INFO ESPHome 2024.4.2
INFO Reading configuration esp32-s3-test.yaml...
INFO Detected timezone 'America/Los_Angeles'
INFO Generating C++ source...
INFO Compiling app...
Processing esp32-s3-test (board: adafruit_feather_esp32s3_nopsram; framework: espidf; platform: platformio/espressif32@5.4.0)
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
HARDWARE: ESP32S3 240MHz, 320KB RAM, 8MB Flash
 - framework-espidf @ 3.40406.240122 (4.4.6) 
 - tool-cmake @ 3.16.4 
 - tool-ninja @ 1.7.1 
 - toolchain-esp32ulp @ 2.35.0-20220830 
 - toolchain-riscv32-esp @ 8.4.0+2021r2-patch5 
 - toolchain-xtensa-esp32s3 @ 8.4.0+2021r2-patch5
Reading CMake configuration...
No dependencies
RAM:   [=         ]   9.9% (used 32568 bytes from 327680 bytes)
Flash: [==        ]  17.7% (used 696777 bytes from 3932160 bytes)
==================================================================================================================================== [SUCCESS] Took 6.46 seconds ====================================================================================================================================
INFO Successfully compiled program.
esptool.py v4.7.0
Serial port /dev/ttyACM0
Connecting...
Chip is ESP32-S3 (QFN56) (revision v0.1)
Features: WiFi, BLE, Embedded Flash 8MB (GD)
Crystal is 40MHz
MAC: dc:54:75:cf:bc:d8
Uploading stub...
Running stub...
Stub running...
Changing baud rate to 460800
Changed.
Configuring flash size...
Auto-detected Flash size: 8MB
Flash will be erased from 0x00010000 to 0x000bafff...
Flash will be erased from 0x00000000 to 0x00005fff...
Flash will be erased from 0x00008000 to 0x00008fff...
Flash will be erased from 0x00009000 to 0x0000afff...
Compressed 697136 bytes to 453296...
Wrote 697136 bytes (453296 compressed) at 0x00010000 in 4.8 seconds (effective 1171.9 kbit/s)...
Hash of data verified.
Compressed 20912 bytes to 13091...
Wrote 20912 bytes (13091 compressed) at 0x00000000 in 0.3 seconds (effective 537.4 kbit/s)...
Hash of data verified.
Compressed 3072 bytes to 134...
Wrote 3072 bytes (134 compressed) at 0x00008000 in 0.0 seconds (effective 607.9 kbit/s)...
Hash of data verified.
Compressed 8192 bytes to 31...
Wrote 8192 bytes (31 compressed) at 0x00009000 in 0.1 seconds (effective 978.7 kbit/s)...
Hash of data verified.

Leaving...
Hard resetting via RTS pin...
INFO Successfully uploaded program.
INFO Starting log output from /dev/ttyACM0 with baud rate 115200
ERROR Serial port closed!
```

```console
$ esphome run --device /dev/ttyACM0 adafruit-esp32-s3-feather-test.yaml 
INFO ESPHome 2024.4.2
INFO Reading configuration adafruit-esp32-s3-feather-test.yaml...
INFO Detected timezone 'America/Los_Angeles'
WARNING GPIO3 is a strapping PIN and should only be used for I/O with care.
Attaching external pullup/down resistors to strapping pins can cause unexpected failures.
See https://esphome.io/guides/faq.html#why-am-i-getting-a-warning-about-strapping-pins
WARNING GPIO33 is used by the PSRAM interface on ESP32-S3R8 / ESP32-S3R8V and should be avoided on these models
INFO Generating C++ source...
INFO Compiling app...
Processing adafruit-esp32-s3-feather-test (board: adafruit_feather_esp32s3_nopsram; framework: arduino; platform: platformio/espressif32@5.4.0)
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
HARDWARE: ESP32S3 240MHz, 320KB RAM, 8MB Flash
 - toolchain-riscv32-esp @ 8.4.0+2021r2-patch5 
 - toolchain-xtensa-esp32s3 @ 8.4.0+2021r2-patch5
Dependency Graph
|-- WiFi @ 2.0.0
|-- ESPmDNS @ 2.0.0
|-- Update @ 2.0.0
|-- Wire @ 2.0.0
RAM:   [=         ]  14.8% (used 48396 bytes from 327680 bytes)
Flash: [=====     ]  46.6% (used 854709 bytes from 1835008 bytes)
==================================================================================================================================== [SUCCESS] Took 2.29 seconds ====================================================================================================================================
INFO Successfully compiled program.
esptool.py v4.7.0
Serial port /dev/ttyACM0
Connecting...
Chip is ESP32-S3 (QFN56) (revision v0.1)
Features: WiFi, BLE, Embedded Flash 8MB (GD)
Crystal is 40MHz
MAC: dc:54:75:cf:bc:d8
Uploading stub...
Running stub...
Stub running...
Changing baud rate to 460800
Changed.
Configuring flash size...
Auto-detected Flash size: 8MB
Flash will be erased from 0x00010000 to 0x000e0fff...
Flash will be erased from 0x00000000 to 0x00003fff...
Flash will be erased from 0x00008000 to 0x00008fff...
Flash will be erased from 0x0000e000 to 0x0000ffff...
Flash will be erased from 0x002d0000 to 0x002f8fff...
Compressed 855104 bytes to 559172...
Wrote 855104 bytes (559172 compressed) at 0x00010000 in 6.1 seconds (effective 1129.9 kbit/s)...
Hash of data verified.
Warning: Image file at 0x0 is protected with a hash checksum, so not changing the flash size setting. Use the --flash_size=keep option instead of --flash_size=8MB in order to remove this warning, or use the --dont-append-digest option for the elf2image command in order to generate an image file without a hash checksum
Compressed 15040 bytes to 10364...
Wrote 15040 bytes (10364 compressed) at 0x00000000 in 0.2 seconds (effective 483.6 kbit/s)...
Hash of data verified.
Compressed 3072 bytes to 144...
Wrote 3072 bytes (144 compressed) at 0x00008000 in 0.0 seconds (effective 558.8 kbit/s)...
Hash of data verified.
Compressed 8192 bytes to 47...
Wrote 8192 bytes (47 compressed) at 0x0000e000 in 0.1 seconds (effective 838.9 kbit/s)...
Hash of data verified.
Compressed 165536 bytes to 106746...
Wrote 165536 bytes (106746 compressed) at 0x002d0000 in 1.2 seconds (effective 1122.6 kbit/s)...
Hash of data verified.

Leaving...
Hard resetting via RTS pin...
INFO Successfully uploaded program.
INFO Starting log output from /dev/ttyACM0 with baud rate 115200
ERROR Serial port closed!
```