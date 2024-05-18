# ESP32-S3-DEVKITC Firmware Update Problems

## Setup

- ESP32-S3-DEVKITC-1-N32R8V: 32MB Flash, 8MB PSRAM
- ESPHome 2024.5.0: `pip install --upgrade --pre setuptools wheel platformio esphome`
- Python 3.12 : Windows Store (auto updating)
- VSCode : Preview
- Template : `templates\esp32-s3-devkitc.yaml`

## BootLoop

Writing firmware over USB results in boot-loop unless `board_build.arduino.memory_type: opi_opi` is added to config.

- Set default config for [board](https://docs.platformio.org/en/latest/boards/espressif32/esp32-s3-devkitc-1.html):
  - Set `board: esp32-s3-devkitc-1`
  - Set `flash_size: 32MB`
  - Add `psram` section to YAML config.
- Flash over USB-UART, continuous boot-crash repeat, see [CLI USB BootLoop](#cli-usb-bootloop).
- Observe crash report `esp_core_dump_flash: Core dump flash config is corrupted! CRC=0x7bd5c66f instead of 0x0`.
- Add `board_build.arduino.memory_type: opi_opi` to `esphome: platformio_options:`
- No more crash.
- Crash message indicates problem may be related to missing [Dump Partition](#dump-partition).

## OTA

Writing updated firmware OTA reboots device but does not apply new firmware.

- Write firmware over USB-UART, see [CLI USB-UART Programming](#cli-usb-uart-programming).
- Note compilation time `May 18 2024, 08:01:15` in log output `[D][text_sensor:064]: 'esp32-s3-devkitc-test_version': Sending state '2024.5.0 May 18 2024, 08:01:15'`.
- Connect Serial Monitor to USB-UART, press reset button, capture serial output, see [Serial Monitor During OTA](#serial-monitor-during-ota).
- Note new compile time `May 18, 2024 8:21:26 AM` from `>date Saturday, May 18, 2024 8:21:26 AM`.
- Apply firmware update OTA, see [CLI OTA Programming](#cli-ota-programming).
- Note compilation time `May 18 2024, 08:01:15` in log output `[08:22:05][I][app:100]: ESPHome version 2024.5.0 compiled on May 18 2024, 08:01:15`.
- Observe that compile time did not change and OTA did not actually apply a firmware update.

## Dump Partition

Partition file is missing a `dump` partition.

- On device boot it reports `esp_core_dump_flash: No core dump partition found!` error.
- Partition file is missing a `dump` partition, see [PlatformIO Partitions](#platformio-partitions).
- IDF [docs](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/core_dump.html#save-core-dump-to-flash) indicate to either use a partition or configure to dump to UART.

## Output

### CLI USB-UART Programming

```console
> esphome run .\esp32-s3-devkitc-test.yaml    
INFO ESPHome 2024.5.0
INFO Reading configuration .\esp32-s3-devkitc-test.yaml...
WARNING The selected Arduino framework version is not the recommended one. If there are connectivity or build issues please remove the manual version.
INFO Detected timezone 'America/Los_Angeles'
WARNING The selected Arduino framework version is not the recommended one. If there are connectivity or build issues please remove the manual version.
INFO Generating C++ source...
INFO Compiling app...
Processing esp32-s3-devkitc-test (board: esp32-s3-devkitc-1; framework: arduino; platform: platformio/espressif32@5.4.0)
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Verbose mode can be enabled via `-v, --verbose` option
CONFIGURATION: https://docs.platformio.org/page/boards/espressif32/esp32-s3-devkitc-1.html
PLATFORM: Espressif 32 (5.4.0) > Espressif ESP32-S3-DevKitC-1-N8 (8 MB QD, No PSRAM)
HARDWARE: ESP32S3 240MHz, 320KB RAM, 8MB Flash
DEBUG: Current (esp-builtin) On-board (esp-builtin) External (cmsis-dap, esp-bridge, esp-prog, iot-bus-jtag, jlink, minimodule, olimex-arm-usb-ocd, olimex-arm-usb-ocd-h, olimex-arm-usb-tiny-h, olimex-jtag-tiny, tumpa)
PACKAGES: 
 - framework-arduinoespressif32 @ 3.20009.0 (2.0.9) 
 - tool-esptoolpy @ 1.40400.0 (4.4.0) 
 - toolchain-riscv32-esp @ 8.4.0+2021r2-patch5 
 - toolchain-xtensa-esp32s3 @ 8.4.0+2021r2-patch5
LDF: Library Dependency Finder -> https://bit.ly/configure-pio-ldf
LDF Modes: Finder ~ off, Compatibility ~ soft
Found 33 compatible libraries
Scanning dependencies...
Dependency Graph
|-- WiFi @ 2.0.0
|-- ESPmDNS @ 2.0.0
|-- Update @ 2.0.0
Building in release mode
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\api\api_connection.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\api\api_frame_helper.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\api\api_pb2.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\api\api_pb2_service.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\api\api_server.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\api\list_entities.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\api\proto.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\api\subscribe_state.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\api\user_services.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\binary_sensor\automation.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\binary_sensor\binary_sensor.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\binary_sensor\filter.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\button\button.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\debug\debug_component.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\esp32\core.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\esp32\gpio.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\esp32\preferences.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\esp32_rmt_led_strip\led_strip.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\homeassistant\time\homeassistant_time.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\internal_temperature\internal_temperature.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\light\addressable_light.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\light\automation.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\light\esp_color_correction.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\light\esp_hsv_color.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\light\esp_range_view.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\light\light_call.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\light\light_json_schema.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\light\light_output.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\light\light_state.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\logger\logger.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\logger\logger_esp32.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\logger\logger_esp8266.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\logger\logger_host.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\logger\logger_libretiny.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\logger\logger_rp2040.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\md5\md5.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\mdns\mdns_component.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\mdns\mdns_esp32.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\mdns\mdns_esp8266.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\mdns\mdns_host.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\mdns\mdns_libretiny.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\mdns\mdns_rp2040.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\network\util.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\ota\ota_backend_arduino_esp32.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\ota\ota_backend_arduino_esp8266.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\ota\ota_backend_arduino_libretiny.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\ota\ota_backend_arduino_rp2040.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\ota\ota_backend_esp_idf.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\ota\ota_component.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\psram\psram.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\restart\button\restart_button.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\sensor\automation.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\sensor\filter.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\sensor\sensor.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\socket\bsd_sockets_impl.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\socket\lwip_raw_tcp_impl.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\socket\lwip_sockets_impl.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\socket\socket.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\status\status_binary_sensor.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\status_indicator\status_indicator.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\text_sensor\filter.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\text_sensor\text_sensor.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\time\automation.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\time\real_time_clock.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\uptime\uptime_sensor.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\version\version_text_sensor.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\wifi\wifi_component.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\wifi\wifi_component_esp32_arduino.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\wifi\wifi_component_esp8266.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\wifi\wifi_component_esp_idf.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\wifi\wifi_component_libretiny.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\wifi\wifi_component_pico_w.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\wifi_info\wifi_info_text_sensor.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\wifi_signal\wifi_signal_sensor.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\application.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\color.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\component.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\component_iterator.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\controller.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\entity_base.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\helpers.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\log.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\ring_buffer.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\scheduler.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\string_ref.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\time.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\util.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\main.cpp.o
Building .pioenvs\esp32-s3-devkitc-test\bootloader.bin
Generating partitions .pioenvs\esp32-s3-devkitc-test\partitions.bin
esptool.py v4.4
Creating esp32s3 image...
Merged 1 ELF section
Successfully created esp32s3 image.
Compiling .pioenvs\esp32-s3-devkitc-test\lib1cf\WiFi\WiFi.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\lib1cf\WiFi\WiFiAP.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\lib1cf\WiFi\WiFiClient.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\lib1cf\WiFi\WiFiGeneric.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\lib1cf\WiFi\WiFiMulti.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\lib1cf\WiFi\WiFiSTA.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\lib1cf\WiFi\WiFiScan.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\lib1cf\WiFi\WiFiServer.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\lib1cf\WiFi\WiFiUdp.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\libb46\ESPmDNS\ESPmDNS.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\lib4c8\Update\HttpsOTAUpdate.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\lib4c8\Update\Updater.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\Esp.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\FirmwareMSC.cpp.o
Archiving .pioenvs\esp32-s3-devkitc-test\lib1cf\libWiFi.a
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\FunctionalInterrupt.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\HWCDC.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\HardwareSerial.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\IPAddress.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\IPv6Address.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\MD5Builder.cpp.o
Archiving .pioenvs\esp32-s3-devkitc-test\libb46\libESPmDNS.a
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\Print.cpp.o
Archiving .pioenvs\esp32-s3-devkitc-test\lib4c8\libUpdate.a
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\Stream.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\StreamString.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\Tone.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\USB.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\USBCDC.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\USBMSC.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\WMath.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\WString.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\base64.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\cbuf.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-adc.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-bt.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-cpu.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-dac.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-gpio.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-i2c-slave.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-i2c.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-ledc.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-matrix.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-misc.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-psram.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-rgb-led.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-rmt.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-sigmadelta.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-spi.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-time.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-timer.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-tinyusb.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-touch.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-uart.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\firmware_msc_fat.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\libb64\cdecode.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\libb64\cencode.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\main.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\stdlib_noniso.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\wiring_pulse.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\wiring_shift.c.o
Archiving .pioenvs\esp32-s3-devkitc-test\libFrameworkArduino.a
Linking .pioenvs\esp32-s3-devkitc-test\firmware.elf
Retrieving maximum program size .pioenvs\esp32-s3-devkitc-test\firmware.elf
Checking size .pioenvs\esp32-s3-devkitc-test\firmware.elf
Advanced Memory Usage is available via "PlatformIO Home > Project Inspect"
RAM:   [=         ]  14.6% (used 47892 bytes from 327680 bytes)
Flash: [=         ]   5.1% (used 850085 bytes from 16515072 bytes)
Building .pioenvs\esp32-s3-devkitc-test\firmware.bin
esptool.py v4.4
Creating esp32s3 image...
Merged 2 ELF sections
Successfully created esp32s3 image.
esp32_create_combined_bin([".pioenvs\esp32-s3-devkitc-test\firmware.bin"], [".pioenvs\esp32-s3-devkitc-test\firmware.elf"])
esptool.py v4.7.0
Wrote 0xdfa10 bytes to file C:\Users\piete\source\repos\ptr727\ESPHome-Config\.esphome\build\esp32-s3-devkitc-test\.pioenvs\esp32-s3-devkitc-test/firmware-factory.bin, ready to flash to offset 0x0
==================================================================================================================================== [SUCCESS] Took 39.06 seconds ====================================================================================================================================
INFO Successfully compiled program.
Found multiple options for uploading, please choose one:
  [1] COM9 (Silicon Labs CP210x USB to UART Bridge (COM9))
  [2] Over The Air (esp32-s3-devkitc-test.home.insanegenius.net)
(number): 1
esptool.py v4.7.0
Serial port COM9
Connecting...
Chip is ESP32-S3 (QFN56) (revision v0.1)
Features: WiFi, BLE, Embedded PSRAM 8MB (AP_1v8)
Crystal is 40MHz
MAC: 68:b6:b3:3d:63:6c
Uploading stub...
Running stub...
Stub running...
Changing baud rate to 460800
Changed.
Configuring flash size...
Auto-detected Flash size: 32MB
Flash will be erased from 0x00010000 to 0x000dffff...
Flash will be erased from 0x00000000 to 0x00003fff...
Flash will be erased from 0x00008000 to 0x00008fff...
Flash will be erased from 0x0000e000 to 0x0000ffff...
Compressed 850448 bytes to 555522...
Wrote 850448 bytes (555522 compressed) at 0x00010000 in 14.7 seconds (effective 462.5 kbit/s)...
Hash of data verified.
Compressed 14000 bytes to 9717...
Wrote 14000 bytes (9717 compressed) at 0x00000000 in 0.4 seconds (effective 277.1 kbit/s)...
Hash of data verified.
Compressed 3072 bytes to 145...
Wrote 3072 bytes (145 compressed) at 0x00008000 in 0.1 seconds (effective 476.5 kbit/s)...
Hash of data verified.
Compressed 8192 bytes to 47...
Wrote 8192 bytes (47 compressed) at 0x0000e000 in 0.1 seconds (effective 667.2 kbit/s)...
Hash of data verified.

Leaving...
Hard resetting via RTS pin...
INFO Successfully uploaded program.
INFO Starting log output from COM9 with baud rate 115200
[08:02:47]ESP-ROM:esp32s3-20210327
[08:02:47]Build:Mar 27 2021
[08:02:47]rst:0x1 (POWERON),boot:0x8 (SPI_FAST_FLASH_BOOT)
[08:02:47]SPIWP:0xee
[08:02:47]Octal Flash Mode Enabled
[08:02:47]For OPI Flash, Use Default Flash Boot Mode
[08:02:47]mode:SLOW_RD, clock div:1
[08:02:47]load:0x3fce3808,len:0x3ac
[08:02:47]load:0x403c9700,len:0x9b4
[08:02:47]load:0x403cc700,len:0x28fc
[08:02:47]entry 0x403c98bc
[08:02:47]E (259) esp_core_dump_flash: No core dump partition found!
[08:02:47]E (259) esp_core_dump_flash: No core dump partition found!
[08:02:47][I][logger:156]: Log initialized
[08:02:48][C][ota:483]: There have been 1 suspected unsuccessful boot attempts.
[08:02:48][D][esp32.preferences:114]: Saving 1 preferences to flash...
[08:02:48][D][esp32.preferences:143]: Saving 1 preferences to flash: 0 cached, 1 written, 0 failed
[08:02:48][I][app:029]: Running through setup()...
[08:02:48][C][esp32_rmt_led_strip:021]: Setting up ESP32 LED Strip...
[08:02:48][C][light:035]: Setting up light 'esp32-s3-devkitc-test_rgb_led'...
[08:02:48][D][light:036]: 'esp32-s3-devkitc-test_rgb_led' Setting:
[08:02:48][D][light:041]:   Color mode: RGB
[08:02:48][D][light:085]:   Transition length: 1.0s
[08:02:48][D][binary_sensor:034]: 'esp32-s3-devkitc-test_status': Sending initial state OFF
[08:02:48][D][text_sensor:064]: 'esp32-s3-devkitc-test_version': Sending state '2024.5.0 May 18 2024, 08:01:15'
[08:02:48][C][wifi:038]: Setting up WiFi...
[08:02:48][C][wifi:051]: Starting WiFi...
[08:02:48][C][wifi:052]:   Local MAC: 68:B6:B3:3D:63:6C
[08:02:48][D][wifi:464]: Starting scan...
[08:02:48][D][sensor:094]: 'esp32-s3-devkitc-test_internal_temperature': Sending state 34.28920 °C with 1 decimals of accuracy
[08:02:48][D][sensor:094]: 'esp32-s3-devkitc-test_uptime': Sending state 0.00688 min with 0 decimals of accuracy
[08:02:48][I][status_indicator:135]: <>> on_network_disconnected->status_indicator_statustrigger_id_5
[08:02:48][D][light:036]: 'esp32-s3-devkitc-test_rgb_led' Setting:
[08:02:48][D][light:047]:   State: ON
[08:02:48][D][light:051]:   Brightness: 50%
[08:02:48][D][light:059]:   Red: 100%, Green: 0%, Blue: 0%
[08:02:48][D][light:109]:   Effect: 'fast_pulse'
[08:02:48][W][component:157]: Component wifi set Warning flag: unspecified
[08:02:54][D][wifi:479]: Found networks:
[08:02:54][I][wifi:523]: - 'Draadloos' (E4:38:83:55:19:32) ▂▄▆█
[08:02:54][D][wifi:524]:     Channel: 6
[08:02:54][D][wifi:525]:     RSSI: -61 dB
[08:02:54][I][wifi:523]: - 'Draadloos' (E4:38:83:54:BA:4B) ▂▄▆█
[08:02:54][D][wifi:524]:     Channel: 1
[08:02:54][D][wifi:525]:     RSSI: -63 dB
[08:02:54][I][wifi:523]: - 'Draadloos' (AC:8B:A9:D4:F3:16) ▂▄▆█
[08:02:54][D][wifi:524]:     Channel: 6
[08:02:54][D][wifi:525]:     RSSI: -76 dB
[08:02:54][I][wifi:523]: - 'Draadloos' (AC:8B:A9:D4:F2:AE) ▂▄▆█
[08:02:54][D][wifi:524]:     Channel: 11
[08:02:54][D][wifi:525]:     RSSI: -76 dB
[08:02:54][I][wifi:523]: - 'Draadloos' (AC:8B:A9:D4:D8:E6) ▂▄▆█
[08:02:54][D][wifi:524]:     Channel: 11
[08:02:54][D][wifi:525]:     RSSI: -86 dB
[08:02:54][D][wifi:528]: - 'DP20_7A431139373857' (D4:F9:8D:35:7F:49) ▂▄▆█
[08:02:54][D][wifi:528]: - 'Draadloos_Guest' (EA:38:83:54:BA:4B) ▂▄▆█
[08:02:54][D][wifi:528]: - 'Draadloos_Guest' (EA:38:83:55:19:32) ▂▄▆█
[08:02:54][D][wifi:528]: - 'Draadloos_Family' (EE:38:83:54:BA:4B) ▂▄▆█
[08:02:54][D][wifi:528]: - 'Draadloos_Family' (EE:38:83:55:19:32) ▂▄▆█
[08:02:54][D][wifi:528]: - 'Draadloos_Family' (B6:8B:A9:D4:F3:16) ▂▄▆█
[08:02:54][D][wifi:528]: - 'Skaariboon-guest' (72:3A:CB:4B:B1:14) ▂▄▆█
[08:02:54][D][wifi:528]: - 'Skaariboon' (70:3A:CB:4B:B1:16) ▂▄▆█
[08:02:54][D][wifi:528]: - 'Draadloos_Guest' (B2:8B:A9:D4:F3:16) ▂▄▆█
[08:02:54][D][wifi:528]: - 'Draadloos_Guest' (B2:8B:A9:D4:F2:AE) ▂▄▆█
[08:02:54][D][wifi:528]: - 'Draadloos_Family' (B6:8B:A9:D4:F2:AE) ▂▄▆█
[08:02:54][D][wifi:528]: - 'DIRECT-8C1150AC' (66:EB:8C:11:D0:AC) ▂▄▆█
[08:02:54][D][wifi:528]: - 'Skaariboon' (70:3A:CB:A4:67:0F) ▂▄▆█
[08:02:54][D][wifi:528]: - 'Skaariboon-guest' (72:3A:CB:A4:67:0C) ▂▄▆█
[08:02:54][D][wifi:528]: - 'Draadloos_Family' (B6:8B:A9:D4:D8:E6) ▂▄▆█
[08:02:54][D][wifi:528]: - 'Draadloos_Guest' (B2:8B:A9:D4:D8:E6) ▂▄▆█
[08:02:54][D][wifi:528]: - 'Skaariboon' (24:05:88:01:7E:E1) ▂▄▆█
[08:02:54][D][wifi:528]: - 'Skaariboon-guest' (32:FD:38:E7:FE:28) ▂▄▆█
[08:02:54][I][wifi:305]: WiFi Connecting to 'Draadloos'...
[08:02:56][I][wifi:596]: WiFi Connected!
[08:02:56][C][wifi:410]:   Local MAC: 68:B6:B3:3D:63:6C
[08:02:56][C][wifi:415]:   SSID: 'Draadloos'
[08:02:56][C][wifi:418]:   IP Address: 192.168.1.129
[08:02:56][C][wifi:422]:   BSSID: E4:38:83:55:19:32
[08:02:56][C][wifi:423]:   Hostname: 'esp32-s3-devkitc-test'
[08:02:56][C][wifi:425]:   Signal strength: -61 dB ▂▄▆█
[08:02:56][C][wifi:429]:   Channel: 6
[08:02:56][C][wifi:430]:   Subnet: 255.255.255.0
[08:02:56][C][wifi:431]:   Gateway: 192.168.1.1
[08:02:56][C][wifi:432]:   DNS1: 192.168.1.1
[08:02:56][C][wifi:433]:   DNS2: 0.0.0.0
[08:02:56][C][ota:096]: Over-The-Air Updates:
[08:02:56][C][ota:097]:   Address: esp32-s3-devkitc-test.home.insanegenius.net:3232
[08:02:56][C][ota:100]:   Using Password.
[08:02:56][C][ota:103]:   OTA version: 2.
[08:02:56][C][api:025]: Setting up Home Assistant API server...
[08:02:56][I][app:062]: setup() finished successfully!
[08:02:56][D][text_sensor:064]: 'esp32-s3-devkitc-test_wifi_bssid': Sending state 'E4:38:83:55:19:32'
[08:02:56][D][text_sensor:064]: 'esp32-s3-devkitc-test_wifi_ip': Sending state '192.168.1.129'
[08:02:56][D][sensor:094]: 'esp32-s3-devkitc-test_wifi_signal': Sending state -61.00000 dBm with 0 decimals of accuracy
[08:02:56][D][text_sensor:064]: 'esp32-s3-devkitc-test_wifi_ssid': Sending state 'Draadloos'
[08:02:56][D][sensor:094]: 'esp32-s3-devkitc-test_heap_free': Sending state 263408.00000 B with 0 decimals of accuracy
[08:02:56][I][status_indicator:135]: <>> on_turn_off->status_indicator_statustrigger_id
[08:02:56][D][light:036]: 'esp32-s3-devkitc-test_rgb_led' Setting:
[08:02:56][D][light:051]:   Brightness: 25%
[08:02:56][D][light:059]:   Red: 0%, Green: 100%, Blue: 0%
[08:02:56][D][light:085]:   Transition length: 1.0s
[08:02:56][D][light:091]:   Effect: 'None'
[08:02:56][W][component:170]: Component wifi cleared Warning flag
[08:02:56][W][component:157]: Component api set Warning flag: unspecified
[08:02:56][I][app:100]: ESPHome version 2024.5.0 compiled on May 18 2024, 08:01:15
[08:02:56][C][status_indicator:058]: Status Indicator supports:
[08:02:56][C][status_indicator:060]:  * on_api_disconnected: status_indicator_statustrigger_id_6        |       | 0
[08:02:56][C][status_indicator:060]:  * on_app_error: status_indicator_statustrigger_id_2       |       | 0
[08:02:56][C][status_indicator:060]:  * on_app_warning: status_indicator_statustrigger_id_3     |       | 0
[08:02:56][C][status_indicator:060]:  * on_network_disconnected: status_indicator_statustrigger_id_5    |       | 0
[08:02:56][C][status_indicator:060]:  * on_turn_off: status_indicator_statustrigger_id  |       | 0
[08:02:56][C][status_indicator:060]:  * on_wifi_ap_enabled: status_indicator_statustrigger_id_4         |       | 0
[08:02:56][I][status_indicator:135]: <>> on_api_disconnected->status_indicator_statustrigger_id_6
[08:02:56][D][light:036]: 'esp32-s3-devkitc-test_rgb_led' Setting:
[08:02:56][D][light:051]:   Brightness: 50%
[08:02:56][D][light:059]:   Red: 100%, Green: 100%, Blue: 0%
[08:02:56][D][light:109]:   Effect: 'fast_pulse'
[08:02:56][C][wifi:582]: WiFi:
[08:02:56][C][wifi:410]:   Local MAC: 68:B6:B3:3D:63:6C
[08:02:56][C][wifi:415]:   SSID: 'Draadloos'
[08:02:56][C][wifi:418]:   IP Address: 192.168.1.129
[08:02:56][C][wifi:422]:   BSSID: E4:38:83:55:19:32
[08:02:56][C][wifi:423]:   Hostname: 'esp32-s3-devkitc-test'
[08:02:56][C][wifi:425]:   Signal strength: -63 dB ▂▄▆█
[08:02:56][C][wifi:429]:   Channel: 6
[08:02:56][C][wifi:430]:   Subnet: 255.255.255.0
[08:02:56][C][wifi:431]:   Gateway: 192.168.1.1
[08:02:56][C][wifi:432]:   DNS1: 192.168.1.1
[08:02:56][C][wifi:433]:   DNS2: 0.0.0.0
[08:02:56][C][logger:185]: Logger:
[08:02:56][C][logger:186]:   Level: DEBUG
[08:02:56][C][logger:188]:   Log Baud Rate: 115200
[08:02:56][C][logger:189]:   Hardware UART: UART0
[08:02:56][C][uptime.sensor:031]: Uptime Sensor 'esp32-s3-devkitc-test_uptime'
[08:02:56][C][uptime.sensor:031]:   Device Class: 'duration'
[08:02:56][C][uptime.sensor:031]:   State Class: 'total_increasing'
[08:02:56][C][uptime.sensor:031]:   Unit of Measurement: 'min'
[08:02:56][C][uptime.sensor:031]:   Accuracy Decimals: 0
[08:02:56][C][uptime.sensor:031]:   Icon: 'mdi:timer-outline'
[08:02:56][C][esp32_rmt_led_strip:175]: ESP32 RMT LED Strip:
[08:02:56][C][esp32_rmt_led_strip:176]:   Pin: 38
[08:02:56][C][esp32_rmt_led_strip:177]:   Channel: 0
[08:02:56][C][esp32_rmt_led_strip:202]:   RGB Order: GRB
[08:02:56][C][esp32_rmt_led_strip:203]:   Max refresh rate: 0
[08:02:56][C][esp32_rmt_led_strip:204]:   Number of LEDs: 1
[08:02:56][C][light:103]: Light 'esp32-s3-devkitc-test_rgb_led'
[08:02:56][C][light:105]:   Default Transition Length: 1.0s
[08:02:56][C][light:106]:   Gamma Correct: 2.80
[08:02:56][C][restart.button:017]: Restart Button 'esp32-s3-devkitc-test_restart'
[08:02:56][C][status:034]: Status Binary Sensor 'esp32-s3-devkitc-test_status'
[08:02:56][C][status:034]:   Device Class: 'connectivity'
[08:02:56][C][version.text_sensor:021]: Version Text Sensor 'esp32-s3-devkitc-test_version'
[08:02:56][C][version.text_sensor:021]:   Icon: 'mdi:new-box'
[08:02:56][C][internal_temperature:076]: Internal Temperature Sensor 'esp32-s3-devkitc-test_internal_temperature'
[08:02:56][C][internal_temperature:076]:   Device Class: 'temperature'
[08:02:56][C][internal_temperature:076]:   State Class: 'measurement'
[08:02:56][C][internal_temperature:076]:   Unit of Measurement: '°C'
[08:02:57][C][internal_temperature:076]:   Accuracy Decimals: 1
[08:02:57][C][homeassistant.time:010]: Home Assistant Time:
[08:02:57][C][homeassistant.time:011]:   Timezone: 'PST8PDT,M3.2.0,M11.1.0'
[08:02:57][C][psram:020]: PSRAM:
[08:02:57][C][psram:021]:   Available: YES
[08:02:57][C][psram:024]:   Size: 8191 KB
[08:02:57][C][mdns:115]: mDNS:
[08:02:57][C][mdns:116]:   Hostname: esp32-s3-devkitc-test
[08:02:57][C][ota:096]: Over-The-Air Updates:
[08:02:57][C][ota:097]:   Address: esp32-s3-devkitc-test.home.insanegenius.net:3232
[08:02:57][C][ota:100]:   Using Password.
[08:02:57][C][ota:103]:   OTA version: 2.
[08:02:57][C][api:139]: API Server:
[08:02:57][C][api:140]:   Address: esp32-s3-devkitc-test.home.insanegenius.net:6053
[08:02:57][C][api:144]:   Using noise encryption: NO
[08:02:57][C][wifi_info:011]: WifiInfo SSID 'esp32-s3-devkitc-test_wifi_ssid'
[08:02:57][C][wifi_info:012]: WifiInfo BSSID 'esp32-s3-devkitc-test_wifi_bssid'
[08:02:57][C][wifi_info:009]: WifiInfo IPAddress 'esp32-s3-devkitc-test_wifi_ip'
[08:02:57][C][wifi_signal.sensor:009]: WiFi Signal 'esp32-s3-devkitc-test_wifi_signal'
[08:02:57][C][wifi_signal.sensor:009]:   Device Class: 'signal_strength'
[08:02:57][C][wifi_signal.sensor:009]:   State Class: 'measurement'
[08:02:57][C][wifi_signal.sensor:009]:   Unit of Measurement: 'dBm'
[08:02:57][C][wifi_signal.sensor:009]:   Accuracy Decimals: 0
[08:02:57][C][debug:067]: Debug component:
[08:02:57][C][debug:069]:   Device info 'esp32-s3-devkitc-test_device_info'
[08:02:57][C][debug:069]:     Icon: 'mdi:chip'
[08:02:57][C][debug:072]:   Free space on heap 'esp32-s3-devkitc-test_heap_free'
[08:02:57][C][debug:072]:     State Class: ''
[08:02:57][C][debug:072]:     Unit of Measurement: 'B'
[08:02:57][C][debug:072]:     Accuracy Decimals: 0
[08:02:57][C][debug:072]:     Icon: 'mdi:counter'
[08:02:57][D][debug:079]: ESPHome version 2024.5.0
[08:02:57][D][debug:083]: Free Heap Size: 262952 bytes
[08:02:57][D][debug:113]: Flash Chip: Size=32768kB Speed=80MHz Mode=FAST_READ
[08:02:57][D][debug:162]: Chip: Model=ESP32-S3, Features=WIFI_BGN,BLE, Cores=2, Revision=0
[08:02:57][D][debug:170]: ESP-IDF Version: v4.4.4
[08:02:57][D][debug:175]: EFuse MAC: 68:B6:B3:3D:63:6C
[08:02:57][D][debug:275]: Reset Reason: Power On Reset
[08:02:57][D][debug:320]: Wakeup Reason: Unknown
[08:02:57][D][text_sensor:064]: 'esp32-s3-devkitc-test_device_info': Sending state '2024.5.0|Flash: 32768kB Speed:80MHz Mode:FAST_READ|Chip: ESP32-S3 Features:WIFI_BGN,BLE, Cores:2 Revision:0|ESP-IDF: v4.4.4|EFuse MAC: 68:B6:B3:3D:63:6C|Reset: Power On Reset|Wakeup: Unknown'
[08:02:57][D][text_sensor:064]: 'esp32-s3-devkitc-test_reset_reason': Sending state 'Power On Reset'
[08:03:01][D][api:102]: Accepted 192.168.1.27
[08:03:01][W][component:170]: Component api cleared Warning flag
[08:03:01][I][status_indicator:135]: <>> on_turn_off->status_indicator_statustrigger_id
[08:03:01][D][light:036]: 'esp32-s3-devkitc-test_rgb_led' Setting:
[08:03:01][D][light:051]:   Brightness: 25%
[08:03:01][D][light:059]:   Red: 0%, Green: 100%, Blue: 0%
[08:03:01][D][light:085]:   Transition length: 1.0s
[08:03:01][D][light:091]:   Effect: 'None'
[08:03:01][D][binary_sensor:036]: 'esp32-s3-devkitc-test_status': Sending state ON
[08:03:01][D][api.connection:1321]: ESPHome Logs 2024.5.0 (192.168.1.27): Connected successfully
[08:03:01][D][time:051]: Synchronized time: 2024-05-18 08:03:00
[08:03:07][D][api:102]: Accepted 192.168.1.26
[08:03:07][D][api.connection:1321]: Home Assistant 2024.5.4 (192.168.1.26): Connected successfully
[08:03:07][D][time:051]: Synchronized time: 2024-05-18 08:03:05
[08:03:27][D][sensor:094]: 'esp32-s3-devkitc-test_internal_temperature': Sending state 36.04360 °C with 1 decimals of accuracy
[08:03:31][D][sensor:094]: 'esp32-s3-devkitc-test_uptime': Sending state 0.72845 min with 0 decimals of accuracy
[08:03:45][D][sensor:094]: 'esp32-s3-devkitc-test_wifi_signal': Sending state -62.00000 dBm with 0 decimals of accuracy
[08:03:56][D][sensor:094]: 'esp32-s3-devkitc-test_heap_free': Sending state 260576.00000 B with 0 decimals of accuracy
[08:04:27][D][sensor:094]: 'esp32-s3-devkitc-test_internal_temperature': Sending state 36.92080 °C with 1 decimals of accuracy
[08:04:31][D][sensor:094]: 'esp32-s3-devkitc-test_uptime': Sending state 1.72845 min with 0 decimals of accuracy
[08:04:45][D][sensor:094]: 'esp32-s3-devkitc-test_wifi_signal': Sending state -62.00000 dBm with 0 decimals of accuracy
```

### CLI OTA Programming

```console
> date

Saturday, May 18, 2024 8:21:26 AM

PS C:\Users\piete\source\repos\ptr727\ESPHome-Config> esphome run .\esp32-s3-devkitc-test.yaml
INFO ESPHome 2024.5.0
INFO Reading configuration .\esp32-s3-devkitc-test.yaml...
WARNING The selected Arduino framework version is not the recommended one. If there are connectivity or build issues please remove the manual version.
INFO Detected timezone 'America/Los_Angeles'
WARNING The selected Arduino framework version is not the recommended one. If there are connectivity or build issues please remove the manual version.
INFO Generating C++ source...
INFO Compiling app...
Processing esp32-s3-devkitc-test (board: esp32-s3-devkitc-1; framework: arduino; platform: platformio/espressif32@5.4.0)
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Verbose mode can be enabled via `-v, --verbose` option
CONFIGURATION: https://docs.platformio.org/page/boards/espressif32/esp32-s3-devkitc-1.html
PLATFORM: Espressif 32 (5.4.0) > Espressif ESP32-S3-DevKitC-1-N8 (8 MB QD, No PSRAM)
HARDWARE: ESP32S3 240MHz, 320KB RAM, 8MB Flash
DEBUG: Current (esp-builtin) On-board (esp-builtin) External (cmsis-dap, esp-bridge, esp-prog, iot-bus-jtag, jlink, minimodule, olimex-arm-usb-ocd, olimex-arm-usb-ocd-h, olimex-arm-usb-tiny-h, olimex-jtag-tiny, tumpa)
PACKAGES: 
 - framework-arduinoespressif32 @ 3.20009.0 (2.0.9) 
 - tool-esptoolpy @ 1.40400.0 (4.4.0) 
 - toolchain-riscv32-esp @ 8.4.0+2021r2-patch5 
 - toolchain-xtensa-esp32s3 @ 8.4.0+2021r2-patch5
LDF: Library Dependency Finder -> https://bit.ly/configure-pio-ldf
LDF Modes: Finder ~ off, Compatibility ~ soft
Found 33 compatible libraries
Scanning dependencies...
Dependency Graph
|-- WiFi @ 2.0.0
|-- ESPmDNS @ 2.0.0
|-- Update @ 2.0.0
Building in release mode
Retrieving maximum program size .pioenvs\esp32-s3-devkitc-test\firmware.elf
Checking size .pioenvs\esp32-s3-devkitc-test\firmware.elf
Advanced Memory Usage is available via "PlatformIO Home > Project Inspect"
RAM:   [=         ]  14.6% (used 47892 bytes from 327680 bytes)
Flash: [=         ]   5.1% (used 850085 bytes from 16515072 bytes)
==================================================================================================================================== [SUCCESS] Took 4.20 seconds ====================================================================================================================================
INFO Successfully compiled program.
Found multiple options for uploading, please choose one:
  [1] COM9 (Silicon Labs CP210x USB to UART Bridge (COM9))
  [2] Over The Air (esp32-s3-devkitc-test.home.insanegenius.net)
(number): 2
INFO Resolving IP address of esp32-s3-devkitc-test.home.insanegenius.net
INFO  -> 192.168.1.129
INFO Uploading .\.esphome\build\esp32-s3-devkitc-test\.pioenvs\esp32-s3-devkitc-test\firmware.bin (850448 bytes)
Uploading: [============================================================] 100% Done...

INFO Upload took 5.72 seconds, waiting for result...
INFO OTA successful
INFO Successfully uploaded program.
INFO Starting log output from esp32-s3-devkitc-test.home.insanegenius.net using esphome API
INFO Successfully connected to esp32-s3-devkitc-test @ 192.168.1.129 in 15.170s
INFO Successful handshake with esp32-s3-devkitc-test @ 192.168.1.129 in 0.029s
[08:22:05][I][app:100]: ESPHome version 2024.5.0 compiled on May 18 2024, 08:01:15
[08:22:05][C][status_indicator:058]: Status Indicator supports:
[08:22:05][C][status_indicator:060]:  * on_api_disconnected: status_indicator_statustrigger_id_6        |       | 0
[08:22:05][C][status_indicator:060]:  * on_app_error: status_indicator_statustrigger_id_2       |       | 0
[08:22:05][C][status_indicator:060]:  * on_app_warning: status_indicator_statustrigger_id_3     |       | 0
[08:22:05][C][status_indicator:060]:  * on_network_disconnected: status_indicator_statustrigger_id_5    |       | 0
[08:22:05][C][status_indicator:060]:  * on_turn_off: status_indicator_statustrigger_id  |       | 0
[08:22:05][C][status_indicator:060]:  * on_wifi_ap_enabled: status_indicator_statustrigger_id_4         |       | 0
[08:22:05][C][wifi:582]: WiFi:
[08:22:05][C][wifi:410]:   Local MAC: 68:B6:B3:3D:63:6C
[08:22:05][C][wifi:415]:   SSID: 'Draadloos'
[08:22:05][C][wifi:418]:   IP Address: 192.168.1.129
[08:22:05][C][wifi:422]:   BSSID: E4:38:83:55:19:32
[08:22:05][C][wifi:423]:   Hostname: 'esp32-s3-devkitc-test'
[08:22:05][C][wifi:425]:   Signal strength: -62 dB ▂▄▆█
[08:22:05][C][wifi:429]:   Channel: 6
[08:22:05][C][wifi:430]:   Subnet: 255.255.255.0
[08:22:05][C][wifi:431]:   Gateway: 192.168.1.1
[08:22:05][C][wifi:432]:   DNS1: 192.168.1.1
[08:22:05][C][wifi:433]:   DNS2: 0.0.0.0
[08:22:05][C][logger:185]: Logger:
[08:22:05][C][logger:186]:   Level: DEBUG
[08:22:05][C][logger:188]:   Log Baud Rate: 115200
[08:22:05][C][logger:189]:   Hardware UART: UART0
[08:22:05][C][uptime.sensor:031]: Uptime Sensor 'esp32-s3-devkitc-test_uptime'
[08:22:05][C][uptime.sensor:031]:   Device Class: 'duration'
[08:22:05][C][uptime.sensor:031]:   State Class: 'total_increasing'
[08:22:05][C][uptime.sensor:031]:   Unit of Measurement: 'min'
[08:22:05][C][uptime.sensor:031]:   Accuracy Decimals: 0
[08:22:05][C][uptime.sensor:031]:   Icon: 'mdi:timer-outline'
[08:22:05][C][esp32_rmt_led_strip:175]: ESP32 RMT LED Strip:
[08:22:05][C][esp32_rmt_led_strip:176]:   Pin: 38
[08:22:05][C][esp32_rmt_led_strip:177]:   Channel: 0
[08:22:05][C][esp32_rmt_led_strip:202]:   RGB Order: GRB
[08:22:05][C][esp32_rmt_led_strip:203]:   Max refresh rate: 0
[08:22:05][C][esp32_rmt_led_strip:204]:   Number of LEDs: 1
[08:22:05][C][light:103]: Light 'esp32-s3-devkitc-test_rgb_led'
[08:22:05][C][light:105]:   Default Transition Length: 1.0s
[08:22:05][C][light:106]:   Gamma Correct: 2.80
[08:22:05][C][restart.button:017]: Restart Button 'esp32-s3-devkitc-test_restart'
[08:22:05][C][status:034]: Status Binary Sensor 'esp32-s3-devkitc-test_status'
[08:22:05][C][status:034]:   Device Class: 'connectivity'
[08:22:05][C][version.text_sensor:021]: Version Text Sensor 'esp32-s3-devkitc-test_version'
[08:22:05][C][version.text_sensor:021]:   Icon: 'mdi:new-box'
[08:22:05][C][internal_temperature:076]: Internal Temperature Sensor 'esp32-s3-devkitc-test_internal_temperature'
[08:22:05][C][internal_temperature:076]:   Device Class: 'temperature'
[08:22:05][C][internal_temperature:076]:   State Class: 'measurement'
[08:22:05][C][internal_temperature:076]:   Unit of Measurement: '°C'
[08:22:05][C][internal_temperature:076]:   Accuracy Decimals: 1
[08:22:05][C][homeassistant.time:010]: Home Assistant Time:
[08:22:05][C][homeassistant.time:011]:   Timezone: 'PST8PDT,M3.2.0,M11.1.0'
[08:22:05][C][psram:020]: PSRAM:
[08:22:05][C][psram:021]:   Available: YES
[08:22:05][C][psram:024]:   Size: 8191 KB
[08:22:05][C][mdns:115]: mDNS:
[08:22:05][C][mdns:116]:   Hostname: esp32-s3-devkitc-test
[08:22:05][C][ota:096]: Over-The-Air Updates:
[08:22:05][C][ota:097]:   Address: esp32-s3-devkitc-test.home.insanegenius.net:3232
[08:22:05][C][ota:100]:   Using Password.
[08:22:05][C][ota:103]:   OTA version: 2.
[08:22:05][C][api:139]: API Server:
[08:22:05][C][api:140]:   Address: esp32-s3-devkitc-test.home.insanegenius.net:6053
[08:22:05][C][api:144]:   Using noise encryption: NO
[08:22:05][C][wifi_info:011]: WifiInfo SSID 'esp32-s3-devkitc-test_wifi_ssid'
[08:22:05][C][wifi_info:012]: WifiInfo BSSID 'esp32-s3-devkitc-test_wifi_bssid'
[08:22:05][C][wifi_info:009]: WifiInfo IPAddress 'esp32-s3-devkitc-test_wifi_ip'
[08:22:05][C][wifi_signal.sensor:009]: WiFi Signal 'esp32-s3-devkitc-test_wifi_signal'
[08:22:05][C][wifi_signal.sensor:009]:   Device Class: 'signal_strength'
[08:22:05][C][wifi_signal.sensor:009]:   State Class: 'measurement'
[08:22:05][C][wifi_signal.sensor:009]:   Unit of Measurement: 'dBm'
[08:22:05][C][wifi_signal.sensor:009]:   Accuracy Decimals: 0
[08:22:05][C][debug:067]: Debug component:
[08:22:05][C][debug:069]:   Device info 'esp32-s3-devkitc-test_device_info'
[08:22:05][C][debug:069]:     Icon: 'mdi:chip'
[08:22:05][C][debug:072]:   Free space on heap 'esp32-s3-devkitc-test_heap_free'
[08:22:05][C][debug:072]:     State Class: ''
[08:22:05][C][debug:072]:     Unit of Measurement: 'B'
[08:22:05][C][debug:072]:     Accuracy Decimals: 0
[08:22:05][C][debug:072]:     Icon: 'mdi:counter'
[08:22:05][D][debug:079]: ESPHome version 2024.5.0
[08:22:05][D][debug:083]: Free Heap Size: 245748 bytes
[08:22:05][D][debug:113]: Flash Chip: Size=32768kB Speed=80MHz Mode=FAST_READ
[08:22:05][D][debug:162]: Chip: Model=ESP32-S3, Features=WIFI_BGN,BLE, Cores=2, Revision=0
[08:22:05][D][debug:170]: ESP-IDF Version: v4.4.4
[08:22:05][D][debug:175]: EFuse MAC: 68:B6:B3:3D:63:6C
[08:22:05][D][debug:275]: Reset Reason: Software Reset CPU
[08:22:05][D][debug:320]: Wakeup Reason: Unknown
[08:22:05][D][text_sensor:064]: 'esp32-s3-devkitc-test_device_info': Sending state '2024.5.0|Flash: 32768kB Speed:80MHz Mode:FAST_READ|Chip: ESP32-S3 Features:WIFI_BGN,BLE, Cores:2 Revision:0|ESP-IDF: v4.4.4|EFuse MAC: 68:B6:B3:3D:63:6C|Reset: Software Reset CPU|Wakeup: Unknown'
[08:22:05][D][text_sensor:064]: 'esp32-s3-devkitc-test_reset_reason': Sending state 'Software Reset CPU'
[08:22:25][D][sensor:094]: 'esp32-s3-devkitc-test_internal_temperature': Sending state 39.99100 °C with 1 decimals of accuracy
[08:22:32][D][sensor:094]: 'esp32-s3-devkitc-test_heap_free': Sending state 258392.00000 B with 0 decimals of accuracy
[08:22:32][D][sensor:094]: 'esp32-s3-devkitc-test_uptime': Sending state 0.72653 min with 0 decimals of accuracy
[08:22:36][D][sensor:094]: 'esp32-s3-devkitc-test_wifi_signal': Sending state -62.00000 dBm with 0 decimals of accuracy
[08:23:25][D][sensor:094]: 'esp32-s3-devkitc-test_internal_temperature': Sending state 39.11380 °C with 1 decimals of accuracy
[08:23:32][D][sensor:094]: 'esp32-s3-devkitc-test_heap_free': Sending state 258392.00000 B with 0 decimals of accuracy
[08:23:32][D][sensor:094]: 'esp32-s3-devkitc-test_uptime': Sending state 1.72650 min with 0 decimals of accuracy
[08:23:36][D][sensor:094]: 'esp32-s3-devkitc-test_wifi_signal': Sending state -60.00000 dBm with 0 decimals of accuracy
[08:24:25][D][sensor:094]: 'esp32-s3-devkitc-test_internal_temperature': Sending state 38.23660 °C with 1 decimals of accuracy
[08:24:32][D][sensor:094]: 'esp32-s3-devkitc-test_heap_free': Sending state 258392.00000 B with 0 decimals of accuracy
[08:24:32][D][sensor:094]: 'esp32-s3-devkitc-test_uptime': Sending state 2.72650 min with 0 decimals of accuracy
[08:24:36][D][sensor:094]: 'esp32-s3-devkitc-test_wifi_signal': Sending state -62.00000 dBm with 0 decimals of accuracy
WARNING esp32-s3-devkitc-test @ 192.168.1.129: Connection error occurred: [WinError 64] The specified network name is no longer available
INFO Processing unexpected disconnect from ESPHome API for esp32-s3-devkitc-test @ 192.168.1.129
WARNING Disconnected from API
INFO Successfully connected to esp32-s3-devkitc-test @ 192.168.1.129 in 0.018s
INFO Successful handshake with esp32-s3-devkitc-test @ 192.168.1.129 in 0.012s
[08:25:46][D][api.connection:197]: ESPHome Logs 2024.5.0 (192.168.1.15) requested disconnected
INFO Processing expected disconnect from ESPHome API for esp32-s3-devkitc-test @ 192.168.1.129
WARNING Disconnected from API
```

### Serial Monitor During OTA

```console
---- Opened the serial port COM9 ----
ESP-ROM:esp32s3-20210327
Build:Mar 27 2021
rst:0x1 (POWERON),boot:0x8 (SPI_FAST_FLASH_BOOT)
SPIWP:0xee
Octal Flash Mode Enabled
For OPI Flash, Use Default Flash Boot Mode
mode:SLOW_RD, clock div:1
load:0x3fce3808,len:0x3ac
load:0x403c9700,len:0x9b4
load:0x403cc700,len:0x28fc
entry 0x403c98bc
E (259) esp_core_dump_flash: No core dump partition found!
E (259) esp_core_dump_flash: No core dump partition f[I][logger:156]: Log initialized
[C][ota:483]: There have been 0 suspected unsuccessful boot attempts.
[D][esp32.preferences:114]: Saving 1 preferences to flash...
[D][esp32.preferences:143]: Saving 1 preferences to flash: 0 cached, 1 written, 0 failed
[I][app:029]: Running through setup()...
[C][esp32_rmt_led_strip:021]: Setting up ESP32 LED Strip...
[C][light:035]: Setting up light 'esp32-s3-devkitc-test_rgb_led'...
[D][light:036]: 'esp32-s3-devkitc-test_rgb_led' Setting:
[D][light:041]:   Color mode: RGB
[D][light:085]:   Transition length: 1.0s
[D][binary_sensor:034]: 'esp32-s3-devkitc-test_status': Sending initial state OFF
[D][text_sensor:064]: 'esp32-s3-devkitc-test_version': Sending state '2024.5.0 May 18 2024, 08:01:15'
[C][wifi:038]: Setting up WiFi...
[C][wifi:051]: Starting WiFi...
[C][wifi:052]:   LocalÂ MAC: 68:B6:B3:3D:63:6C
[D][wifi:464]: Starting scan...
[D][sensor:094]: 'esp32-s3-devkitc-test_uptime': Sending state 0.00668 min with 0 decimals of accuracy
[D][sensor:094]: 'esp32-s3-devkitc-test_internal_temperature': Sending state 38.67520 Â°C with 1 decimals of accuracy
[I][status_indicator:135]: <>> on_network_disconnected->status_indicator_statustrigger_id_5
[D][light:036]: 'esp32-s3-devkitc-test_rgb_led' Setting:
[D][light:047]:   State: ON
[D][light:051]:   Brightness: 50%
[D][light:059]:   Red: 100%, Green: 0%, Blue: 0%
[D][light:109]:   Effect: 'fast_pulse'
[W][component:157]: Component wifi set Warning flag: unspecified
[D][wifi:479]: Found networks:
[I][wifi:523]: - 'Draadloos' (E4:38:83:55:19:32) ââ
                                                   ââ
[D][wifi:524]:     Channel: 6
[D][wifi:525]:     RSSI: -61 dB
[I][wifi:523]: - 'Draadloos' (AC:8B:A9:D4:F3:16) ââ
                                                   ââ
[D][wifi:524]:     Channel: 6
[D][wifi:525]:     RSSI: -62 dB
[I][wifi:523]: - 'Draadloos' (E4:38:83:54:BA:4B) ââ
                                                   ââ
[D][wifi:524]:     Channel: 1
[D][wifi:525]:     RSSI: -65 dB
[I][wifi:523]: - 'Draadloos' (AC:8B:A9:D4:F2:AE) ââ
                                                   ââ
[D][wifi:524]:     Channel: 11
[D][wifi:525]:     RSSI: -73 dB
[I][wifi:523]: - 'Draadloos' (AC:8B:A9:D4:D8:E6) ââ
                                                   ââ
[D][wifi:524]:     Channel: 11
[D][wifi:525]:     RSSI: -88 dB
[D][wifi:528]: - 'DP20_7A431139373857' (D4:F9:8D:35:7F:49) ââ
                                                             ââ
[D][wifi:528]: - 'Draadloos_Family' (B6:8B:A9:D4:F3:16) ââ
                                                          ââ
[D][wifi:528]: - 'Draadloos_Guest' (EA:38:83:55:19:32) ââ
                                                         ââ
[D][wifi:528]: - 'Draadloos_Family' (EE:38:83:55:19:32) ââ
                                                          ââ
[D][wifi:528]: - 'Draadloos_Guest' (B2:8B:A9:D4:F3:16) ââ
                                                         ââ
[D][wifi:528]: - 'Draadloos_Guest' (EA:38:83:54:BA:4B) ââ
                                                         ââ
[D][wifi:528]: - 'Draadloos_Family' (EE:38:83:54:BA:4B) ââ
                                                          ââ
[D][wifi:528]: - 'Skaariboon' (70:3A:CB:4B:B1:16) ââ
                                                    ââ
[D][wifi:528]: - 'Skaariboon-guest' (72:3A:CB:4B:B1:14) ââ
                                                          ââ
[D][wifi:528]: - 'Draadloos_Guest' (B2:8B:A9:D4:F2:AE) ââ
                                                         ââ
[D][wifi:528]: - 'Draadloos_Family' (B6:8B:A9:D4:F2:AE) ââ
                                                          ââ
[D][wifi:528]: - 'Skaariboon-guest' (72:3A:CB:A4:67:0C) ââ
                                                          ââ
[D][wifi:528]: - 'Skaariboon' (24:05:88:01:7E:E1) ââ
                                                    ââ
[D][wifi:528]: - 'DIRECT-8C1150AC' (66:EB:8C:11:D0:AC) ââ
                                                         ââ
[D][wifi:528]: - 'Draadloos_Guest' (B2:8B:A9:D4:D8:E6) ââ
                                                         ââ
[D][wifi:528]: - 'Draadloos_Family' (B6:8B:A9:D4:D8:E6) ââ
                                                          ââ
[D][wifi:528]: - 'Skaariboon-guest' (32:FD:38:E7:F2:20) ââ
                                                          ââ
[D][wifi:528]: - 'Skaariboon' (30:FD:38:E7:F2:23) ââ
                                                    ââ
[D][wifi:528]: - 'Skaariboon-guest' (32:FD:38:E7:FE:28) ââ
                                                          ââ
[D][wifi:528]: - 'Skaariboon' (30:FD:38:E7:FE:2B) ââ
                                                    ââ
[I][wifi:305]: WiFi Connecting to 'Draadloos'...
[I][wifi:596]: WiFi Connected!
[C][wifi:410]:   Local MAC: 68:B6:B3:3D:63:6C
[C][wifi:415]:   SSID: 'Draadloos'
[C][wifi:418]:   IP Address: 192.168.1.129
[C][wifi:422]:   BSSID: E4:38:83:55:19:32
[C][wifi:423]:   Hostname: 'esp32-s3-devkitc-test'
[C][wifi:425]:   Signal strength: -61 dB ââ
                                           ââ
[C][wifi:429]:   Channel: 6
[C][wifi:430]:   Subnet: 255.255.255.0
[C][wifi:431]:   Gateway: 192.168.1.1
[C][wifi:432]:   DNS1: 192.168.1.1
[C][wifi:433]:   DNS2: 0.0.0.0
[C][ota:096]: Over-The-Air Updates:
[C][ota:097]:   Address: esp32-s3-devkitc-test.home.insanegenius.net:3232
[C][ota:100]:   Using Password.
[C][ota:103]:   OTA version: 2.
[C][api:025]: Setting up Home Assistant API server...
[I][app:062]: setup() finished successfully!
[D][text_sensor:064]: 'esp32-s3-devkitc-test_wifi_ssid': Sending state 'Draadloos'
[D][text_sensor:064]: 'esp32-s3-devkitc-test_wifi_bssid': Sending state 'E4:38:83:55:19:32'
[D][text_sensor:064]: 'esp32-s3-devkitc-test_wifi_ip': Sending state '192.168.1.129'
[D][sensor:094]: 'esp32-s3-devkitc-test_heap_free': Sending state 263152.00000 B with 0 decimals of accuracy
[D][sensor:094]: 'esp32-s3-devkitc-test_wifi_signal': Sending state -61.00000 dBm with 0 decimals of accuracy
[I][status_indicator:135]: <>> on_turn_off->status_indicator_statustrigger_id
[D][light:036]: 'esp32-s3-devkitc-test_rgb_led' Setting:
[D][light:051]:   Brightness: 25%
[D][light:059]:   Red: 0%, Green: 100%, Blue: 0%
[D][light:085]:   Transition length: 1.0s
[D][light:091]:   Effect: 'None'
[W][component:170]: Component wifi cleared Warning flag
[W][component:157]: Component api set Warning flag: unspecified
[I][app:100]: ESPHome version 2024.5.0 compiled on May 18 2024, 08:01:15
[C][status_indicator:058]: Status Indicator supports:
[C][status_indicator:060]:  * on_api_disconnected: status_indicator_statustrigger_id_6  |       | 0
[C][status_indicator:060]:  * on_app_error: status_indicator_statustrigger_id_2         |       | 0
[C][status_indicator:060]:  * on_app_warning: status_indicator_statustrigger_id_3       |       | 0
[C][status_indicator:060]:  * on_network_disconnected: status_indicator_statustrigger_id_5      |       | 0
[C][status_indicator:060]:  * on_turn_off: status_indicator_statustrigger_id    |       | 0
[C][status_indicator:060]:  * on_wifi_ap_enabled: status_indicator_statustrigger_id_4   |       | 0
[I][status_indicator:135]: <>> on_api_disconnected->status_indicator_statustrigger_id_6
[D][light:036]: 'esp32-s3-devkitc-test_rgb_led' Setting:
[D][light:051]:   Brightness: 50%
[D][light:059]:   Red: 100%, Green: 100%, Blue: 0%
[D][light:109]:   Effect: 'fast_pulse'
[C][wifi:582]: WiFi:
[C][wifi:410]:   Local MAC: 68:B6:B3:3D:63:6C
[C][wifi:415]:   SSID: 'Draadloos'
[C][wifi:418]:   IP Address: 192.168.1.129
[C][wifi:422]:   BSSID: E4:38:83:55:19:32
[C][wifi:423]:   Hostname: 'esp32-s3-devkitc-test'
[C][wifi:425]:   Signal strength: -61 dB ââ
                                           ââ
[C][wifi:429]:   Channel: 6
[C][wifi:430]:   Subnet: 255.255.255.0
[C][wifi:431]:   Gateway: 192.168.1.1
[C][wifi:432]:   DNS1: 192.168.1.1
[C][wifi:433]:   DNS2: 0.0.0.0
[C][logger:185]: Logger:
[C][logger:186]:   Level: DEBUG
[C][logger:188]:   Log Baud Rate: 115200
[C][logger:189]:   Hardware UART: UART0
[C][uptime.sensor:031]: Uptime Sensor 'esp32-s3-devkitc-test_uptime'
[C][uptime.sensor:031]:   Device Class: 'duration'
[C][uptime.sensor:031]:   State Class: 'total_increasing'
[C][uptime.sensor:031]:   Unit of Measurement: 'min'
[C][uptime.sensor:031]:   Accuracy Decimals: 0
[C][uptime.sensor:031]:   Icon: 'mdi:timer-outline'
[C][esp32_rmt_led_strip:175]: ESP32 RMT LED Strip:
[C][esp32_rmt_led_strip:176]:   Pin: 38
[C][esp32_rmt_led_strip:177]:   Channel: 0
[C][esp32_rmt_led_strip:202]:   RGB Order: GRB
[C][esp32_rmt_led_strip:203]:   Max refresh rate: 0
[C][esp32_rmt_led_strip:204]:   Number of LEDs: 1
[C][light:103]: Light 'esp32-s3-devkitc-test_rgb_led'
[C][light:105]:   Default Transition Length: 1.0s
[C][light:106]:   Gamma Correct: 2.80
[C][restart.button:017]: Restart Button 'esp32-s3-devkitc-test_restart'
[C][status:034]: Status Binary Sensor 'esp32-s3-devkitc-test_status'
[C][status:034]:   Device Class: 'connectivity'
[C][version.text_sensor:021]: Version Text Sensor 'esp32-s3-devkitc-test_version'
[C][version.text_sensor:021]:   Icon: 'mdi:new-box'
[C][internal_temperature:076]: Internal Temperature Sensor 'esp32-s3-devkitc-test_internal_temperature'
[C][internal_temperature:076]:   Device Class: 'temperature'
[C][internal_temperature:076]:   State Class: 'measurement'
[C][internal_temperature:076]:   Unit of Measurement: 'Â°C'
[C][internal_temperature:076]:   Accuracy Decimals: 1
[C][homeassistant.time:010]: Home Assistant Time:
[C][homeassistant.time:011]:   Timezone: 'PST8PDT,M3.2.0,M11.1.0'
[C][psram:020]: PSRAM:
[C][psram:021]:   Available: YES
[C][psram:024]:   Size: 8191 KB
[C][mdns:115]: mDNS:
[C][mdns:116]:   Hostname: esp32-s3-devkitc-test
[C][ota:096]: Over-The-Air Updates:
[C][ota:097]:   Address: esp32-s3-devkitc-test.home.insanegenius.net:3232
[C][ota:100]:   Using Password.
[C][ota:103]:   OTA version: 2.
[C][api:139]: API Server:
[C][api:140]:   Address: esp32-s3-devkitc-test.home.insanegenius.net:6053
[C][api:144]:   Using noise encryption: NO
[C][wifi_info:011]: WifiInfo SSID 'esp32-s3-devkitc-test_wifi_ssid'
[C][wifi_info:012]: WifiInfo BSSID 'esp32-s3-devkitc-test_wifi_bssid'
[C][wifi_info:009]: WifiInfo IPAddress 'esp32-s3-devkitc-test_wifi_ip'
[C][wifi_signal.sensor:009]: WiFi Signal 'esp32-s3-devkitc-test_wifi_signal'
[C][wifi_signal.sensor:009]:   Device Class: 'signal_strength'
[C][wifi_signal.sensor:009]:   State Class: 'measurement'
[C][wifi_signal.sensor:009]:   Unit of Measurement: 'dBm'
[C][wifi_signal.sensor:009]:   Accuracy Decimals: 0
[C][debug:067]: Debug component:
[C][debug:069]:   Device info 'esp32-s3-devkitc-test_device_info'
[C][debug:069]:     Icon: 'mdi:chip'
[C][debug:072]:   Free space on heap 'esp32-s3-devkitc-test_heap_free'
[C][debug:072]:     State Class: ''
[C][debug:072]:     Unit of Measurement: 'B'
[C][debug:072]:     Accuracy Decimals: 0
[C][debug:072]:     Icon: 'mdi:counter'
[D][debug:079]: ESPHome version 2024.5.0
[D][debug:083]: Free Heap Size: 262704 bytes
[D][debug:113]: Flash Chip: Size=32768kB Speed=80MHz Mode=FAST_READ
[D][debug:162]: Chip: Model=ESP32-S3, Features=WIFI_BGN,BLE, Cores=2, Revision=0
[D][debug:170]: ESP-IDF Version: v4.4.4
[D][debug:175]: EFuse MAC: 68:B6:B3:3D:63:6C
[D][debug:275]: Reset Reason: Power On Reset
[D][debug:320]: Wakeup Reason: Unknown
[D][text_sensor:064]: 'esp32-s3-devkitc-test_device_info': Sending state '2024.5.0|Flash: 32768kB Speed:80MHz Mode:FAST_READ|Chip: ESP32-S3 Features:WIFI_BGN,BLE, Cores:2 Revision:0|ESP-IDF: v4.4.4|EFuse MAC: 68:B6:B3:3D:63:6C|Reset: Power On Reset|Wakeup: Unknown'
[D][text_sensor:064]: 'esp32-s3-devkitc-test_reset_reason': Sending state 'Power On Reset'
[D][api:102]: Accepted 192.168.1.27
[W][component:170]: Component api cleared Warning flag
[I][status_indicator:135]: <>> on_turn_off->status_indicator_statustrigger_id
[D][light:036]: 'esp32-s3-devkitc-test_rgb_led' Setting:
[D][light:051]:   Brightness: 25%
[D][light:059]:   Red: 0%, Green: 100%, Blue: 0%
[D][light:085]:   Transition length: 1.0s
[D][light:091]:   Effect: 'None'
[D][binary_sensor:036]: 'esp32-s3-devkitc-test_status': Sending state ON
[D][api.connection:1321]: ESPHome Logs 2024.5.0 (192.168.1.27): Connected successfully
[D][time:051]: Synchronized time: 2024-05-18 08:21:10
[D][api:102]: Accepted 192.168.1.26
[D][api.connection:1321]: Home Assistant 2024.5.4 (192.168.1.26): Connected successfully
[D][time:051]: Synchronized time: 2024-05-18 08:21:30
[D][sensor:094]: 'esp32-s3-devkitc-test_uptime': Sending state 0.62148 min with 0 decimals of accuracy
[D][sensor:094]: 'esp32-s3-devkitc-test_internal_temperature': Sending state 39.11380 Â°C with 1 decimals of accuracy
[D][ota:154]: Starting OTA Update from 192.168.1.15...
[W][component:157]: Component ota set Warning flag: unspecified
[D][ota:330]: OTA in progress: 0.1%
[D][ota:330]: OTA in progress: 16.0%
[D][ota:330]: OTA in progress: 38.2%
[D][ota:330]: OTA in progress: 54.4%
[D][ota:330]: OTA in progress: 75.8%
[D][ota:330]: OTA in progress: 94.5%
[I][ota:363]: OTA update finished!
[W][component:170]: Component ota cleared Warning flag
[I][app:132]: Rebooting safely...
[D][esp32.preferences:114]: Saving 1 preferences to flash...
[D][esp32.preferences:143]: Saving 1 preferences to flash: 0 cached, 1 written, 0 failed
[W][wifi_esp32:482][arduino_events]: Event: Disconnected ssid='Draadloos' bssid=E4:38:83:55:19:32 reason='Association Leave'
ESP-ROM:esp32s3-20210327
Build:Mar 27 2021
rst:0xc (RTC_SW_CPU_RST),boot:0x8 (SPI_FAST_FLASH_BOOT)
Saved PC:0x42098f8e
SPIWP:0xee
Octal Flash Mode Enabled
For OPI Flash, Use Default Flash Boot Mode
mode:SLOW_RD, clock div:1
load:0x3fce3808,len:0x3ac
load:0x403c9700,len:0x9b4
load:0x403cc700,len:0x28fc
entry 0x403c98bc
E (477) esp_core_dump_flash: No core dump partition found!
E (477) esp_core_dump_flash: No core dump partition [I][logger:156]: Log initialized
[C][ota:483]: There have been 0 suspected unsuccessful boot attempts.
[D][esp32.preferences:114]: Saving 1 preferences to flash...
[D][esp32.preferences:143]: Saving 1 preferences to flash: 0 cached, 1 written, 0 failed
[I][app:029]: Running through setup()...
[C][esp32_rmt_led_strip:021]: Setting up ESP32 LED Strip...
[C][light:035]: Setting up light 'esp32-s3-devkitc-test_rgb_led'...
[D][light:036]: 'esp32-s3-devkitc-test_rgb_led' Setting:
[D][light:041]:   Color mode: RGB
[D][light:085]:   Transition length: 1.0s
[D][binary_sensor:034]: 'esp32-s3-devkitc-test_status': Sending initial state OFF
[D][text_sensor:064]: 'esp32-s3-devkitc-test_version': Sending state '2024.5.0 May 18 2024, 08:01:15'
[C][wifi:038]: Setting up WiFi...
[C][wifi:051]: Starting WiFi...
[C][wifi:052]:   LocalÂ MAC: 68:B6:B3:3D:63:6C
[D][wifi:464]: Starting scan...
[D][sensor:094]: 'esp32-s3-devkitc-test_internal_temperature': Sending state 40.42960 Â°C with 1 decimals of accuracy
[D][sensor:094]: 'esp32-s3-devkitc-test_uptime': Sending state 0.01050 min with 0 decimals of accuracy
[I][status_indicator:135]: <>> on_network_disconnected->status_indicator_statustrigger_id_5
[D][light:036]: 'esp32-s3-devkitc-test_rgb_led' Setting:
[D][light:047]:   State: ON
[D][light:051]:   Brightness: 50%
[D][light:059]:   Red: 100%, Green: 0%, Blue: 0%
[D][light:109]:   Effect: 'fast_pulse'
[W][component:157]: Component wifi set Warning flag: unspecified
[D][wifi:479]: Found networks:
[I][wifi:523]: - 'Draadloos' (E4:38:83:55:19:32) ââ
                                                   ââ
[D][wifi:524]:     Channel: 6
[D][wifi:525]:     RSSI: -60 dB
[I][wifi:523]: - 'Draadloos' (AC:8B:A9:D4:F3:16) ââ
                                                   ââ
[D][wifi:524]:     Channel: 6
[D][wifi:525]:     RSSI: -60 dB
[I][wifi:523]: - 'Draadloos' (E4:38:83:54:BA:4B) ââ
                                                   ââ
[D][wifi:524]:     Channel: 1
[D][wifi:525]:     RSSI: -63 dB
[I][wifi:523]: - 'Draadloos' (AC:8B:A9:D4:F2:AE) ââ
                                                   ââ
[D][wifi:524]:     Channel: 11
[D][wifi:525]:     RSSI: -74 dB
[I][wifi:523]: - 'Draadloos' (AC:8B:A9:D4:D8:E6) ââ
                                                   ââ
[D][wifi:524]:     Channel: 11
[D][wifi:525]:     RSSI: -86 dB
[D][wifi:528]: - 'DP20_7A431139373857' (D4:F9:8D:35:7F:49) ââ
                                                             ââ
[D][wifi:528]: - 'Draadloos_Family' (B6:8B:A9:D4:F3:16) ââ
                                                          ââ
[D][wifi:528]: - 'Draadloos_Guest' (EA:38:83:55:19:32) ââ
                                                         ââ
[D][wifi:528]: - 'Draadloos_Family' (EE:38:83:55:19:32) ââ
                                                          ââ
[D][wifi:528]: - 'Draadloos_Guest' (B2:8B:A9:D4:F3:16) ââ
                                                         ââ
[D][wifi:528]: - 'Draadloos_Family' (EE:38:83:54:BA:4B) ââ
                                                          ââ
[D][wifi:528]: - 'Draadloos_Guest' (EA:38:83:54:BA:4B) ââ
                                                         ââ
[D][wifi:528]: - 'Skaariboon' (70:3A:CB:4B:B1:16) ââ
                                                    ââ
[D][wifi:528]: - 'Skaariboon-guest' (72:3A:CB:4B:B1:14) ââ
                                                          ââ
[D][wifi:528]: - 'Draadloos_Guest' (B2:8B:A9:D4:F2:AE) ââ
                                                         ââ
[D][wifi:528]: - 'Draadloos_Family' (B6:8B:A9:D4:F2:AE) ââ
                                                          ââ
[D][wifi:528]: - 'Skaariboon-guest' (72:3A:CB:A4:67:0C) ââ
                                                          ââ
[D][wifi:528]: - 'Skaariboon' (70:3A:CB:A4:67:0F) ââ
                                                    ââ
[D][wifi:528]: - 'beach3' (E4:38:83:3C:95:97) ââ
                                                ââ
[D][wifi:528]: - 'Beach3' (E6:38:83:1C:95:97) ââ
                                                ââ
[D][wifi:528]: - '' (E6:38:83:2C:95:97) ââ
                                          ââ
[D][wifi:528]: - 'DIRECT-8C1150AC' (66:EB:8C:11:D0:AC) ââ
                                                         ââ
[D][wifi:528]: - 'Skaariboon' (24:05:88:01:7E:E1) ââ
                                                    ââ
[D][wifi:528]: - 'Draadloos_Family' (B6:8B:A9:D4:D8:E6) ââ
                                                          ââ
[D][wifi:528]: - '' (E6:38:83:3C:95:97) ââ
                                          ââ
[D][wifi:528]: - 'Draadloos_Guest' (B2:8B:A9:D4:D8:E6) ââ
                                                         ââ
[D][wifi:528]: - 'Skaariboon' (30:FD:38:E7:FE:2B) ââ
                                                    ââ
[D][wifi:528]: - 'Skaariboon' (30:FD:38:E7:F2:23) ââ
                                                    ââ
[D][wifi:528]: - 'Skaariboon-guest' (32:FD:38:E7:FE:28) ââ
                                                          ââ
[D][wifi:528]: - 'Skaariboon-guest' (32:FD:38:E7:F2:20) ââ
                                                          ââ
[D][wifi:528]: - 'TEG-AH4' (88:DA:1A:22:A7:59) ââ
                                                 ââ
[D][wifi:528]: - 'NETGEAR98' (50:6A:03:BD:5D:55) ââ
                                                   ââ
[I][wifi:305]: WiFi Connecting to 'Draadloos'...
[I][wifi:596]: WiFi Connected!
[C][wifi:410]:   Local MAC: 68:B6:B3:3D:63:6C
[C][wifi:415]:   SSID: 'Draadloos'
[C][wifi:418]:   IP Address: 192.168.1.129
[C][wifi:422]:   BSSID: E4:38:83:55:19:32
[C][wifi:423]:   Hostname: 'esp32-s3-devkitc-test'
[C][wifi:425]:   Signal strength: -60 dB ââ
                                           ââ
[C][wifi:429]:   Channel: 6
[C][wifi:430]:   Subnet: 255.255.255.0
[C][wifi:431]:   Gateway: 192.168.1.1
[C][wifi:432]:   DNS1: 192.168.1.1
[C][wifi:433]:   DNS2: 0.0.0.0
[C][ota:096]: Over-The-Air Updates:
[C][ota:097]:   Address: esp32-s3-devkitc-test.home.insanegenius.net:3232
[C][ota:100]:   Using Password.
[C][ota:103]:   OTA version: 2.
[C][api:025]: Setting up Home Assistant API server...
[I][app:062]: setup() finished successfully!
[D][text_sensor:064]: 'esp32-s3-devkitc-test_wifi_ip': Sending state '192.168.1.129'
[D][text_sensor:064]: 'esp32-s3-devkitc-test_wifi_ssid': Sending state 'Draadloos'
[D][sensor:094]: 'esp32-s3-devkitc-test_heap_free': Sending state 262976.00000 B with 0 decimals of accuracy
[D][sensor:094]: 'esp32-s3-devkitc-test_wifi_signal': Sending state -60.00000 dBm with 0 decimals of accuracy
[D][text_sensor:064]: 'esp32-s3-devkitc-test_wifi_bssid': Sending state 'E4:38:83:55:19:32'
[I][status_indicator:135]: <>> on_turn_off->status_indicator_statustrigger_id
[D][light:036]: 'esp32-s3-devkitc-test_rgb_led' Setting:
[D][light:051]:   Brightness: 25%
[D][light:059]:   Red: 0%, Green: 100%, Blue: 0%
[D][light:085]:   Transition length: 1.0s
[D][light:091]:   Effect: 'None'
[W][component:170]: Component wifi cleared Warning flag
[W][component:157]: Component api set Warning flag: unspecified
[I][app:100]: ESPHome version 2024.5.0 compiled on May 18 2024, 08:01:15
[C][status_indicator:058]: Status Indicator supports:
[C][status_indicator:060]:  * on_api_disconnected: status_indicator_statustrigger_id_6  |       | 0
[C][status_indicator:060]:  * on_app_error: status_indicator_statustrigger_id_2         |       | 0
[C][status_indicator:060]:  * on_app_warning: status_indicator_statustrigger_id_3       |       | 0
[C][status_indicator:060]:  * on_network_disconnected: status_indicator_statustrigger_id_5      |       | 0
[C][status_indicator:060]:  * on_turn_off: status_indicator_statustrigger_id    |       | 0
[C][status_indicator:060]:  * on_wifi_ap_enabled: status_indicator_statustrigger_id_4   |       | 0
[I][status_indicator:135]: <>> on_api_disconnected->status_indicator_statustrigger_id_6
[D][light:036]: 'esp32-s3-devkitc-test_rgb_led' Setting:
[D][light:051]:   Brightness: 50%
[D][light:059]:   Red: 100%, Green: 100%, Blue: 0%
[D][light:109]:   Effect: 'fast_pulse'
[C][wifi:582]: WiFi:
[C][wifi:410]:   Local MAC: 68:B6:B3:3D:63:6C
[C][wifi:415]:   SSID: 'Draadloos'
[C][wifi:418]:   IP Address: 192.168.1.129
[C][wifi:422]:   BSSID: E4:38:83:55:19:32
[C][wifi:423]:   Hostname: 'esp32-s3-devkitc-test'
[C][wifi:425]:   Signal strength: -60 dB ââ
                                           ââ
[C][wifi:429]:   Channel: 6
[C][wifi:430]:   Subnet: 255.255.255.0
[C][wifi:431]:   Gateway: 192.168.1.1
[C][wifi:432]:   DNS1: 192.168.1.1
[C][wifi:433]:   DNS2: 0.0.0.0
[C][logger:185]: Logger:
[C][logger:186]:   Level: DEBUG
[C][logger:188]:   Log Baud Rate: 115200
[C][logger:189]:   Hardware UART: UART0
[C][uptime.sensor:031]: Uptime Sensor 'esp32-s3-devkitc-test_uptime'
[C][uptime.sensor:031]:   Device Class: 'duration'
[C][uptime.sensor:031]:   State Class: 'total_increasing'
[C][uptime.sensor:031]:   Unit of Measurement: 'min'
[C][uptime.sensor:031]:   Accuracy Decimals: 0
[C][uptime.sensor:031]:   Icon: 'mdi:timer-outline'
[C][esp32_rmt_led_strip:175]: ESP32 RMT LED Strip:
[C][esp32_rmt_led_strip:176]:   Pin: 38
[C][esp32_rmt_led_strip:177]:   Channel: 0
[C][esp32_rmt_led_strip:202]:   RGB Order: GRB
[C][esp32_rmt_led_strip:203]:   Max refresh rate: 0
[C][esp32_rmt_led_strip:204]:   Number of LEDs: 1
[C][light:103]: Light 'esp32-s3-devkitc-test_rgb_led'
[C][light:105]:   Default Transition Length: 1.0s
[C][light:106]:   Gamma Correct: 2.80
[C][restart.button:017]: Restart Button 'esp32-s3-devkitc-test_restart'
[C][status:034]: Status Binary Sensor 'esp32-s3-devkitc-test_status'
[C][status:034]:   Device Class: 'connectivity'
[C][version.text_sensor:021]: Version Text Sensor 'esp32-s3-devkitc-test_version'
[C][version.text_sensor:021]:   Icon: 'mdi:new-box'
[C][internal_temperature:076]: Internal Temperature Sensor 'esp32-s3-devkitc-test_internal_temperature'
[C][internal_temperature:076]:   Device Class: 'temperature'
[C][internal_temperature:076]:   State Class: 'measurement'
[C][internal_temperature:076]:   Unit of Measurement: 'Â°C'
[C][internal_temperature:076]:   Accuracy Decimals: 1
[C][homeassistant.time:010]: Home Assistant Time:
[C][homeassistant.time:011]:   Timezone: 'PST8PDT,M3.2.0,M11.1.0'
[C][psram:020]: PSRAM:
[C][psram:021]:   Available: YES
[C][psram:024]:   Size: 8191 KB
[C][mdns:115]: mDNS:
[C][mdns:116]:   Hostname: esp32-s3-devkitc-test
[C][ota:096]: Over-The-Air Updates:
[C][ota:097]:   Address: esp32-s3-devkitc-test.home.insanegenius.net:3232
[C][ota:100]:   Using Password.
[C][ota:103]:   OTA version: 2.
[C][api:139]: API Server:
[C][api:140]:   Address: esp32-s3-devkitc-test.home.insanegenius.net:6053
[C][api:144]:   Using noise encryption: NO
[C][wifi_info:011]: WifiInfo SSID 'esp32-s3-devkitc-test_wifi_ssid'
[C][wifi_info:012]: WifiInfo BSSID 'esp32-s3-devkitc-test_wifi_bssid'
[C][wifi_info:009]: WifiInfo IPAddress 'esp32-s3-devkitc-test_wifi_ip'
[C][wifi_signal.sensor:009]: WiFi Signal 'esp32-s3-devkitc-test_wifi_signal'
[C][wifi_signal.sensor:009]:   Device Class: 'signal_strength'
[C][wifi_signal.sensor:009]:   State Class: 'measurement'
[C][wifi_signal.sensor:009]:   Unit of Measurement: 'dBm'
[C][wifi_signal.sensor:009]:   Accuracy Decimals: 0
[C][debug:067]: Debug component:
[C][debug:069]:   Device info 'esp32-s3-devkitc-test_device_info'
[C][debug:069]:     Icon: 'mdi:chip'
[C][debug:072]:   Free space on heap 'esp32-s3-devkitc-test_heap_free'
[C][debug:072]:     State Class: ''
[C][debug:072]:     Unit of Measurement: 'B'
[C][debug:072]:     Accuracy Decimals: 0
[C][debug:072]:     Icon: 'mdi:counter'
[D][debug:079]: ESPHome version 2024.5.0
[D][debug:083]: Free Heap Size: 262432 bytes
[D][debug:113]: Flash Chip: Size=32768kB Speed=80MHz Mode=FAST_READ
[D][debug:162]: Chip: Model=ESP32-S3, Features=WIFI_BGN,BLE, Cores=2, Revision=0
[D][debug:170]: ESP-IDF Version: v4.4.4
[D][debug:175]: EFuse MAC: 68:B6:B3:3D:63:6C
[D][debug:275]: Reset Reason: Software Reset CPU
[D][debug:320]: Wakeup Reason: Unknown
[D][text_sensor:064]: 'esp32-s3-devkitc-test_device_info': Sending state '2024.5.0|Flash: 32768kB Speed:80MHz Mode:FAST_READ|Chip: ESP32-S3 Features:WIFI_BGN,BLE, Cores:2 Revision:0|ESP-IDF: v4.4.4|EFuse MAC: 68:B6:B3:3D:63:6C|Reset: Software Reset CPU|Wakeup: Unknown'
[D][text_sensor:064]: 'esp32-s3-devkitc-test_reset_reason': Sending state 'Software Reset CPU'
[D][api:102]: Accepted 192.168.1.27
[D][api:102]: Accepted 192.168.1.26
[W][component:170]: Component api cleared Warning flag
[I][status_indicator:135]: <>> on_turn_off->status_indicator_statustrigger_id
[D][light:036]: 'esp32-s3-devkitc-test_rgb_led' Setting:
[D][light:051]:   Brightness: 25%
[D][light:059]:   Red: 0%, Green: 100%, Blue: 0%
[D][light:085]:   Transition length: 1.0s
[D][light:091]:   Effect: 'None'
[D][binary_sensor:036]: 'esp32-s3-devkitc-test_status': Sending state ON
[D][api.connection:1321]: ESPHome Logs 2024.5.0 (192.168.1.27): Connected successfully
[D][api.connection:1321]: Home Assistant 2024.5.4 (192.168.1.26): Connected successfully
[D][time:051]: Synchronized time: 2024-05-18 08:21:56
[D][time:051]: Synchronized time: 2024-05-18 08:21:56
[D][api:102]: Accepted 192.168.1.15
[D][api.connection:1321]: ESPHome Logs 2024.5.0 (192.168.1.15): Connected successfully
[D][time:051]: Synchronized time: 2024-05-18 08:22:04
[I][app:100]: ESPHome version 2024.5.0 compiled on May 18 2024, 08:01:15
[C][status_indicator:058]: Status Indicator supports:
[C][status_indicator:060]:  * on_api_disconnected: status_indicator_statustrigger_id_6  |       | 0
[C][status_indicator:060]:  * on_app_error: status_indicator_statustrigger_id_2         |       | 0
[C][status_indicator:060]:  * on_app_warning: status_indicator_statustrigger_id_3       |       | 0
[C][status_indicator:060]:  * on_network_disconnected: status_indicator_statustrigger_id_5      |       | 0
[C][status_indicator:060]:  * on_turn_off: status_indicator_statustrigger_id    |       | 0
[C][status_indicator:060]:  * on_wifi_ap_enabled: status_indicator_statustrigger_id_4   |       | 0
[C][wifi:582]: WiFi:
[C][wifi:410]:   Local MAC: 68:B6:B3:3D:63:6C
[C][wifi:415]:   SSID: 'Draadloos'
[C][wifi:418]:   IP Address: 192.168.1.129
[C][wifi:422]:   BSSID: E4:38:83:55:19:32
[C][wifi:423]:   Hostname: 'esp32-s3-devkitc-test'
[C][wifi:425]:   Signal strength: -62 dB ââ
                                           ââ
[C][wifi:429]:   Channel: 6
[C][wifi:430]:   Subnet: 255.255.255.0
[C][wifi:431]:   Gateway: 192.168.1.1
[C][wifi:432]:   DNS1: 192.168.1.1
[C][wifi:433]:   DNS2: 0.0.0.0
[C][logger:185]: Logger:
[C][logger:186]:   Level: DEBUG
[C][logger:188]:   Log Baud Rate: 115200
[C][logger:189]:   Hardware UART: UART0
[C][uptime.sensor:031]: Uptime Sensor 'esp32-s3-devkitc-test_uptime'
[C][uptime.sensor:031]:   Device Class: 'duration'
[C][uptime.sensor:031]:   State Class: 'total_increasing'
[C][uptime.sensor:031]:   Unit of Measurement: 'min'
[C][uptime.sensor:031]:   Accuracy Decimals: 0
[C][uptime.sensor:031]:   Icon: 'mdi:timer-outline'
[C][esp32_rmt_led_strip:175]: ESP32 RMT LED Strip:
[C][esp32_rmt_led_strip:176]:   Pin: 38
[C][esp32_rmt_led_strip:177]:   Channel: 0
[C][esp32_rmt_led_strip:202]:   RGB Order: GRB
[C][esp32_rmt_led_strip:203]:   Max refresh rate: 0
[C][esp32_rmt_led_strip:204]:   Number of LEDs: 1
[C][light:103]: Light 'esp32-s3-devkitc-test_rgb_led'
[C][light:105]:   Default Transition Length: 1.0s
[C][light:106]:   Gamma Correct: 2.80
[C][restart.button:017]: Restart Button 'esp32-s3-devkitc-test_restart'
[C][status:034]: Status Binary Sensor 'esp32-s3-devkitc-test_status'
[C][status:034]:   Device Class: 'connectivity'
[C][version.text_sensor:021]: Version Text Sensor 'esp32-s3-devkitc-test_version'
[C][version.text_sensor:021]:   Icon: 'mdi:new-box'
[C][internal_temperature:076]: Internal Temperature Sensor 'esp32-s3-devkitc-test_internal_temperature'
[C][internal_temperature:076]:   Device Class: 'temperature'
[C][internal_temperature:076]:   State Class: 'measurement'
[C][internal_temperature:076]:   Unit of Measurement: 'Â°C'
[C][internal_temperature:076]:   Accuracy Decimals: 1
[C][homeassistant.time:010]: Home Assistant Time:
[C][homeassistant.time:011]:   Timezone: 'PST8PDT,M3.2.0,M11.1.0'
[C][psram:020]: PSRAM:
[C][psram:021]:   Available: YES
[C][psram:024]:   Size: 8191 KB
[C][mdns:115]: mDNS:
[C][mdns:116]:   Hostname: esp32-s3-devkitc-test
[C][ota:096]: Over-The-Air Updates:
[C][ota:097]:   Address: esp32-s3-devkitc-test.home.insanegenius.net:3232
[C][ota:100]:   Using Password.
[C][ota:103]:   OTA version: 2.
[C][api:139]: API Server:
[C][api:140]:   Address: esp32-s3-devkitc-test.home.insanegenius.net:6053
[C][api:144]:   Using noise encryption: NO
[C][wifi_info:011]: WifiInfo SSID 'esp32-s3-devkitc-test_wifi_ssid'
[C][wifi_info:012]: WifiInfo BSSID 'esp32-s3-devkitc-test_wifi_bssid'
[C][wifi_info:009]: WifiInfo IPAddress 'esp32-s3-devkitc-test_wifi_ip'
[C][wifi_signal.sensor:009]: WiFi Signal 'esp32-s3-devkitc-test_wifi_signal'
[C][wifi_signal.sensor:009]:   Device Class: 'signal_strength'
[C][wifi_signal.sensor:009]:   State Class: 'measurement'
[C][wifi_signal.sensor:009]:   Unit of Measurement: 'dBm'
[C][wifi_signal.sensor:009]:   Accuracy Decimals: 0
[C][debug:067]: Debug component:
[C][debug:069]:   Device info 'esp32-s3-devkitc-test_device_info'
[C][debug:069]:     Icon: 'mdi:chip'
[C][debug:072]:   Free space on heap 'esp32-s3-devkitc-test_heap_free'
[C][debug:072]:     State Class: ''
[C][debug:072]:     Unit of Measurement: 'B'
[C][debug:072]:     Accuracy Decimals: 0
[C][debug:072]:     Icon: 'mdi:counter'
[D][debug:079]: ESPHome version 2024.5.0
[D][debug:083]: Free Heap Size: 245748 bytes
[D][debug:113]: Flash Chip: Size=32768kB Speed=80MHz Mode=FAST_READ
[D][debug:162]: Chip: Model=ESP32-S3, Features=WIFI_BGN,BLE, Cores=2, Revision=0
[D][debug:170]: ESP-IDF Version: v4.4.4
[D][debug:175]: EFuse MAC: 68:B6:B3:3D:63:6C
[D][debug:275]: Reset Reason: Software Reset CPU
[D][debug:320]: Wakeup Reason: Unknown
[D][text_sensor:064]: 'esp32-s3-devkitc-test_device_info': Sending state '2024.5.0|Flash: 32768kB Speed:80MHz Mode:FAST_READ|Chip: ESP32-S3 Features:WIFI_BGN,BLE, Cores:2 Revision:0|ESP-IDF: v4.4.4|EFuse MAC: 68:B6:B3:3D:63:6C|Reset: Software Reset CPU|Wakeup: Unknown'
[D][text_sensor:064]: 'esp32-s3-devkitc-test_reset_reason': Sending state 'Software Reset CPU'
[D][sensor:094]: 'esp32-s3-devkitc-test_internal_temperature': Sending state 39.99100 Â°C with 1 decimals of accuracy
[D][sensor:094]: 'esp32-s3-devkitc-test_heap_free': Sending state 258392.00000 B with 0 decimals of accuracy
[D][sensor:094]: 'esp32-s3-devkitc-test_uptime': Sending state 0.72653 min with 0 decimals of accuracy
[D][sensor:094]: 'esp32-s3-devkitc-test_wifi_signal': Sending state -62.00000 dBm with 0 decimals of accuracy
[D][sensor:094]: 'esp32-s3-devkitc-test_internal_temperature': Sending state 39.11380 Â°C with 1 decimals of accuracy
[D][sensor:094]: 'esp32-s3-devkitc-test_heap_free': Sending state 258392.00000 B with 0 decimals of accuracy
[D][sensor:094]: 'esp32-s3-devkitc-test_uptime': Sending state 1.72650 min with 0 decimals of accuracy
[D][sensor:094]: 'esp32-s3-devkitc-test_wifi_signal': Sending state -60.00000 dBm with 0 decimals of accuracy
[D][sensor:094]: 'esp32-s3-devkitc-test_internal_temperature': Sending state 38.23660 Â°C with 1 decimals of accuracy
[D][sensor:094]: 'esp32-s3-devkitc-test_heap_free': Sending state 258392.00000 B with 0 decimals of accuracy
[D][sensor:094]: 'esp32-s3-devkitc-test_uptime': Sending state 2.72650 min with 0 decimals of accuracy
[D][sensor:094]: 'esp32-s3-devkitc-test_wifi_signal': Sending state -62.00000 dBm with 0 decimals of accuracy
---- Closed the serial port COM9 ----
```

### PlatformIO INI

```ini
; Auto generated code by esphome

[common]
lib_deps =
build_flags =
upload_flags =

; ========== AUTO GENERATED CODE BEGIN ===========
[platformio]
description = ESPHome 2024.5.0
[env:esp32-s3-devkitc-test]
board = esp32-s3-devkitc-1
board_build.arduino.memory_type = opi_opi
board_build.partitions = partitions.csv
board_upload.flash_size = 32MB
build_flags =
    -DBOARD_HAS_PSRAM
    -DESPHOME_LOG_LEVEL=ESPHOME_LOG_LEVEL_DEBUG
    -DUSE_ARDUINO
    -DUSE_ESP32
    -DUSE_ESP32_FRAMEWORK_ARDUINO
    -DUSE_ESP32_VARIANT_ESP32S3
    -Wno-sign-compare
    -Wno-unused-but-set-variable
    -Wno-unused-variable
    -fno-exceptions
extra_scripts =
    post:post_build.py
framework = arduino
lib_deps =
    WiFi
    ESPmDNS
    Update
    ${common.lib_deps}
lib_ldf_mode = off
platform = platformio/espressif32@5.4.0
platform_packages =
    platformio/framework-arduinoespressif32@~3.20009.0
; =========== AUTO GENERATED CODE END ============
```

### PlatformIO Partitions

```csv
nvs,      data, nvs,     0x9000, 0x5000,
otadata,  data, ota,     0xE000, 0x2000,
app0,     app,  ota_0,   0x10000, 0xFC0000,
app1,     app,  ota_1,   0xFD0000, 0xFC0000,
eeprom,   data, 0x99,    0x1F90000, 0x1000,
spiffs,   data, spiffs,  0x1F91000, 0xF000
```

### CLI USB BootLoop

```console
> esphome run .\esp32-s3-devkitc-test.yaml
INFO ESPHome 2024.5.0
INFO Reading configuration .\esp32-s3-devkitc-test.yaml...
WARNING The selected Arduino framework version is not the recommended one. If there are connectivity or build issues please remove the manual version.
INFO Detected timezone 'America/Los_Angeles'
WARNING The selected Arduino framework version is not the recommended one. If there are connectivity or build issues please remove the manual version.
INFO Generating C++ source...
INFO Compiling app...
Processing esp32-s3-devkitc-test (board: esp32-s3-devkitc-1; framework: arduino; platform: platformio/espressif32@5.4.0)
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Verbose mode can be enabled via `-v, --verbose` option
CONFIGURATION: https://docs.platformio.org/page/boards/espressif32/esp32-s3-devkitc-1.html
PLATFORM: Espressif 32 (5.4.0) > Espressif ESP32-S3-DevKitC-1-N8 (8 MB QD, No PSRAM)
HARDWARE: ESP32S3 240MHz, 320KB RAM, 8MB Flash
DEBUG: Current (esp-builtin) On-board (esp-builtin) External (cmsis-dap, esp-bridge, esp-prog, iot-bus-jtag, jlink, minimodule, olimex-arm-usb-ocd, olimex-arm-usb-ocd-h, olimex-arm-usb-tiny-h, olimex-jtag-tiny, tumpa)
PACKAGES: 
 - framework-arduinoespressif32 @ 3.20009.0 (2.0.9) 
 - tool-esptoolpy @ 1.40400.0 (4.4.0) 
 - toolchain-riscv32-esp @ 8.4.0+2021r2-patch5 
 - toolchain-xtensa-esp32s3 @ 8.4.0+2021r2-patch5
LDF: Library Dependency Finder -> https://bit.ly/configure-pio-ldf
LDF Modes: Finder ~ off, Compatibility ~ soft
Found 33 compatible libraries
Scanning dependencies...
Dependency Graph
|-- WiFi @ 2.0.0
|-- ESPmDNS @ 2.0.0
|-- Update @ 2.0.0
Building in release mode
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\api\api_connection.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\api\api_frame_helper.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\api\api_pb2.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\api\api_pb2_service.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\api\api_server.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\api\list_entities.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\api\proto.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\api\subscribe_state.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\api\user_services.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\binary_sensor\automation.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\binary_sensor\binary_sensor.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\binary_sensor\filter.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\button\button.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\debug\debug_component.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\esp32\core.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\esp32\gpio.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\esp32\preferences.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\esp32_rmt_led_strip\led_strip.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\homeassistant\time\homeassistant_time.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\internal_temperature\internal_temperature.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\light\addressable_light.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\light\automation.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\light\esp_color_correction.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\light\esp_hsv_color.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\light\esp_range_view.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\light\light_call.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\light\light_json_schema.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\light\light_output.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\light\light_state.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\logger\logger.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\logger\logger_esp32.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\logger\logger_esp8266.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\logger\logger_host.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\logger\logger_libretiny.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\logger\logger_rp2040.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\md5\md5.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\mdns\mdns_component.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\mdns\mdns_esp32.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\mdns\mdns_esp8266.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\mdns\mdns_host.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\mdns\mdns_libretiny.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\mdns\mdns_rp2040.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\network\util.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\ota\ota_backend_arduino_esp32.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\ota\ota_backend_arduino_esp8266.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\ota\ota_backend_arduino_libretiny.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\ota\ota_backend_arduino_rp2040.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\ota\ota_backend_esp_idf.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\ota\ota_component.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\psram\psram.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\restart\button\restart_button.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\sensor\automation.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\sensor\filter.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\sensor\sensor.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\socket\bsd_sockets_impl.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\socket\lwip_raw_tcp_impl.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\socket\lwip_sockets_impl.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\socket\socket.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\status\status_binary_sensor.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\status_indicator\status_indicator.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\text_sensor\filter.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\text_sensor\text_sensor.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\time\automation.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\time\real_time_clock.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\uptime\uptime_sensor.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\version\version_text_sensor.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\wifi\wifi_component.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\wifi\wifi_component_esp32_arduino.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\wifi\wifi_component_esp8266.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\wifi\wifi_component_esp_idf.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\wifi\wifi_component_libretiny.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\wifi\wifi_component_pico_w.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\wifi_info\wifi_info_text_sensor.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\components\wifi_signal\wifi_signal_sensor.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\application.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\color.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\component.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\component_iterator.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\controller.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\entity_base.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\helpers.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\log.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\ring_buffer.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\scheduler.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\string_ref.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\time.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\esphome\core\util.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\src\main.cpp.o
Building .pioenvs\esp32-s3-devkitc-test\bootloader.bin
Generating partitions .pioenvs\esp32-s3-devkitc-test\partitions.bin
esptool.py v4.4
Creating esp32s3 image...
Merged 1 ELF section
Successfully created esp32s3 image.
Compiling .pioenvs\esp32-s3-devkitc-test\lib1cf\WiFi\WiFi.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\lib1cf\WiFi\WiFiAP.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\lib1cf\WiFi\WiFiClient.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\lib1cf\WiFi\WiFiGeneric.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\lib1cf\WiFi\WiFiMulti.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\lib1cf\WiFi\WiFiSTA.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\lib1cf\WiFi\WiFiScan.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\lib1cf\WiFi\WiFiServer.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\lib1cf\WiFi\WiFiUdp.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\libb46\ESPmDNS\ESPmDNS.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\lib4c8\Update\HttpsOTAUpdate.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\lib4c8\Update\Updater.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\Esp.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\FirmwareMSC.cpp.o
Archiving .pioenvs\esp32-s3-devkitc-test\lib1cf\libWiFi.a
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\FunctionalInterrupt.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\HWCDC.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\HardwareSerial.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\IPAddress.cpp.o
Archiving .pioenvs\esp32-s3-devkitc-test\libb46\libESPmDNS.a
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\IPv6Address.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\MD5Builder.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\Print.cpp.o
Archiving .pioenvs\esp32-s3-devkitc-test\lib4c8\libUpdate.a
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\Stream.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\StreamString.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\Tone.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\USB.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\USBCDC.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\USBMSC.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\WMath.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\WString.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\base64.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\cbuf.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-adc.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-bt.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-cpu.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-dac.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-gpio.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-i2c-slave.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-i2c.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-ledc.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-matrix.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-misc.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-psram.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-rgb-led.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-rmt.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-sigmadelta.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-spi.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-time.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-timer.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-tinyusb.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-touch.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\esp32-hal-uart.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\firmware_msc_fat.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\libb64\cdecode.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\libb64\cencode.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\main.cpp.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\stdlib_noniso.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\wiring_pulse.c.o
Compiling .pioenvs\esp32-s3-devkitc-test\FrameworkArduino\wiring_shift.c.o
Archiving .pioenvs\esp32-s3-devkitc-test\libFrameworkArduino.a
Linking .pioenvs\esp32-s3-devkitc-test\firmware.elf
Retrieving maximum program size .pioenvs\esp32-s3-devkitc-test\firmware.elf
Checking size .pioenvs\esp32-s3-devkitc-test\firmware.elf
Advanced Memory Usage is available via "PlatformIO Home > Project Inspect"
RAM:   [=         ]  14.6% (used 47976 bytes from 327680 bytes)
Flash: [=         ]   5.1% (used 848741 bytes from 16515072 bytes)
Building .pioenvs\esp32-s3-devkitc-test\firmware.bin
esptool.py v4.4
Creating esp32s3 image...
Merged 2 ELF sections
Successfully created esp32s3 image.
esp32_create_combined_bin([".pioenvs\esp32-s3-devkitc-test\firmware.bin"], [".pioenvs\esp32-s3-devkitc-test\firmware.elf"])
esptool.py v4.7.0
Wrote 0xdf4d0 bytes to file C:\Users\piete\source\repos\ptr727\ESPHome-Config\.esphome\build\esp32-s3-devkitc-test\.pioenvs\esp32-s3-devkitc-test/firmware-factory.bin, ready to flash to offset 0x0
==================================================================================================================================== [SUCCESS] Took 37.72 seconds ====================================================================================================================================
INFO Successfully compiled program.
Found multiple options for uploading, please choose one:
  [1] COM9 (Silicon Labs CP210x USB to UART Bridge (COM9))
  [2] Over The Air (esp32-s3-devkitc-test.home.insanegenius.net)
(number): 1
esptool.py v4.7.0
Serial port COM9
Connecting....
Chip is ESP32-S3 (QFN56) (revision v0.1)
Features: WiFi, BLE, Embedded PSRAM 8MB (AP_1v8)
Crystal is 40MHz
MAC: 68:b6:b3:3d:63:6c
Uploading stub...
Running stub...
Stub running...
Changing baud rate to 460800
Changed.
Configuring flash size...
Auto-detected Flash size: 32MB
Flash will be erased from 0x00010000 to 0x000dffff...
Flash will be erased from 0x00000000 to 0x00003fff...
Flash will be erased from 0x00008000 to 0x00008fff...
Flash will be erased from 0x0000e000 to 0x0000ffff...
Compressed 849104 bytes to 554807...
Wrote 849104 bytes (554807 compressed) at 0x00010000 in 14.7 seconds (effective 462.1 kbit/s)...
Hash of data verified.
Compressed 15040 bytes to 10333...
Wrote 15040 bytes (10333 compressed) at 0x00000000 in 0.4 seconds (effective 282.3 kbit/s)...
Hash of data verified.
Compressed 3072 bytes to 145...
Wrote 3072 bytes (145 compressed) at 0x00008000 in 0.1 seconds (effective 475.6 kbit/s)...
Hash of data verified.
Compressed 8192 bytes to 47...
Wrote 8192 bytes (47 compressed) at 0x0000e000 in 0.1 seconds (effective 682.6 kbit/s)...
Hash of data verified.

Leaving...
Hard resetting via RTS pin...
INFO Successfully uploaded program.
INFO Starting log output from COM9 with baud rate 115200
[08:43:21]ESP-ROM:esp32s3-20210327
[08:43:21]Build:Mar 27 2021
[08:43:21]rst:0x1 (POWERON),boot:0x8 (SPI_FAST_FLASH_BOOT)
[08:43:21]SPIWP:0xee
[08:43:21]Octal Flash Mode Enabled
[08:43:21]For OPI Flash, Use Default Flash Boot Mode
[08:43:21]mode:SLOW_RD, clock div:1
[08:43:21]load:0x3fce3808,len:0x44c
[08:43:21]load:0x403c9700,len:0xbe4
[08:43:21]load:0x403cc700,len:0x2a38
[08:43:21]entry 0x403c98d4
[08:43:21]
[08:43:21]assert failed: do_core_init startup.c:326 (flash_ret == ESP_OK)
[08:43:21]
[08:43:21]
[08:43:21]Backtrace: 0x403779e2:0x3fceb180 0x4037d3e5:0x3fceb1a0 0x403837dd:0x3fceb1c0 0x42027462:0x3fceb2f0 0x40377351:0x3fceb320 0x403cd757:0x3fceb350 0x403cda16:0x3fceb380 0x403c9929:0x3fceb4b0 0x40045c01:0x3fceb570 |<-CORRUPTED
WARNING Found stack trace! Trying to decode it
WARNING Decoded 0x403779e2: panic_abort at /Users/ficeto/Desktop/ESP32/ESP32S2/esp-idf-public/components/esp_system/panic.c:408
WARNING Decoded 0x4037d3e5: esp_system_abort at /Users/ficeto/Desktop/ESP32/ESP32S2/esp-idf-public/components/esp_system/esp_system.c:137
WARNING Decoded 0x403837dd: __assert_func at /Users/ficeto/Desktop/ESP32/ESP32S2/esp-idf-public/components/newlib/assert.c:85
WARNING Decoded 0x42027462: do_core_init at /Users/ficeto/Desktop/ESP32/ESP32S2/esp-idf-public/components/esp_system/startup.c:318
 (inlined by) start_cpu0_default at /Users/ficeto/Desktop/ESP32/ESP32S2/esp-idf-public/components/esp_system/startup.c:433
WARNING Decoded 0x40377351: call_start_cpu0 at /Users/ficeto/Desktop/ESP32/ESP32S2/esp-idf-public/components/esp_system/port/cpu_start.c:632
[08:43:21]
[08:43:21]
[08:43:21]
[08:43:21]
[08:43:21]ELF file SHA256: 3cd6b8c3a2e43895
[08:43:21]
[08:43:21]E (323) esp_core_dump_flash: Core dump flash config is corrupted! CRC=0x7bd5c66f instead of 0x0
[08:43:21]Rebooting...
[08:43:21]ESP-ROM:esp32s3-20210327
[08:43:21]Build:Mar 27 2021
[08:43:21]rst:0xc (RTC_SW_CPU_RST),boot:0x8 (SPI_FAST_FLASH_BOOT)
[08:43:21]Saved PC:0x403775f0
WARNING Decoded 0x403775f0: esp_restart_noos at /Users/ficeto/Desktop/ESP32/ESP32S2/esp-idf-public/components/esp_system/port/soc/esp32s3/system_internal.c:151 (discriminator 1)
[08:43:22]SPIWP:0xee
[08:43:22]Octal Flash Mode Enabled
[08:43:22]For OPI Flash, Use Default Flash Boot Mode
[08:43:22]mode:SLOW_RD, clock div:1
[08:43:22]load:0x3fce3808,len:0x44c
[08:43:22]load:0x403c9700,len:0xbe4
[08:43:22]load:0x403cc700,len:0x2a38
[08:43:22]entry 0x403c98d4
[08:43:22]
[08:43:22]assert failed: do_core_init startup.c:326 (flash_ret == ESP_OK)
[08:43:22]
[08:43:22]
[08:43:22]Backtrace: 0x403779e2:0x3fceb180 0x4037d3e5:0x3fceb1a0 0x403837dd:0x3fceb1c0 0x42027462:0x3fceb2f0 0x40377351:0x3fceb320 0x403cd757:0x3fceb350 0x403cda16:0x3fceb380 0x403c9929:0x3fceb4b0 0x40045c01:0x3fceb570 |<-CORRUPTED
WARNING Found stack trace! Trying to decode it
WARNING Decoded 0x403779e2: panic_abort at /Users/ficeto/Desktop/ESP32/ESP32S2/esp-idf-public/components/esp_system/panic.c:408
WARNING Decoded 0x4037d3e5: esp_system_abort at /Users/ficeto/Desktop/ESP32/ESP32S2/esp-idf-public/components/esp_system/esp_system.c:137
WARNING Decoded 0x403837dd: __assert_func at /Users/ficeto/Desktop/ESP32/ESP32S2/esp-idf-public/components/newlib/assert.c:85
WARNING Decoded 0x42027462: do_core_init at /Users/ficeto/Desktop/ESP32/ESP32S2/esp-idf-public/components/esp_system/startup.c:318
 (inlined by) start_cpu0_default at /Users/ficeto/Desktop/ESP32/ESP32S2/esp-idf-public/components/esp_system/startup.c:433
WARNING Decoded 0x40377351: call_start_cpu0 at /Users/ficeto/Desktop/ESP32/ESP32S2/esp-idf-public/components/esp_system/port/cpu_start.c:632
[08:43:22]
[08:43:22]
[08:43:22]
[08:43:22]
[08:43:22]ELF file SHA256: 3cd6b8c3a2e43895
[08:43:22]
[08:43:22]E (327) esp_core_dump_flash: Core dump flash config is corrupted! CRC=0x7bd5c66f instead of 0x0
[08:43:22]Rebooting...
[08:43:22]ESP-ROM:esp32s3-20210327
[08:43:22]Build:Mar 27 2021
[08:43:22]rst:0xc (RTC_SW_CPU_RST),boot:0x8 (SPI_FAST_FLASH_BOOT)
[08:43:22]Saved PC:0x403775f0
WARNING Decoded 0x403775f0: esp_restart_noos at /Users/ficeto/Desktop/ESP32/ESP32S2/esp-idf-public/components/esp_system/port/soc/esp32s3/system_internal.c:151 (discriminator 1)
[08:43:22]SPIWP:0xee
[08:43:22]Octal Flash Mode Enabled
[08:43:22]For OPI Flash, Use Default Flash Boot Mode
[08:43:22]mode:SLOW_RD, clock div:1
[08:43:22]load:0x3fce3808,len:0x44c
[08:43:22]load:0x403c9700,len:0xbe4
[08:43:22]load:0x403cc700,len:0x2a38
[08:43:22]entry 0x403c98d4
[08:43:22]
[08:43:22]assert failed: do_core_init startup.c:326 (flash_ret == ESP_OK)
[08:43:22]
[08:43:22]
[08:43:22]Backtrace: 0x403779e2:0x3fceb180 0x4037d3e5:0x3fceb1a0 0x403837dd:0x3fceb1c0 0x42027462:0x3fceb2f0 0x40377351:0x3fceb320 0x403cd757:0x3fceb350 0x403cda16:0x3fceb380 0x403c9929:0x3fceb4b0 0x40045c01:0x3fceb570 |<-CORRUPTED
WARNING Found stack trace! Trying to decode it
WARNING Decoded 0x403779e2: panic_abort at /Users/ficeto/Desktop/ESP32/ESP32S2/esp-idf-public/components/esp_system/panic.c:408
WARNING Decoded 0x4037d3e5: esp_system_abort at /Users/ficeto/Desktop/ESP32/ESP32S2/esp-idf-public/components/esp_system/esp_system.c:137
WARNING Decoded 0x403837dd: __assert_func at /Users/ficeto/Desktop/ESP32/ESP32S2/esp-idf-public/components/newlib/assert.c:85
WARNING Decoded 0x42027462: do_core_init at /Users/ficeto/Desktop/ESP32/ESP32S2/esp-idf-public/components/esp_system/startup.c:318
 (inlined by) start_cpu0_default at /Users/ficeto/Desktop/ESP32/ESP32S2/esp-idf-public/components/esp_system/startup.c:433
WARNING Decoded 0x40377351: call_start_cpu0 at /Users/ficeto/Desktop/ESP32/ESP32S2/esp-idf-public/components/esp_system/port/cpu_start.c:632
[08:43:22]
[08:43:22]
[08:43:22]
[08:43:22]
[08:43:22]ELF file SHA256: 3cd6b8c3a2e43895
[08:43:22]
[08:43:22]E (327) esp_core_dump_flash: Core dump flash config is corrupted! CRC=0x7bd5c66f instead of 0x0
[08:43:22]Rebooting...
[08:43:22]ESP-ROM:esp32s3-20210327
[08:43:22]Build:Mar 27 2021
[08:43:22]rst:0xc (RTC_SW_CPU_RST),boot:0x8 (SPI_FAST_FLASH_BOOT)
[08:43:22]Saved PC:0x403775f0
```
