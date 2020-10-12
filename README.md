# ESPHome-Config

ESPHome configuration.

## Usage

- Run ESPHome in Docker container.
- Sync Git repository in ESPHome config folder.
  - `cd /data/appdata/esphome/config`
  - `git pull https://github.com/ptr727/ESPHome-Config .`
- Deploy `secrets.yaml`.
- Use VSCode and open remote SSH folder.

## Devices

### TuyaConvert

Generic bootstrap profile used when [converting](https://blog.insanegenius.com/2020/09/10/tuya-to-tasmota-to-esphome/) Tuya devices to ESPHome using TuyaConvert.

### Ayococr X5P WiFi Wall Plug

[Converted](https://blog.insanegenius.com/2020/09/10/tuya-to-tasmota-to-esphome/) to ESPHome using TuyaConvert.

### Efun SH331 WiFi Power Monitoring Wall Plug

[Converted](https://blog.insanegenius.com/2020/09/10/tuya-to-tasmota-to-esphome/) to ESPHome using TuyaConvert.

### Sonoff TH10 Hot Water Recirculation Pump Controller

TH10 controller [replaces](https://blog.insanegenius.com/2020/10/11/hot-water-recirculation-pump-controller/) the aquastat used to control my home hot water recirculation pump.
