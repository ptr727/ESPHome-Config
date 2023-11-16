# ESPHome-Config

ESPHome configuration.

## Deployment

- Run [ESPHome](https://hub.docker.com/r/esphome/esphome) in a Docker container.
  - Run the container as `root`, running as a regular user results in permission [problems](https://github.com/esphome/issues/issues/3558).
  - Run using `macvlan` and a static IP to support automatic device discovery.
  - Make sure that container user has correct file and directory permissions, e.g.:
    - `sudo chown -R nobody:users /data/appdata/esphome/config`
    - `sudo chmod -R ugo+rwx /data/appdata/esphome/config`
  - Make sure that container user has Git permissions for mixed user file permissions.
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

- [Template](./templates/aoycocr_x5p.yaml) for the [Ayococr X5P](https://www.amazon.com/dp/B07R6CT3G7) US 120V AC WiFi wall plug.
- See blog [post](https://blog.insanegenius.com/2020/09/10/tuya-to-tasmota-to-esphome/) for firmware conversion details.

### EFUN SH331 WiFi Power Monitoring Plug

- [Template](./templates/efun_sh331.yaml) for the [EFUN SH331W](https://www.amazon.com/gp/product/B07DCJ7TDR) US 120V AC WiFi power monitoring wall plug.
- See blog [post](https://blog.insanegenius.com/2020/09/10/tuya-to-tasmota-to-esphome/) for firmware conversion details.

### Sonoff TH10/TH16 WiFi Relay

- [Template](/templates/sonoff_th10.yaml) for the [Sonoff TH10](https://www.amazon.com/Sonoff-Temperature-Monitoring-Assistant-DS18B20/dp/B08DFQ2NP3) and [Sonoff TH16](https://www.amazon.com/Sonoff-Temperature-Humidity-Monitoring-Assistant/dp/B07TF5SYGL) WiFi relay.
- Follow the Tasmota [guide](https://tasmota.github.io/docs/devices/Sonoff-TH/) for flashing instructions, but use the ESPHome firmware.

### Sonoff S31 WiFi Power Monitoring Plug

- [Template](./templates/sonoff_s31.yaml) for the [Sonoff S31](https://www.amazon.com/Sonoff-Monitoring-Certified-Assistant-Supporting/dp/B08GKGS197) US 120V AC WiFi power monitoring wall plug.
- Follow the Tasmota [guide](https://tasmota.github.io/docs/devices/Sonoff-S31/) for flashing instructions, but use the ESPHome firmware.

## Projects

### Garage Fan Thermostat

- The [`garage-gate-fan.yaml`](./garage-gate-fan.yaml) and [`garage-door-fan.yaml`](./garage-door-fan.yaml) configs are used to control Sonoff TH16's as thermostats for cool air ventilation in my garage.
- See blog [post](https://blog.insanegenius.com/2021/08/11/trying-to-keep-my-garage-cool/) for project details.

### Utility Gas and Water Meter Pulse Counter

- The [`utility-pulse-counter.yaml`](./utility-pulse-counter.yaml) config is used to measure water and gas consumption from utility meter pulse counters.
- See blog [post](https://blog.insanegenius.com/2021/08/09/esp32-water-and-gas-utility-meter/) for project details.

### Hot Water Recirculation Pump

- The [`hot-water-recirc-pump.yaml`](./hot-water-recirc-pump.yaml) config is used to control my whole home hot water recirculation pump using a Sonoff TH16 and several temperature probes.
- See blog [post](https://blog.insanegenius.com/2020/10/11/hot-water-recirculation-pump-controller/) for project details.

### TubesZB Ethernet Zigbee Coordinator

- Customized version of the [TubesZB Ethernet Zigbee Coordinator](https://github.com/tube0013/tube_gateways/blob/main/models/current/tubeszb-cc2652-eth_usb/firmware/esphome/tubezb-cc2652p2-ethusb-2022.yaml).

### RatGDO Garage Door Controller

- Customized version of the [RatGDO Garage Door Controller](https://github.com/ratgdo/esphome-ratgdo/blob/main/static/v25board_esp8266_d1_mini_lite.yaml).

## Notes

### Hardware Availability

- The Sonoff TH10 and TH16 have been replaced by the [SONOFF TH Origin](https://itead.cc/product/sonoff-th/), see the [Tasmota Templates](https://templates.blakadder.com/sonoff_THR316.html) for pin layouts.
- EFUN SH331W is no longer listed on Amazon.
- I have switched away from WiFi smart plugs and now use [Sengled](https://www.amazon.com/gp/product/B092DBFFBY/) Zigbee power monitoring smart plugs, much easier to deploy.

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

### TODO

- Consolidate common templates, e.g. sensors, to be included in the common templates.
- Update TubesZB when [PR #7](https://github.com/tube0013/esphome-stream-server-v2/pull/7) is merged.
