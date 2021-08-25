# ESPHome-Config

ESPHome configuration.

## Usage

- Run ESPHome in Docker container.
- Sync Git repository in ESPHome config folder.
  - `cd /data/appdata/esphome/config`
  - `git pull https://github.com/ptr727/ESPHome-Config .`
- Deploy `secrets.yaml`.
- Use VSCode and open remote SSH folder.

## Device Templates

### TuyaConvert

- Generic bootstrap [template](./tuya_convert.yaml) used when converting Tuya devices to ESPHome using TuyaConvert.
- See blog [post](https://blog.insanegenius.com/2020/09/10/tuya-to-tasmota-to-esphome/) for firmware conversion details.

### Ayococr X5P WiFi Plug

- [Template](./templates/aoycocr_x5p.yaml) for the [Ayococr X5P](https://www.amazon.com/dp/B07R6CT3G7) US 120V AC WiFi wall plug.
- See blog [post](https://blog.insanegenius.com/2020/09/10/tuya-to-tasmota-to-esphome/) for firmware conversion details.

### EFUN SH331 WiFi Power Monitoring Plug

- [Template](./templates/efun_sh331.yaml) for the [EFUN SH331W](https://www.amazon.com/gp/product/B07DCJ7TDR) US 120V AC WiFi power monitoring wall plug.
- See blog [post](https://blog.insanegenius.com/2020/09/10/tuya-to-tasmota-to-esphome/) for firmware conversion details.

### Sonoff TH10/TH16 WiFi Relay

- [Template](/templates/sonoff_th10.yaml) for the [Sonoff TH10](https://www.amazon.com/Sonoff-Temperature-Monitoring-Assistant-DS18B20/dp/B08DFQ2NP3) and [Sonoff TH16](https://www.amazon.com/Sonoff-Temperature-Humidity-Monitoring-Assistant/dp/B07TF5SYGL) WiFi relay.
- Follow the Tasmota [guide](https://tasmota.github.io/docs/devices/Sonoff-TH/) for flashing instructions, but use the ESPHome firmware.

## Sonoff S31 WiFi Power Monitoring Plug

- [Template](./templates/sonoff_s31.yaml) for the [Sonoff S31](https://www.amazon.com/Sonoff-Monitoring-Certified-Assistant-Supporting/dp/B08GKGS197) US 120V AC WiFi power monitoring wall plug.
- Follow the Tasmota [guide](https://tasmota.github.io/docs/devices/Sonoff-S31/) for flashing instructions, but use the ESPHome firmware.

## Notes

### Renaming a Device

- Rename HA entities:
  - Stop HA container using `docker stop home-assistant`.
  - Reset config permissions:
    - `sudo chown -R nobody:users /data/appdata/home-assistant/config`
    - `sudo chmod -R u=rwx,g=rwx+s,o=rx /data/appdata/home-assistant/config`
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
