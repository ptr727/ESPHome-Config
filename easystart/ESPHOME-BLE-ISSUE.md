# ESPHome Issue Draft: ble_client Service Release Crashes the Device <!-- omit from toc -->

Draft for an upstream ESPHome issue, with the evidence captured on this project's hardware. Nothing here is specific to the EasyStart component beyond it being the component that surfaced the fault.

## Summary

`ble_client` releases the peer's GATT database while a notify registration is still in flight, then calls an ESP-IDF API that walks that database. Bluedroid either returns `ESP_GATT_NOT_FOUND`, silently leaving the characteristic unsubscribed, or asserts on the freed list and panics the device.

Both outcomes were observed on the same firmware against the same peer. The ordering is not a race: the release always wins. Only the consequence of reading the freed list varies.

## Environment

- ESPHome 2026.7.2
- ESP-IDF v5.5.5, `framework: type: esp-idf`
- ESP32-S3 rev0.2 (Unexpected Maker ProS3D), 16MB flash, 8MB quad PSRAM
- `esp32_ble: max_connections: 2`, two `ble_client` entries, no `bluetooth_proxy`
- `esp32_ble_tracker` at stock scan parameters with `active: false`

The `esp32_ble_client` and `ble_client` sources in 2026.7.2 are byte-identical to `dev` at the time of writing, so the defect is present on both.

## Symptom

```text
[12:17:50][D][esp32_ble_client:212]: [0] ESP_GATTC_SEARCH_CMPL_EVT
[12:17:50][I][esp32_ble_client:465]: [0] Service discovery complete
[12:17:50][D][ble_client:056]: All clients established, services released
[12:17:50][D][esp32_ble_client:411]: [0] cfg_mtu status 0, mtu 23
[12:17:50]assert failed: list_end list.c:272 (list != NULL)
[12:17:50]rst:0xc (RTC_SW_CPU_RST),boot:0x2b (SPI_FAST_FLASH_BOOT)
```

Decoded backtrace, innermost first:

```text
panic_abort                          panic.c:477
esp_system_abort                     esp_system_chip.c:87
__assert_func                        assert.c:81
list_end                             common/osi/list.c:272
bta_gattc_get_db_with_operation      bta/gatt/bta_gattc_cache.c:1637
BTA_GATTC_GetDescrByCharHandle       bta/gatt/bta_gattc_api.c:432
btc_ble_gattc_get_descr_by_char_handle  btc/profile/std/gatt/btc_gattc.c:516
esp_ble_gattc_get_descr_by_char_handle  api/esp_gattc_api.c:533
BLEClientBase::gattc_event_handler   esphome/components/esp32_ble_client/ble_client_base.cpp:509
BLEClient::gattc_event_handler       esphome/components/ble_client/ble_client.cpp:48
ESP32BLETracker::gattc_event_handler esphome/components/esp32_ble_tracker/esp32_ble_tracker.cpp:424
```

The device reboots with reset reason `exception/panic`, confirmed by the uptime counter resetting to zero.

## Root Cause

Three ESPHome behaviors combine.

**1. The release is triggered from inside the same event dispatch that runs the nodes.** [`BLEClient::gattc_event_handler`][ble-client-handler] forwards each GATT event to every node, then immediately releases the services if all nodes report established:

```cpp
for (auto *node : this->nodes_)
  node->gattc_event_handler(event, esp_gattc_if, param);

if (!this->services_.empty() && this->all_nodes_established_()) {
  this->release_services();
  ESP_LOGD(TAG, "All clients established, services released");
}
```

**2. The release frees Bluedroid's database, not only ESPHome's mirror of it.** [`BLEClientBase::release_services()`][release-services] deletes the local `services_` vector and then calls `esp_ble_gattc_cache_clean()`, which frees the GATT cache inside Bluedroid.

**3. A later event walks the freed database.** `esp_ble_gattc_register_for_notify()` is asynchronous. When its [`ESP_GATTC_REG_FOR_NOTIFY_EVT`][reg-for-notify] arrives, `BLEClientBase` looks the CCCD up by characteristic handle:

```cpp
case ESP_GATTC_REG_FOR_NOTIFY_EVT: {
  ...
  esp_gatt_status_t descr_status = esp_ble_gattc_get_descr_by_char_handle(
      this->gattc_if_, this->conn_id_, param->reg_for_notify.handle, NOTIFY_DESC_UUID, &desc_result, &count);
```

That lookup reaches into the freed cache. `ESP_GATTC_REG_FOR_NOTIFY_EVT` carries no `conn_id`, so unlike every other event in this handler it has no existing guard to piggyback on.

**What opens the window.** Any node that reports `ClientState::ESTABLISHED` before its own notify registration has completed makes `all_nodes_established_()` true while a registration is outstanding. The contract is undocumented, [`node_state`][node-state] is a public field, and most bundled node types do set it directly in `ESP_GATTC_SEARCH_CMPL_EVT` ([`ble_switch.cpp`][ble-switch], [`ble_rssi_sensor.cpp`][ble-rssi], several classes in [`automation.h`][automation]). Only [`sensor`][ble-sensor] and [`text_sensor`][ble-text-sensor] with `notify: true` wait for `ESP_GATTC_REG_FOR_NOTIFY_EVT`. Copying the common pattern into a component that registers for notifications is enough to trigger this, and the penalty is a hard crash rather than a warning.

## Evidence

### Production capture

From a single continuous 80 minute serial capture on one device and one build, every release raced the registration:

| Time | `services released` | Outcome |
|---|---|---|
| 11:49:40 | yes | `get_descr_by_char_handle error, status=10` |
| 12:17:50 | yes | **assert, panic, reboot** |
| 12:18:03 | yes | `get_descr_by_char_handle error, status=10` |
| 12:54:27 | yes | `get_descr_by_char_handle error, status=10` |
| 12:57:53 | yes | `get_descr_by_char_handle error, status=10` |

Status 10 is `ESP_GATT_NOT_FOUND`. Five releases, five races, one abort. The four non-fatal outcomes are not successes: the handler breaks out before `esp_ble_gattc_write_char_descr()`, so the CCCD is never written and no notification ever arrives, while the node believes it is subscribed.

### Deterministic reproduction

A minimal node that registers for notifications and then reports `ESTABLISHED` reproduces the race on every connection. See [`test/components/ble_notify_race/`][race-component] and [`ble-notify-race-test.yaml`][race-config], which forces a reconnect every 60 seconds so cycles do not depend on the peer's duty cycle.

Four consecutive cycles on stock 2026.7.2, with a temporary diagnostic added to `BLEClient::gattc_event_handler`:

```text
DIAG event=6 services=3 nodes=2 client_state=6 all_established=1
All clients established, services released
[W][esp32_ble_client:224]: esp_ble_gattc_get_descr_by_char_handle error, status=10
DIAG event=38 services=0 nodes=2 client_state=6 all_established=1
```

Event 6 is `ESP_GATTC_SEARCH_CMPL_EVT` and event 38 is `ESP_GATTC_REG_FOR_NOTIFY_EVT`. The service vector goes from 3 entries to 0 between them, and the CCCD lookup lands after the release.

### Why this is not seen more often

Several bundled node types register themselves as BLE nodes but never reach `ESTABLISHED`, which pins `all_nodes_established_()` false and disables the release entirely for that client. [`BLEClientDisconnectAction`][disconnect-action] never assigns `node_state` at all, [`BLEClientConnectAction`][connect-action] assigns it only while the action is mid-flight because both return early when `num_running_ == 0`, and the three GAP triggers never assign it either.

A single `ble_client.disconnect` action anywhere in a configuration is therefore enough to suppress the release, and with it this crash, for the whole client. That also means those configurations never free the service memory the release exists to reclaim. This is a separate defect with its own fix, which has to land after the one below: re-enabling the release also re-exposes those configurations to the crash.

## Fix

Two independent changes, either of which prevents the crash.

**Hold the release while a registration is outstanding.** A new `BLEClientBase::register_for_notify()` wraps `esp_ble_gattc_register_for_notify()` and counts outstanding requests, `ESP_GATTC_REG_FOR_NOTIFY_EVT` retires them, and [`BLEClient::gattc_event_handler`][ble-client-handler] skips the release while the count is non-zero. The release still happens, one event later, so the memory optimization is preserved.

**Guard the lookup.** `release_services()` sets a `services_released_` flag on the path that actually calls `esp_ble_gattc_cache_clean()`, `connect()` clears it, and the `ESP_GATTC_REG_FOR_NOTIFY_EVT` handler returns early with a warning rather than calling into a cache that is gone. This covers external components that call the ESP-IDF API directly and so are invisible to the counter. A `CONFIG_BT_GATTC_CACHE_NVS_FLASH` build never cleans the stack cache, so the flag stays false there and the lookup proceeds as before.

The [`BLEClientNode::node_state`][node-state] comment is extended to state the ordering requirement.

### Validation

All three runs used the same hardware, peer, and harness, differing only in the ESPHome sources.

| Build | Result |
|---|---|
| Stock 2026.7.2, raw ESP-IDF registration | `status=10` on 4 of 4 cycles, release before the lookup |
| Fix, raw ESP-IDF registration | Guard fires on 3 of 3 cycles, `REG_FOR_NOTIFY after services released`, no call into Bluedroid |
| Fix, registration via `register_for_notify()` | Release held on 3 of 3 cycles, `notify_pending=1` at `SEARCH_CMPL`, lookup succeeds, release runs immediately after |

The third run is the intended path and shows the release still happening:

```text
DIAG event=6  services=3 nodes=2 client_state=6 all_established=1 notify_pending=1
REG_FOR_NOTIFY handle 14, status 0, services held
DIAG event=38 services=3 nodes=2 client_state=6 all_established=1 notify_pending=0
All clients established, services released
```

## Possibly Related

[esphome/esphome#17437][issue-17437] reports a silent hang whose last log line is `All clients established, services released`. The symptom differs and no backtrace is available, so this is noted rather than claimed.

## Note on the Component That Surfaced This

The component in this repository was setting `ESTABLISHED` during `ESP_GATTC_SEARCH_CMPL_EVT`, immediately after requesting the subscription, which is what opened the window on every connection. That is fixed separately in [`components/easystart/easystart.h`][easystart-header] by moving the state change into `ESP_GATTC_REG_FOR_NOTIFY_EVT` with a status check, matching the pattern ESPHome's own `ble_client` sensor uses.

That fix removes this project's exposure. It does not remove the underlying defect.

<!-- Repo -->

[easystart-header]: ./components/easystart/easystart.h
[race-component]: ./test/components/ble_notify_race/
[race-config]: ../ble-notify-race-test.yaml

<!-- External -->

[automation]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/automation.h#L33
[ble-client-handler]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/ble_client.cpp#L46-L59
[ble-rssi]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/sensor/ble_rssi_sensor.cpp#L33-L34
[ble-sensor]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/sensor/ble_sensor.cpp#L116-L128
[ble-switch]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/switch/ble_switch.cpp#L22-L23
[ble-text-sensor]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/text_sensor/ble_text_sensor.cpp#L116-L120
[connect-action]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/automation.h#L326-L330
[disconnect-action]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/automation.h#L367-L375
[issue-17437]: https://github.com/esphome/esphome/issues/17437
[node-state]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/ble_client.h#L34-L37
[reg-for-notify]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/esp32_ble_client/ble_client_base.cpp#L499-L514
[release-services]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/esp32_ble_client/ble_client_base.cpp#L196-L205
