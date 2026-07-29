# ESPHome Issue Draft: Two Defects in the ble_client Service Release <!-- omit from toc -->

Draft for upstream ESPHome issues, with the evidence captured on this project's hardware. Nothing here is specific to the EasyStart component beyond it being the component that surfaced the first fault.

Both defects sit on the same mechanism, the release of discovered services once every node reports `ESTABLISHED`, and they interact, so they are drafted together.

- **[Defect 1][defect-1]** crashes the device. The release frees the peer's GATT database while a notify registration is still in flight, and a later event walks the freed database.
- **[Defect 2][defect-2]** wastes memory. Several bundled nodes never report `ESTABLISHED`, so the release never runs for their client.

They must be fixed in that order. Defect 2 currently masks defect 1, so fixing defect 2 first turns a latent crash into a reachable one.

## Defect 1: The Release Races an Outstanding Notify Registration

`ble_client` releases the peer's GATT database while a notify registration is still in flight, then calls an ESP-IDF API that walks that database. Bluedroid either returns `ESP_GATT_NOT_FOUND`, silently leaving the characteristic unsubscribed, or asserts on the freed list and panics the device.

Both outcomes were observed on the same firmware against the same peer. The ordering is not a race: the release always wins. Only the consequence of reading the freed list varies.

### Environment

- ESPHome 2026.7.2
- ESP-IDF v5.5.5, `framework: type: esp-idf`
- ESP32-S3 rev0.2 (Unexpected Maker ProS3D), 16MB flash, 8MB quad PSRAM
- `esp32_ble: max_connections: 2`, two `ble_client` entries, no `bluetooth_proxy`
- `esp32_ble_tracker` at stock scan parameters with `active: false`

The `esp32_ble_client` and `ble_client` sources in 2026.7.2 are byte-identical to `dev` at the time of writing, so the defect is present on both.

### Symptom

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

### Root Cause

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

### Evidence

#### The configuration that hit this

This was not constructed. A deployed device crashed, and the code below is the component as it ran, from [`easystart.h`][easystart-header] before its own fix.

```cpp
case ESP_GATTC_SEARCH_CMPL_EVT: {
  auto *nt = this->parent()->get_characteristic(espbt::ESPBTUUID::from_raw(SERVICE_UUID),
                                                espbt::ESPBTUUID::from_raw(NOTIFY_UUID));
  ...
  this->notify_handle_ = nt->handle;
  auto err = esp_ble_gattc_register_for_notify(gattc_if, this->parent()->get_remote_bda(), this->notify_handle_);
  if (err != ESP_OK)
    ESP_LOGW(TAG, "register_for_notify failed, err=%d", err);
  this->node_state = espbt::ClientState::ESTABLISHED;
  ...
}
```

The registration is requested and the node reports `ESTABLISHED` four lines later, in the same event, while the registration is still in flight. The component is an `esphome::ble_client::BLEClientNode` polling a Micro-Air EasyStart soft starter over the Laird VSP service.

The YAML, reduced to the parts that matter (WiFi, API, OTA, and the board package omitted):

```yaml
esp32_ble:
  max_connections: 2

esp32_ble_tracker:
  scan_parameters:
    active: false

external_components:
  - source:
      type: local
      path: easystart/components
    components: [easystart]

ble_client:
  - id: easystart_downstairs
    mac_address: XX:XX:XX:XX:XX:XX
    auto_connect: true

easystart:
  - ble_client_id: easystart_downstairs
    update_interval: 5s
    running:
      name: "Downstairs Running"
    current:
      name: "Downstairs Current"

sensor:
  - platform: ble_client
    ble_client_id: easystart_downstairs
    type: rssi
    name: "Downstairs Signal Strength"
    entity_category: diagnostic
    update_interval: 60s
```

The `type: rssi` sensor is a stock ESPHome node and matters: it reports `ESTABLISHED` during `ESP_GATTC_SEARCH_CMPL_EVT`, so both nodes on the client are established inside that one event and the release runs immediately.

#### Production capture

From a single continuous 80 minute serial capture on one device and one build, every release raced the registration:

| Time | `services released` | Outcome |
|---|---|---|
| 11:49:40 | yes | `get_descr_by_char_handle error, status=10` |
| 12:17:50 | yes | **assert, panic, reboot** |
| 12:18:03 | yes | `get_descr_by_char_handle error, status=10` |
| 12:54:27 | yes | `get_descr_by_char_handle error, status=10` |
| 12:57:53 | yes | `get_descr_by_char_handle error, status=10` |

Status 10 is `ESP_GATT_NOT_FOUND`. Five releases, five races, one abort. The four non-fatal outcomes are not successes: the handler breaks out before `esp_ble_gattc_write_char_descr()`, so the CCCD is never written and no notification ever arrives, while the node believes it is subscribed.

#### Minimal reproduction

Reproducing the above needs a Micro-Air soft starter, so the same violation is also kept as a standalone case that works against any peripheral with a notify characteristic. It is a committed, CI-compiled configuration rather than a snippet, so it can be checked out and flashed as is:

- [`ble-notify-race-test.yaml`][race-config], a complete device config. It forces a reconnect every 60 seconds so cycles do not depend on the peer's duty cycle, and it drives that from a `lambda` calling `disconnect()` rather than the `ble_client.disconnect` action, for the reason in [defect 2][defect-2].
- [`ble_notify_race`][race-component], a roughly 60 line `BLEClientNode` that registers for notifications and then reports `ESTABLISHED`. It carries no protocol knowledge, so any notify characteristic will do.

Point it at any such peripheral, flash, and every connection reproduces the release. The `DIAG` lines quoted above come from this configuration with a temporary log added to `BLEClient::gattc_event_handler`.

Four consecutive cycles on stock 2026.7.2, with a temporary diagnostic added to `BLEClient::gattc_event_handler`:

```text
DIAG event=6 services=3 nodes=2 client_state=6 all_established=1
All clients established, services released
[W][esp32_ble_client:224]: esp_ble_gattc_get_descr_by_char_handle error, status=10
DIAG event=38 services=0 nodes=2 client_state=6 all_established=1
```

Event 6 is `ESP_GATTC_SEARCH_CMPL_EVT` and event 38 is `ESP_GATTC_REG_FOR_NOTIFY_EVT`. The service vector goes from 3 entries to 0 between them, and the CCCD lookup lands after the release.

#### Why this is rarely hit

[Defect 2][defect-2] suppresses the release entirely for any client carrying a `ble_client` action or passkey trigger, and with it this crash. Reproducing defect 1 requires a configuration free of those nodes, which is why the harness above drives its reconnects from a `lambda` calling `disconnect()` rather than the `ble_client.disconnect` action.

An unrelated third-party configuration for the same hardware shows both effects together. [Keen-coffee/home_assistant][keen-coffee-easystart] reads the same EasyStart modules using only stock components, and is protected twice over:

- Its `ble_client.disconnect` action never reports `ESTABLISHED`, so `all_nodes_established_()` is permanently false for that client and the release never runs at all. That is defect 2 masking defect 1, in a configuration written without any knowledge of either.
- Its subscription is the stock `ble_client` characteristic sensor with `notify: true`, which establishes in `ESP_GATTC_REG_FOR_NOTIFY_EVT` after checking the status. Even with the actions removed, the ordering would still be correct.

What separates a configuration that crashes from one that does not is therefore whether a node assigns `node_state` itself, not how elaborate the configuration is. The stock nodes that subscribe to notifications order it correctly, so the undocumented contract only reaches code that implements `BLEClientNode` directly. That configuration also pays defect 2's cost in exchange: those services stay allocated for the life of every connection.

### Fix

Two independent changes, either of which prevents the crash.

**Hold the release while a registration is outstanding.** A new `BLEClientBase::register_for_notify()` wraps `esp_ble_gattc_register_for_notify()` and counts outstanding requests, `ESP_GATTC_REG_FOR_NOTIFY_EVT` retires them, and [`BLEClient::gattc_event_handler`][ble-client-handler] skips the release while the count is non-zero. The release still happens, one event later, so the memory optimization is preserved.

**Guard the lookup.** `release_services()` sets a `services_released_` flag on the path that actually calls `esp_ble_gattc_cache_clean()`, `connect()` clears it, and the `ESP_GATTC_REG_FOR_NOTIFY_EVT` handler returns early with a warning rather than calling into a cache that is gone. This covers external components that call the ESP-IDF API directly and so are invisible to the counter. A `CONFIG_BT_GATTC_CACHE_NVS_FLASH` build never cleans the stack cache, so the flag stays false there and the lookup proceeds as before.

The [`BLEClientNode::node_state`][node-state] comment is extended to state the ordering requirement.

#### Validation

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

## Defect 2: Nodes That Never Report Established Suppress the Release

Several `ble_client` nodes register themselves with [`register_ble_node()`][register-ble-node] but never report `ESTABLISHED`. [`all_nodes_established_()`][all-nodes-established] therefore stays false for the life of the connection, and the release in [`BLEClient::gattc_event_handler`][ble-client-handler] never runs.

A single such node anywhere in a configuration keeps the whole client's discovered services allocated, which is exactly the memory the release exists to reclaim.

### Affected Nodes

| Node | Behavior |
|---|---|
| [`BLEClientDisconnectAction`][disconnect-action] | Never assigns `node_state` at all |
| [`BLEClientConnectAction`][connect-action] | Assigns it only while the action runs, the handler returns early when `num_running_ == 0` |
| [`BLEClientPasskeyRequestTrigger`][passkey-request] | Handles only GAP events, never assigns `node_state` |
| [`BLEClientPasskeyNotificationTrigger`][passkey-notification] | Same |
| [`BLEClientNumericComparisonRequestTrigger`][numeric-comparison] | Same |

[`BLEClientConnectTrigger`][connect-trigger] and [`BLEClientDisconnectTrigger`][disconnect-trigger] already do this correctly. [`BLEClientWriteAction`][write-action] does need the services, so it correctly establishes only after resolving its characteristic.

### How This Was Found

A device with a `ble_client.disconnect` action in an `interval:` never logged `All clients established, services released`, despite every configured node being established. A temporary diagnostic in `BLEClient::gattc_event_handler` showed a third, unexpected node:

```text
DIAG event=6 services=3 nodes=3 client_state=6 all_established=0
DIAG   node_state=6
DIAG   node_state=5      <- BLEClientDisconnectAction, CONNECTED, never Established
DIAG   node_state=6
```

State 5 is `CONNECTED` and state 6 is `ESTABLISHED`. Replacing the action with a `lambda` calling `disconnect()` directly dropped the client to two nodes, and the release then fired on every connection.

### The Change

Add `BLEClientServicelessNode`, a base for nodes that never read the parent's services, which reports `ESTABLISHED` on `ESP_GATTC_SEARCH_CMPL_EVT`. The five nodes above derive from it. The two actions call the base handler ahead of their own `num_running_` gate, so they report it whether or not an action is running.

### Ordering

This has to land after the defect 1 fix. Restoring the release for these configurations also exposes them to the use-after-free, since the release is what frees the GATT cache that `ESP_GATTC_REG_FOR_NOTIFY_EVT` then walks. Fixing this one alone converts a latent crash into a reachable one for any configuration pairing a `ble_client` action with a notify subscription.

### Compile Coverage

Compiled against a configuration instantiating every affected node, since these are templates that only type-check when instantiated: `on_connect`, `on_disconnect`, `on_passkey_request`, `on_passkey_notification`, `on_numeric_comparison_request`, plus the `ble_client.connect`, `ble_client.ble_write`, and `ble_client.disconnect` actions.

## Possibly Related

[esphome/esphome#17437][issue-17437] reports a silent hang whose last log line is `All clients established, services released`. The symptom differs and no backtrace is available, so this is noted rather than claimed.

## Note on the Component That Surfaced This

This component is not the defect, it is how the defect was found. It is an external `BLEClientNode` that subscribes to notifications, and it reported `ESTABLISHED` during `ESP_GATTC_SEARCH_CMPL_EVT` immediately after requesting the subscription, which opened the window on every connection.

It now sets the state inside `ESP_GATTC_REG_FOR_NOTIFY_EVT` after checking `param->reg_for_notify.status`, matching the pattern ESPHome's own `ble_client` sensor uses, and the device no longer crashes.

That is a workaround, not a fix. It amounts to a component obeying a rule that is written down nowhere, and every other component is free to get it wrong. The penalty for getting it wrong is a panic and a reboot rather than an error, which is what the fix above addresses.

<!-- Repo -->

[defect-1]: #defect-1-the-release-races-an-outstanding-notify-registration
[defect-2]: #defect-2-nodes-that-never-report-established-suppress-the-release
[easystart-header]: ./components/easystart/easystart.h
[race-component]: https://github.com/ptr727/ESPHome-Config/tree/main/easystart/test/components/ble_notify_race
[race-config]: https://github.com/ptr727/ESPHome-Config/blob/main/ble-notify-race-test.yaml

<!-- External -->

[all-nodes-established]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/ble_client.cpp#L74-L83
[automation]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/automation.h#L33
[ble-client-handler]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/ble_client.cpp#L46-L59
[ble-rssi]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/sensor/ble_rssi_sensor.cpp#L33-L34
[ble-sensor]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/sensor/ble_sensor.cpp#L116-L128
[ble-switch]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/switch/ble_switch.cpp#L22-L23
[ble-text-sensor]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/text_sensor/ble_text_sensor.cpp#L116-L120
[connect-trigger]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/automation.h#L26-L36
[connect-action]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/automation.h#L326-L330
[disconnect-action]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/automation.h#L367-L375
[disconnect-trigger]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/automation.h#L38-L61
[issue-17437]: https://github.com/esphome/esphome/issues/17437
[keen-coffee-easystart]: https://github.com/Keen-coffee/home_assistant/blob/main/easyStart
[numeric-comparison]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/automation.h#L84-L93
[node-state]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/ble_client.h#L34-L37
[passkey-notification]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/automation.h#L73-L82
[passkey-request]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/automation.h#L63-L71
[reg-for-notify]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/esp32_ble_client/ble_client_base.cpp#L499-L514
[register-ble-node]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/ble_client.h#L61-L65
[release-services]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/esp32_ble_client/ble_client_base.cpp#L196-L205
[write-action]: https://github.com/esphome/esphome/blob/72f904dcfbb119c9454f440e313416f828f8ee35/esphome/components/ble_client/automation.h#L208
