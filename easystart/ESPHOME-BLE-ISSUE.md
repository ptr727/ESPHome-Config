# ESPHome Issue: ble_client Walks a Freed GATT Cache <!-- omit from toc -->

Filed upstream as [esphome/esphome#17921][issue-17921-link] on 2026-07-28, with the fixes proposed in [#17919][pr-17919-link] and [#17920][pr-17920-link]. This file is the source that issue was generated from, kept here so the evidence and the reasoning stay with the project that found the fault.

Each `##` heading is one field of the [ESPHome bug report form][bug-report-form-link], which is the layout the filed issue uses.

## The problem

A `ble_client` connected to a BLE peripheral panics the device and reboots it, or silently fails to subscribe to notifications. Both happen on the same firmware against the same peer, and which one occurs is not predictable.

`ble_client` releases the peer's discovered services once every node reports `ESTABLISHED`, and `release_services()` calls `esp_ble_gattc_cache_clean()`, which frees Bluedroid's GATT database rather than only ESPHome's mirror of it. `esp_ble_gattc_register_for_notify()` completes asynchronously, so a node that reports `ESTABLISHED` while its own registration is still in flight makes that release run first. When `ESP_GATTC_REG_FOR_NOTIFY_EVT` then arrives, `BLEClientBase` calls `esp_ble_gattc_get_descr_by_char_handle()` on the freed database.

Bluedroid responds one of two ways:

- It returns `ESP_GATT_NOT_FOUND` (status 10). The handler breaks out before `esp_ble_gattc_write_char_descr()`, so the CCCD is never written and no notification ever arrives, while the node believes it is subscribed. That is a silent failure rather than a warning a user would act on.
- It asserts on the freed list and aborts with `assert failed: list_end list.c:272 (list != NULL)`. The device panics and reboots.

In an 80 minute capture on a deployed device, five service releases produced five races: four `status=10` and one panic.

`ESP_GATTC_REG_FOR_NOTIFY_EVT` carries no `conn_id`, so unlike every other event in that handler it has no existing guard to piggyback on.

## Which version of ESPHome has the issue?

```text
2026.7.2
```

The `esp32_ble_client` and `ble_client` sources in 2026.7.2 are byte-identical to `dev` at the time of writing, so `dev` is affected too.

## What type of installation are you using?

```text
Docker
```

## What platform are you using?

```text
ESP32
```

ESP32-S3, ESP-IDF 5.5.5, `framework: type: esp-idf`.

## Component causing the issue

```text
ble_client
```

The faulting call is in `esp32_ble_client`, reached through `ble_client`.

## YAML Config

Self-contained and verified to compile as written. It pulls the reproduction component from GitHub, so no local files are needed. Point `mac_address` at any peripheral exposing a notify characteristic and set the two UUIDs to match it.

```yaml
esphome:
  name: ble-notify-race

esp32:
  board: esp32dev
  framework:
    type: esp-idf

logger:
  level: DEBUG

# A minimal BLEClientNode that registers for notifications and then reports
# ESTABLISHED in the same event, which is the ordering violation.
external_components:
  - source:
      type: git
      url: https://github.com/ptr727/ESPHome-Config
      ref: main
      path: easystart/test/components
    components: [ble_notify_race]

esp32_ble_tracker:
  scan_parameters:
    active: false

ble_client:
  - id: race_client
    mac_address: "AA:BB:CC:DD:EE:01"
    auto_connect: true

ble_notify_race:
  ble_client_id: race_client
  service_uuid: d973f2e0-b19e-11e2-9e96-0800200c9a66
  characteristic_uuid: d973f2e1-b19e-11e2-9e96-0800200c9a66

# A second, stock node, so both report ESTABLISHED inside SEARCH_CMPL and the
# release runs immediately.
sensor:
  - platform: ble_client
    ble_client_id: race_client
    type: rssi
    name: "Signal Strength"
    entity_category: diagnostic

# Forces a reconnect so the race is exercised on demand rather than waiting on
# the peer. Deliberately a lambda and not the ble_client.disconnect action, see
# the second defect under Additional information.
interval:
  - interval: 60s
    then:
      - lambda: |-
          id(race_client)->disconnect();
```

## Anything in the logs that might be useful for us?

```txt
The panic, from a serial capture on a deployed device:

[12:17:50][D][esp32_ble_client:212]: [0] ESP_GATTC_SEARCH_CMPL_EVT
[12:17:50][I][esp32_ble_client:465]: [0] Service discovery complete
[12:17:50][D][ble_client:056]: All clients established, services released
[12:17:50][D][esp32_ble_client:411]: [0] cfg_mtu status 0, mtu 23
[12:17:50]assert failed: list_end list.c:272 (list != NULL)
[12:17:50]rst:0xc (RTC_SW_CPU_RST),boot:0x2b (SPI_FAST_FLASH_BOOT)

Decoded backtrace, innermost first:

panic_abort                             panic.c:477
esp_system_abort                        esp_system_chip.c:87
__assert_func                           assert.c:81
list_end                                common/osi/list.c:272
bta_gattc_get_db_with_operation         bta/gatt/bta_gattc_cache.c:1637
BTA_GATTC_GetDescrByCharHandle          bta/gatt/bta_gattc_api.c:432
btc_ble_gattc_get_descr_by_char_handle  btc/profile/std/gatt/btc_gattc.c:516
esp_ble_gattc_get_descr_by_char_handle  api/esp_gattc_api.c:533
BLEClientBase::gattc_event_handler      esphome/components/esp32_ble_client/ble_client_base.cpp:509
BLEClient::gattc_event_handler          esphome/components/ble_client/ble_client.cpp:48
ESP32BLETracker::gattc_event_handler    esphome/components/esp32_ble_tracker/esp32_ble_tracker.cpp:424

The device reboots with reset reason exception/panic.

The non-fatal variant, from the same capture and the same code path:

[11:49:40][D][esp32_ble_client:212]: [0] ESP_GATTC_SEARCH_CMPL_EVT
[11:49:40][I][esp32_ble_client:465]: [0] Service discovery complete
[11:49:40][D][ble_client:056]: All clients established, services released
[11:49:40][W][esp32_ble_client:224]: [0] esp_ble_gattc_get_descr_by_char_handle error, status=10

Status 10 is ESP_GATT_NOT_FOUND. The CCCD is never written, so no notification
arrives for that connection.

Four consecutive cycles on stock 2026.7.2, with a temporary ESP_LOGW added to
BLEClient::gattc_event_handler printing the gate inputs. Event 6 is
ESP_GATTC_SEARCH_CMPL_EVT, event 38 is ESP_GATTC_REG_FOR_NOTIFY_EVT:

DIAG event=6 services=3 nodes=2 client_state=6 all_established=1
All clients established, services released
[W][esp32_ble_client:224]: esp_ble_gattc_get_descr_by_char_handle error, status=10
DIAG event=38 services=0 nodes=2 client_state=6 all_established=1

The service vector goes from 3 entries to 0 between the two events, and the
CCCD lookup lands after the release.
```

## Additional information

### Root cause

Three behaviors combine.

**1. The release runs inside the same event dispatch as the nodes.** [`BLEClient::gattc_event_handler`][ble-client-handler-link] forwards each event to every node, then [releases immediately][ble-client-release-link] if all nodes report established.

**2. The release frees Bluedroid's database, not only ESPHome's mirror.** [`release_services()`][release-services-link] clears the local `services_` vector and calls `esp_ble_gattc_cache_clean()`.

**3. A later event walks the freed database.** The [`ESP_GATTC_REG_FOR_NOTIFY_EVT` handler][reg-for-notify-handler-link] calls [`esp_ble_gattc_get_descr_by_char_handle()`][get-descr-link].

### What opens the window

Any node reporting `ClientState::ESTABLISHED` before its own registration completes makes `all_nodes_established_()` true while a registration is outstanding. The contract is undocumented, [`node_state`][node-state-link] is a public field, and most bundled node types assign it directly in `ESP_GATTC_SEARCH_CMPL_EVT`: [`ble_switch.cpp`][ble-switch-link], [`ble_rssi_sensor.cpp`][ble-rssi-sensor-link], several classes in [`automation.h`][automation-link]. Only [`sensor`][ble-sensor-link] and [`text_sensor`][ble-text-sensor-link] with `notify: true` wait for the registration.

The code that trips this is therefore code implementing `BLEClientNode` directly and copying the pattern the bundled non-subscribing nodes use. The penalty for getting it wrong is a panic rather than an error.

### How it was originally hit

Not constructed. A deployed device crashed. The component was an external `BLEClientNode` polling a Micro-Air EasyStart soft starter, which requested its subscription and reported `ESTABLISHED` four lines later in the same event:

```cpp
auto err = esp_ble_gattc_register_for_notify(gattc_if, this->parent()->get_remote_bda(), this->notify_handle_);
if (err != ESP_OK)
  ESP_LOGW(TAG, "register_for_notify failed, err=%d", err);
this->node_state = espbt::ClientState::ESTABLISHED;
```

It has since been [corrected][easystart-header-link] to establish inside `ESP_GATTC_REG_FOR_NOTIFY_EVT` after checking `param->reg_for_notify.status`. That removes the exposure for that project but not the defect: obeying an unwritten rule is a workaround, and the failure mode for breaking it is a reboot.

The reduced reproduction in the YAML above is [`ble_notify_race`][race-component-link], roughly 60 lines carrying no protocol knowledge, driven by [`ble-notify-race-test.yaml`][race-config-link].

### Why this is rarely hit, and a second defect

Several `ble_client` nodes register themselves via `register_ble_node()` but never report `ESTABLISHED`, which pins `all_nodes_established_()` false and suppresses the release entirely for that client. That masks this crash, and leaks the service memory the release exists to reclaim.

| Node | Behavior |
|---|---|
| [`BLEClientDisconnectAction`][disconnect-action-link] | Never assigns `node_state` at all |
| [`BLEClientConnectAction`][connect-action-link] | Only while the action runs, both return early when `num_running_ == 0` |
| [`BLEClientPasskeyRequestTrigger`][passkey-request-link] | Handles only GAP events, never assigns it |
| [`BLEClientPasskeyNotificationTrigger`][passkey-notification-link] | Same |
| [`BLEClientNumericComparisonRequestTrigger`][numeric-comparison-link] | Same |

A single `ble_client.disconnect` action anywhere in a configuration is therefore enough to hide this crash, which is why the reproduction config drives its reconnects from a `lambda` instead.

That interaction is observable in the wild. [Keen-coffee/home_assistant][keen-coffee-link] reads the same hardware using only stock components and is protected twice over: its `ble_client.disconnect` action suppresses the release, and separately its subscription is the stock characteristic sensor, which orders correctly. It pays the leak instead of the crash.

### Suggested fix

Both parts are implemented and hardware-validated:

- [esphome/esphome#17919][pr-17919-link] holds the release while a registration is outstanding, and guards the lookup for external components that call the ESP-IDF API directly.
- [esphome/esphome#17920][pr-17920-link] fixes the nodes that never report established. Held in draft until the first merges, because restoring the release re-exposes those configurations to this crash.

| Build | Result |
|---|---|
| Stock 2026.7.2 | `status=10` on 4 of 4 cycles, release before the lookup |
| Fix, node using the raw ESP-IDF call | Guard fires on 3 of 3, no call into Bluedroid |
| Fix, node using `register_for_notify()` | Release held on 3 of 3, lookup succeeds, release still runs |

### Possibly related

[esphome/esphome#17437][issue-17437-link] reports a silent hang whose last log line is `All clients established, services released`. The symptom differs and no backtrace is available, so this is noted rather than claimed as the same defect.

<!-- External -->

[automation-link]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/automation.h#L33
[ble-client-handler-link]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/ble_client.cpp#L46-L59
[ble-client-release-link]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/ble_client.cpp#L54-L57
[ble-rssi-sensor-link]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/sensor/ble_rssi_sensor.cpp#L33-L34
[ble-sensor-link]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/sensor/ble_sensor.cpp#L116-L128
[ble-switch-link]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/switch/ble_switch.cpp#L22-L23
[ble-text-sensor-link]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/text_sensor/ble_text_sensor.cpp#L116-L120
[bug-report-form-link]: https://github.com/esphome/esphome/issues/new/choose
[connect-action-link]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/automation.h#L326-L330
[disconnect-action-link]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/automation.h#L367-L375
[easystart-header-link]: https://github.com/ptr727/ESPHome-Config/blob/main/easystart/components/easystart/easystart.h
[get-descr-link]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/esp32_ble_client/ble_client_base.cpp#L509-L510
[issue-17437-link]: https://github.com/esphome/esphome/issues/17437
[issue-17921-link]: https://github.com/esphome/esphome/issues/17921
[keen-coffee-link]: https://github.com/Keen-coffee/home_assistant/blob/main/easyStart
[node-state-link]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/ble_client.h#L34-L37
[numeric-comparison-link]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/automation.h#L84-L93
[passkey-notification-link]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/automation.h#L73-L82
[passkey-request-link]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/automation.h#L63-L71
[pr-17919-link]: https://github.com/esphome/esphome/pull/17919
[pr-17920-link]: https://github.com/esphome/esphome/pull/17920
[race-component-link]: https://github.com/ptr727/ESPHome-Config/tree/main/easystart/test/components/ble_notify_race
[race-config-link]: https://github.com/ptr727/ESPHome-Config/blob/main/ble-notify-race-test.yaml
[reg-for-notify-handler-link]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/esp32_ble_client/ble_client_base.cpp#L499-L514
[release-services-link]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/esp32_ble_client/ble_client_base.cpp#L196-L205
