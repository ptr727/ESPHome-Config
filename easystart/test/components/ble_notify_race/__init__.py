"""Deliberately racy BLE client node, used to reproduce an ESPHome ble_client defect.

The node registers for notifications and reports ESTABLISHED before the registration
completes, which makes ble_client free the peer's GATT cache while the stack still needs
it. See ../../../ESPHOME-BLE-ISSUE.md. Nothing in the fleet should copy this pattern.
"""

# esphome is supplied by the ESPHome toolchain when it runs this codegen, not by the editor's
# Python environment, so Pylance/pyright cannot resolve these imports standalone.
# pyright: reportMissingImports=false

import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import ble_client, esp32_ble_tracker
from esphome.const import CONF_CHARACTERISTIC_UUID, CONF_ID, CONF_SERVICE_UUID

CODEOWNERS = ["@ptr727"]
DEPENDENCIES = ["ble_client"]

ble_notify_race_ns = cg.esphome_ns.namespace("ble_notify_race")
BleNotifyRace = ble_notify_race_ns.class_(
    "BleNotifyRace", cg.Component, ble_client.BLEClientNode
)

CONFIG_SCHEMA = (
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(BleNotifyRace),
            cv.Required(CONF_SERVICE_UUID): esp32_ble_tracker.bt_uuid,
            cv.Required(CONF_CHARACTERISTIC_UUID): esp32_ble_tracker.bt_uuid,
        }
    )
    .extend(cv.COMPONENT_SCHEMA)
    .extend(ble_client.BLE_CLIENT_SCHEMA)
)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await ble_client.register_ble_node(var, config)

    cg.add(var.set_service_uuid(config[CONF_SERVICE_UUID]))
    cg.add(var.set_char_uuid(config[CONF_CHARACTERISTIC_UUID]))
