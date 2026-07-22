#pragma once
//
// EasyStart / Micro-Air soft-starter -> ESPHome BLE client component.
//
// Reverse-engineered protocol: see ../../PROTOCOL.md. Transport is the Laird VSP service;
// we write the ASCII command {"Cmd": ReadLive} to the write characteristic and parse the
// little-endian binary frame that arrives as notifications on the notify characteristic.
//
// Status: validated on a flashed ESP32 (GL-S10 proxy, both modules); every decoded field matches
// the live frames. Logs each raw notification frame at DEBUG and the decoded values at INFO.
//
// Wiring into an existing bluetooth-proxy ESP32: keep your `bluetooth_proxy:` /
// `esp32_ble_tracker:` blocks; add a `ble_client:` for the module's MAC and this component.
// The ble_client active connection uses one of the ESP32's connection slots. See the reusable
// package templates/easystart.yaml and the example office-bluetooth-proxy.yaml.

#include "esphome/core/component.h"
#include "esphome/core/log.h"
#include "esphome/components/ble_client/ble_client.h"
#include "esphome/components/binary_sensor/binary_sensor.h"
#include "esphome/components/sensor/sensor.h"
#include "esphome/components/text_sensor/text_sensor.h"

#include <vector>
#include <cstring>

namespace esphome {
namespace easystart {

namespace espbt = esphome::esp32_ble_tracker;

static const char *const TAG = "easystart";

// Laird VSP service + characteristics (see PROTOCOL.md). Confirmed via nRF Connect:
// e1 = NOTIFY, e2 = WRITE / WRITE-NO-RESPONSE.
static const char *const SERVICE_UUID = "d973f2e0-b19e-11e2-9e96-0800200c9a66";
static const char *const NOTIFY_UUID = "d973f2e1-b19e-11e2-9e96-0800200c9a66";  // module -> host
static const char *const WRITE_UUID = "d973f2e2-b19e-11e2-9e96-0800200c9a66";  // host -> module

static const char *const CMD_READ_LIVE = "{\"Cmd\": ReadLive}";

// The live frame is 18 bytes; total-starts (u32) occupies the final offsets 0x0E-0x11.
static const size_t FRAME_MIN_LEN = 18;

// System-state / fault code table (byte [2]).
static const char *const STATE_TEXT[] = {
    "Normal",             // 0
    "Unexpctd Curr Flt",  // 1
    "Short Cycle Delay",  // 2
    "Pwr Intrrptn Fault",  // 3
    "Stall Fault",        // 4
    "Stuck SR Fault",     // 5
    "Open Ovrld Fault",   // 6
    "Overcurrent Fault",  // 7
    "Bad Wiring Fault",   // 8
    "Wrong Voltage Flt",  // 9
};

class EasyStart : public PollingComponent, public ble_client::BLEClientNode {
 public:
  // Setters wired from YAML.
  void set_current_sensor(sensor::Sensor *s) { this->current_sensor_ = s; }
  void set_power_sensor(sensor::Sensor *s) { this->power_sensor_ = s; }
  void set_line_voltage(float v) { this->line_voltage_ = v; }
  void set_power_factor(float pf) { this->power_factor_ = pf; }
  void set_frequency_sensor(sensor::Sensor *s) { this->frequency_sensor_ = s; }
  void set_peak_sensor(sensor::Sensor *s) { this->peak_sensor_ = s; }
  void set_scpt_sensor(sensor::Sensor *s) { this->scpt_sensor_ = s; }
  void set_total_starts_sensor(sensor::Sensor *s) { this->total_starts_sensor_ = s; }
  void set_total_faults_sensor(sensor::Sensor *s) { this->total_faults_sensor_ = s; }
  void set_learned_starts_sensor(sensor::Sensor *s) { this->learned_starts_sensor_ = s; }
  void set_running_sensor(binary_sensor::BinarySensor *s) { this->running_sensor_ = s; }
  void set_state_text_sensor(text_sensor::TextSensor *s) { this->state_text_sensor_ = s; }
  void set_current_threshold(float a) { this->current_threshold_ = a; }

  void update() override {
    // Poll: clear the receive buffer and request a fresh live frame.
    if (this->node_state != espbt::ClientState::ESTABLISHED)
      return;
    if (this->write_handle_ == 0) {
      ESP_LOGW(TAG, "write characteristic not resolved yet");
      return;
    }
    this->rx_buffer_.clear();
    this->parsed_this_poll_ = false;
    this->send_read_live_();
  }

  void gattc_event_handler(esp_gattc_cb_event_t event, esp_gatt_if_t gattc_if,
                           esp_ble_gattc_cb_param_t *param) override {
    switch (event) {
      case ESP_GATTC_OPEN_EVT: {
        if (param->open.status == ESP_GATT_OK)
          ESP_LOGI(TAG, "connected");
        break;
      }
      case ESP_GATTC_DISCONNECT_EVT: {
        this->write_handle_ = 0;
        this->notify_handle_ = 0;
        this->rx_buffer_.clear();
        // The module powers its BLE radio down when the compressor is off, so a disconnect
        // means the compressor is off. Mark running=false and the data stale/unavailable.
        this->publish_offline_();
        break;
      }
      case ESP_GATTC_SEARCH_CMPL_EVT: {
        // Resolve characteristic handles by UUID.
        auto *wr = this->parent()->get_characteristic(espbt::ESPBTUUID::from_raw(SERVICE_UUID),
                                                      espbt::ESPBTUUID::from_raw(WRITE_UUID));
        auto *nt = this->parent()->get_characteristic(espbt::ESPBTUUID::from_raw(SERVICE_UUID),
                                                      espbt::ESPBTUUID::from_raw(NOTIFY_UUID));
        if (wr == nullptr || nt == nullptr) {
          ESP_LOGE(TAG, "EasyStart VSP characteristics not found");
          break;
        }
        this->write_handle_ = wr->handle;
        this->notify_handle_ = nt->handle;
        // Subscribe to notifications (ESPHome writes the CCCD automatically).
        auto err = esp_ble_gattc_register_for_notify(gattc_if, this->parent()->get_remote_bda(),
                                                     this->notify_handle_);
        if (err != ESP_OK)
          ESP_LOGW(TAG, "register_for_notify failed, err=%d", err);
        this->node_state = espbt::ClientState::ESTABLISHED;
        // Connected + subscribed -> the module's radio is up -> the compressor is running.
        if (this->running_sensor_ != nullptr)
          this->running_sensor_->publish_state(true);
        ESP_LOGI(TAG, "handles resolved (write=%d notify=%d)", this->write_handle_,
                 this->notify_handle_);
        break;
      }
      case ESP_GATTC_NOTIFY_EVT: {
        if (param->notify.handle != this->notify_handle_)
          break;
        this->on_notify_(param->notify.value, param->notify.value_len);
        break;
      }
      default:
        break;
    }
  }

  float get_setup_priority() const override { return setup_priority::AFTER_BLUETOOTH; }

 protected:
  void send_read_live_() {
    auto err = esp_ble_gattc_write_char(this->parent()->get_gattc_if(),
                                        this->parent()->get_conn_id(), this->write_handle_,
                                        strlen(CMD_READ_LIVE), (uint8_t *) CMD_READ_LIVE,
                                        ESP_GATT_WRITE_TYPE_NO_RSP, ESP_GATT_AUTH_REQ_NONE);
    if (err != ESP_OK)
      ESP_LOGW(TAG, "ReadLive write failed, err=%d", err);
  }

  void on_notify_(const uint8_t *data, uint16_t len) {
    // A ReadLive poll yields two notifications: the binary live frame and an ASCII status
    // marker like {"Sts": Success}. Ignore the text one; decode the binary frame. At default
    // ATT MTU the frame arrives in one notification, but we still accumulate in case a small
    // MTU splits it. rx_buffer_ is cleared at the start of each poll in update().
    if (len > 0 && data[0] == '{') {
      ESP_LOGD(TAG, "status: %.*s", len, (const char *) data);
      return;
    }
    for (uint16_t i = 0; i < len; i++)
      this->rx_buffer_.push_back(data[i]);

    ESP_LOGD(TAG, "frame %u bytes, buffer=%s", len, format_hex_pretty(this->rx_buffer_).c_str());

    if (!this->parsed_this_poll_ && this->rx_buffer_.size() >= FRAME_MIN_LEN) {
      this->parse_live_frame_();
      this->parsed_this_poll_ = true;
    }
  }

  uint16_t le16_(size_t lo) const {
    return (uint16_t) this->rx_buffer_[lo] | ((uint16_t) this->rx_buffer_[lo + 1] << 8);
  }

  uint32_t le32_(size_t lo) const {
    return (uint32_t) this->rx_buffer_[lo] | ((uint32_t) this->rx_buffer_[lo + 1] << 8) |
           ((uint32_t) this->rx_buffer_[lo + 2] << 16) | ((uint32_t) this->rx_buffer_[lo + 3] << 24);
  }

  // Live frame layout (validated against the app decompile + live hardware, see PROTOCOL.md section 4):
  //   [2] state  [3] learned  [4..5] current/10 A  [6..7] period (500000/p = Hz)
  //   [8..9] peak/10 A  [10..11] scpt  [12..13] faults  [14..17] total starts (u32)
  void parse_live_frame_() {
    if (this->rx_buffer_.size() < FRAME_MIN_LEN) {
      ESP_LOGW(TAG, "live frame too short (%u bytes)", (unsigned) this->rx_buffer_.size());
      return;
    }

    uint8_t state = this->rx_buffer_[2];
    uint8_t learned_starts = this->rx_buffer_[3];
    float current_a = this->le16_(4) / 10.0f;
    uint16_t period = this->le16_(6);
    float freq_hz = period ? 500000.0f / period : 0.0f;
    float peak_a = this->le16_(8) / 10.0f;
    uint16_t scpt_delay = this->le16_(10);
    uint16_t total_faults = this->le16_(12);
    uint32_t total_starts = this->le32_(14);

    const char *state_str = (state <= 9) ? STATE_TEXT[state] : "Not Defined";

    ESP_LOGI(TAG, "state=%s current=%.1fA freq=%.2fHz peak=%.1fA starts=%u faults=%u", state_str,
             current_a, freq_hz, peak_a, total_starts, total_faults);

    // "running" is driven by BLE connection state (radio only on while compressor runs), not by
    // this frame - see publish_offline_() and the OPEN/DISCONNECT handlers.
    if (this->current_sensor_ != nullptr)
      this->current_sensor_->publish_state(current_a);
    // Estimated power: the module reports single-leg current only (no voltage), so this is
    // current * line_voltage * power_factor - an estimate, not a measured value.
    if (this->power_sensor_ != nullptr)
      this->power_sensor_->publish_state(current_a * this->line_voltage_ * this->power_factor_);
    if (this->frequency_sensor_ != nullptr)
      this->frequency_sensor_->publish_state(freq_hz);
    if (this->peak_sensor_ != nullptr)
      this->peak_sensor_->publish_state(peak_a);
    if (this->scpt_sensor_ != nullptr)
      this->scpt_sensor_->publish_state(scpt_delay);
    if (this->total_starts_sensor_ != nullptr)
      this->total_starts_sensor_->publish_state(total_starts);
    if (this->total_faults_sensor_ != nullptr)
      this->total_faults_sensor_->publish_state(total_faults);
    if (this->learned_starts_sensor_ != nullptr)
      this->learned_starts_sensor_->publish_state(learned_starts);
    if (this->state_text_sensor_ != nullptr)
      this->state_text_sensor_->publish_state(state_str);
  }

  // Compressor off / module radio down: report not-running and blank the live telemetry.
  void publish_offline_() {
    if (this->running_sensor_ != nullptr)
      this->running_sensor_->publish_state(false);
    if (this->current_sensor_ != nullptr)
      this->current_sensor_->publish_state(NAN);
    if (this->power_sensor_ != nullptr)
      this->power_sensor_->publish_state(NAN);
    if (this->frequency_sensor_ != nullptr)
      this->frequency_sensor_->publish_state(NAN);
    if (this->peak_sensor_ != nullptr)
      this->peak_sensor_->publish_state(NAN);
    if (this->state_text_sensor_ != nullptr)
      this->state_text_sensor_->publish_state("Off");
  }

  sensor::Sensor *current_sensor_{nullptr};
  sensor::Sensor *power_sensor_{nullptr};
  float line_voltage_{240.0f};
  float power_factor_{1.0f};
  sensor::Sensor *frequency_sensor_{nullptr};
  sensor::Sensor *peak_sensor_{nullptr};
  sensor::Sensor *scpt_sensor_{nullptr};
  sensor::Sensor *total_starts_sensor_{nullptr};
  sensor::Sensor *total_faults_sensor_{nullptr};
  sensor::Sensor *learned_starts_sensor_{nullptr};
  binary_sensor::BinarySensor *running_sensor_{nullptr};
  text_sensor::TextSensor *state_text_sensor_{nullptr};

  float current_threshold_{0.5f};
  bool parsed_this_poll_{false};
  uint16_t write_handle_{0};
  uint16_t notify_handle_{0};
  std::vector<uint8_t> rx_buffer_;
};

}  // namespace easystart
}  // namespace esphome
