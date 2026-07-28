# ESPHome Issue Draft: ble_client Service Release Crashes the Device <!-- omit from toc -->

Draft for an upstream ESPHome issue, with the evidence captured on this project's hardware. Nothing here is specific to the EasyStart component beyond it being the component that surfaced the fault.

## Summary

`ble_client` releases the peer's GATT database while a notify registration is still in flight, then calls an ESP-IDF API that walks that database. Bluedroid asserts on the freed list and the device panics and reboots, rather than returning an error.

The failure is a race, so the same code path recovers gracefully most of the time and hard-crashes occasionally. In one 80 minute capture the release ran five times and crashed once.

## Environment

- ESPHome 2026.7.2
- ESP-IDF v5.5.5, `framework: type: esp-idf`
- ESP32-S3 rev0.2 (Unexpected Maker ProS3D), 16MB flash, 8MB quad PSRAM
- `esp32_ble: max_connections: 2`, two `ble_client` entries, no `bluetooth_proxy`
- `esp32_ble_tracker` at stock scan parameters with `active: false`

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

Two ESPHome code paths combine.

**1. The release is triggered from inside the same event dispatch that runs the nodes.** `BLEClient::gattc_event_handler` forwards each GATT event to every node, then immediately releases the services if all nodes report established:

```cpp
for (auto *node : this->nodes_)
  node->gattc_event_handler(event, esp_gattc_if, param);

if (!this->services_.empty() && this->all_nodes_established_()) {
  this->release_services();
  ESP_LOGD(TAG, "All clients established, services released");
}
```

**2. The release frees Bluedroid's database, not only ESPHome's mirror of it.** `BLEClientBase::release_services()` deletes the local `services_` vector and then calls `esp_ble_gattc_cache_clean()`:

```cpp
void BLEClientBase::release_services() {
  for (auto &svc : this->services_)
    delete svc;
  this->services_.clear();
#ifndef CONFIG_BT_GATTC_CACHE_NVS_FLASH
  esp_ble_gattc_cache_clean(this->remote_bda_);
#endif
```

**3. A later event walks the freed database.** `esp_ble_gattc_register_for_notify()` is asynchronous. When its `ESP_GATTC_REG_FOR_NOTIFY_EVT` arrives, `BLEClientBase` looks the CCCD up by character handle:

```cpp
case ESP_GATTC_REG_FOR_NOTIFY_EVT: {
  ...
  esp_gatt_status_t descr_status = esp_ble_gattc_get_descr_by_char_handle(
      this->gattc_if_, this->conn_id_, param->reg_for_notify.handle, NOTIFY_DESC_UUID, &desc_result, &count);
```

If the cache was cleaned between the registration request and its completion event, that lookup reaches a freed list. Bluedroid sometimes returns a status (ESPHome then logs `esp_ble_gattc_get_descr_by_char_handle` with status 10 and continues) and sometimes asserts on a NULL list and aborts the firmware.

**What opens the window.** Any node that reports `ClientState::ESTABLISHED` before its own notify registration has completed makes `all_nodes_established_()` true while a registration is outstanding. ESPHome's bundled `ble_client` sensor avoids this by establishing only in `ESP_GATTC_REG_FOR_NOTIFY_EVT`, but nothing enforces the ordering, the field is public to external components, and the penalty for getting it wrong is a hard crash rather than a warning.

## Evidence That It Is a Race

From a single continuous 80 minute serial capture on one device and one build:

| Time | `services released` | Outcome |
|---|---|---|
| 11:49:40 | yes | no fault |
| 12:17:50 | yes | **assert, panic, reboot** |
| 12:18:03 | yes | no fault |
| 12:54:27 | yes | no fault |
| 12:57:53 | yes | graceful `status=10` warning |

Same firmware, same peer, same code path, five times, one crash. Whether the freed list reads as NULL or as an empty-but-valid structure decides between a warning and an abort.

## Suggested Remediation

Either fix alone prevents the crash. Doing both is cheap.

**A. Do not release while a registration is outstanding.** Track notify registrations requested against `ESP_GATTC_REG_FOR_NOTIFY_EVT` received, and skip the release in `BLEClient::gattc_event_handler` while the count is non-zero. This preserves the memory optimization and removes the window entirely.

**B. Guard the lookup.** In the `ESP_GATTC_REG_FOR_NOTIFY_EVT` handler, return early when the services have already been released, logging a warning instead of calling into Bluedroid:

```cpp
case ESP_GATTC_REG_FOR_NOTIFY_EVT: {
  if (this->services_released_) {
    ESP_LOGW(TAG, "[%d] notify registration completed after services were released", this->connection_index_);
    break;
  }
```

This needs a small flag set in `release_services()` and cleared on connect, because `services_` being empty is not by itself a reliable signal on every build configuration.

**C. Document the node contract.** State in the external-component documentation that a `BLEClientNode` using notifications must set `node_state = ESTABLISHED` only from `ESP_GATTC_REG_FOR_NOTIFY_EVT`, after checking `param->reg_for_notify.status`.

A defensive fix in Bluedroid (returning an error rather than asserting when the DB is absent) belongs upstream of ESPHome and is not proposed here.

## Note on the Component That Surfaced This

The component in this repository was setting `ESTABLISHED` during `ESP_GATTC_SEARCH_CMPL_EVT`, immediately after requesting the subscription, which is what opened the window on every connection. That is fixed separately in [`components/easystart/easystart.h`][easystart-header] by moving the state change into `ESP_GATTC_REG_FOR_NOTIFY_EVT` with a status check, matching the pattern ESPHome's own `ble_client` sensor uses.

That fix removes this project's exposure. It does not remove the underlying defect: the release still races any outstanding registration, and the failure mode is still a panic rather than an error.

<!-- Repo -->

[easystart-header]: ./components/easystart/easystart.h
