#pragma once
// This node reports ESTABLISHED while its own notify registration is still outstanding, on purpose.
// That is the BLEClientNode contract violation that reproduces the ble_client GATT-cache race.

#include "esphome/core/component.h"
#include "esphome/core/log.h"
#include "esphome/components/ble_client/ble_client.h"

namespace esphome {
namespace ble_notify_race {

namespace espbt = esphome::esp32_ble_tracker;

static const char *const TAG = "ble_notify_race";

class BleNotifyRace : public Component, public ble_client::BLEClientNode {
 public:
  void set_service_uuid(const char *uuid) { this->service_uuid_ = uuid; }
  void set_char_uuid(const char *uuid) { this->char_uuid_ = uuid; }

  void dump_config() override {
    ESP_LOGCONFIG(TAG, "BLE Notify Race:");
    ESP_LOGCONFIG(TAG, "  Service UUID: %s", this->service_uuid_);
    ESP_LOGCONFIG(TAG, "  Characteristic UUID: %s", this->char_uuid_);
  }

  float get_setup_priority() const override { return setup_priority::AFTER_BLUETOOTH; }

  void gattc_event_handler(esp_gattc_cb_event_t event, esp_gatt_if_t gattc_if,
                           esp_ble_gattc_cb_param_t *param) override {
    switch (event) {
      case ESP_GATTC_DISCONNECT_EVT: {
        this->char_handle_ = 0;
        this->notify_count_ = 0;
        break;
      }
      case ESP_GATTC_SEARCH_CMPL_EVT: {
        auto *chr = this->parent()->get_characteristic(espbt::ESPBTUUID::from_raw(this->service_uuid_),
                                                       espbt::ESPBTUUID::from_raw(this->char_uuid_));
        if (chr == nullptr) {
          ESP_LOGE(TAG, "characteristic not found");
          break;
        }
        this->char_handle_ = chr->handle;
        auto err = esp_ble_gattc_register_for_notify(gattc_if, this->parent()->get_remote_bda(), this->char_handle_);
        if (err != ESP_OK) {
          ESP_LOGW(TAG, "register_for_notify failed, err=%d", err);
          break;
        }
        // The violation, the registration is still in flight.
        // Reporting ESTABLISHED here lets ble_client free the cache the CCCD lookup needs.
        ESP_LOGI(TAG, "registered for notify on handle %d, reporting ESTABLISHED early", this->char_handle_);
        this->node_state = espbt::ClientState::ESTABLISHED;
        break;
      }
      case ESP_GATTC_REG_FOR_NOTIFY_EVT: {
        // A null lookup here means ble_client already released the services.
        auto *chr = this->parent()->get_characteristic(espbt::ESPBTUUID::from_raw(this->service_uuid_),
                                                       espbt::ESPBTUUID::from_raw(this->char_uuid_));
        ESP_LOGI(TAG, "REG_FOR_NOTIFY handle %d, status %d, client state %d, node state %d, services %s",
                 param->reg_for_notify.handle, param->reg_for_notify.status, (int) this->parent()->state(),
                 (int) this->node_state, chr == nullptr ? "released" : "held");
        break;
      }
      case ESP_GATTC_NOTIFY_EVT: {
        if (param->notify.handle != this->char_handle_)
          break;
        this->notify_count_++;
        ESP_LOGI(TAG, "notification %" PRIu32 ", %d bytes", this->notify_count_, param->notify.value_len);
        break;
      }
      default:
        break;
    }
  }

 protected:
  const char *service_uuid_{""};
  const char *char_uuid_{""};
  uint16_t char_handle_{0};
  uint32_t notify_count_{0};
};

}  // namespace ble_notify_race
}  // namespace esphome
