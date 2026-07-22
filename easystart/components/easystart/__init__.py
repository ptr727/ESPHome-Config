"""EasyStart (Micro-Air soft-starter) BLE client component for ESPHome.

One instance per module: connects to the Laird VSP service, polls {"Cmd": ReadLive}, and
publishes the decoded live frame. Configure as a single mapping or a list (one per module).
See ../../PROTOCOL.md.
"""

# esphome is supplied by the ESPHome toolchain when it runs this codegen, not by the editor's
# Python environment, so Pylance/pyright cannot resolve these imports standalone.
# pyright: reportMissingImports=false

import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import ble_client, binary_sensor, sensor, text_sensor
from esphome.const import (
    CONF_ID,
    CONF_FREQUENCY,
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_DURATION,
    DEVICE_CLASS_FREQUENCY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_RUNNING,
    STATE_CLASS_MEASUREMENT,
    STATE_CLASS_TOTAL_INCREASING,
    UNIT_AMPERE,
    UNIT_HERTZ,
    UNIT_SECOND,
    UNIT_WATT,
    UNIT_EMPTY,
)

CODEOWNERS = ["@ptr727"]
DEPENDENCIES = ["ble_client"]
AUTO_LOAD = ["binary_sensor", "sensor", "text_sensor"]

CONF_CURRENT = "current"
CONF_POWER = "power"
CONF_LINE_VOLTAGE = "line_voltage"
CONF_POWER_FACTOR = "power_factor"
CONF_PEAK = "last_start_peak"
CONF_SCPT_DELAY = "scpt_delay"
CONF_RUNNING = "running"
CONF_SYSTEM_STATE = "system_state"
CONF_TOTAL_STARTS = "total_starts"
CONF_TOTAL_FAULTS = "total_faults"
CONF_LEARNED_STARTS = "learned_starts"
CONF_CURRENT_THRESHOLD = "current_threshold"

easystart_ns = cg.esphome_ns.namespace("easystart")
EasyStart = easystart_ns.class_(
    "EasyStart", cg.PollingComponent, ble_client.BLEClientNode
)

_INSTANCE_SCHEMA = (
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(EasyStart),
            cv.Optional(CONF_CURRENT_THRESHOLD, default=0.5): cv.positive_float,
            # Estimated-power inputs: the module reports single-leg current only, so power is
            # current * line_voltage * power_factor (defaults: US 240 V split-phase, PF 1.0).
            cv.Optional(CONF_LINE_VOLTAGE, default=240.0): cv.positive_float,
            cv.Optional(CONF_POWER_FACTOR, default=1.0): cv.positive_float,
            cv.Optional(CONF_CURRENT): sensor.sensor_schema(
                unit_of_measurement=UNIT_AMPERE,
                accuracy_decimals=1,
                device_class=DEVICE_CLASS_CURRENT,
                state_class=STATE_CLASS_MEASUREMENT,
            ),
            cv.Optional(CONF_POWER): sensor.sensor_schema(
                unit_of_measurement=UNIT_WATT,
                accuracy_decimals=0,
                device_class=DEVICE_CLASS_POWER,
                state_class=STATE_CLASS_MEASUREMENT,
            ),
            cv.Optional(CONF_FREQUENCY): sensor.sensor_schema(
                unit_of_measurement=UNIT_HERTZ,
                accuracy_decimals=2,
                device_class=DEVICE_CLASS_FREQUENCY,
                state_class=STATE_CLASS_MEASUREMENT,
            ),
            cv.Optional(CONF_PEAK): sensor.sensor_schema(
                unit_of_measurement=UNIT_AMPERE,
                accuracy_decimals=1,
                device_class=DEVICE_CLASS_CURRENT,
                state_class=STATE_CLASS_MEASUREMENT,
            ),
            cv.Optional(CONF_SCPT_DELAY): sensor.sensor_schema(
                unit_of_measurement=UNIT_SECOND,
                accuracy_decimals=0,
                device_class=DEVICE_CLASS_DURATION,
                state_class=STATE_CLASS_MEASUREMENT,
            ),
            cv.Optional(CONF_TOTAL_STARTS): sensor.sensor_schema(
                unit_of_measurement=UNIT_EMPTY,
                accuracy_decimals=0,
                state_class=STATE_CLASS_TOTAL_INCREASING,
            ),
            cv.Optional(CONF_TOTAL_FAULTS): sensor.sensor_schema(
                unit_of_measurement=UNIT_EMPTY,
                accuracy_decimals=0,
                state_class=STATE_CLASS_TOTAL_INCREASING,
            ),
            cv.Optional(CONF_LEARNED_STARTS): sensor.sensor_schema(
                unit_of_measurement=UNIT_EMPTY,
                accuracy_decimals=0,
                state_class=STATE_CLASS_MEASUREMENT,
            ),
            cv.Optional(CONF_RUNNING): binary_sensor.binary_sensor_schema(
                device_class=DEVICE_CLASS_RUNNING,
            ),
            cv.Optional(CONF_SYSTEM_STATE): text_sensor.text_sensor_schema(),
        }
    )
    .extend(cv.polling_component_schema("2s"))
    .extend(ble_client.BLE_CLIENT_SCHEMA)
)

# Allow one instance (mapping) or several (list) - one per EasyStart module.
CONFIG_SCHEMA = cv.ensure_list(_INSTANCE_SCHEMA)


async def to_code(config):
    for conf in config:
        await _instance_to_code(conf)


async def _instance_to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await ble_client.register_ble_node(var, config)

    cg.add(var.set_current_threshold(config[CONF_CURRENT_THRESHOLD]))
    cg.add(var.set_line_voltage(config[CONF_LINE_VOLTAGE]))
    cg.add(var.set_power_factor(config[CONF_POWER_FACTOR]))

    if CONF_CURRENT in config:
        cg.add(var.set_current_sensor(await sensor.new_sensor(config[CONF_CURRENT])))
    if CONF_POWER in config:
        cg.add(var.set_power_sensor(await sensor.new_sensor(config[CONF_POWER])))
    if CONF_FREQUENCY in config:
        cg.add(var.set_frequency_sensor(await sensor.new_sensor(config[CONF_FREQUENCY])))
    if CONF_PEAK in config:
        cg.add(var.set_peak_sensor(await sensor.new_sensor(config[CONF_PEAK])))
    if CONF_SCPT_DELAY in config:
        cg.add(var.set_scpt_sensor(await sensor.new_sensor(config[CONF_SCPT_DELAY])))
    if CONF_TOTAL_STARTS in config:
        cg.add(
            var.set_total_starts_sensor(
                await sensor.new_sensor(config[CONF_TOTAL_STARTS])
            )
        )
    if CONF_TOTAL_FAULTS in config:
        cg.add(
            var.set_total_faults_sensor(
                await sensor.new_sensor(config[CONF_TOTAL_FAULTS])
            )
        )
    if CONF_LEARNED_STARTS in config:
        cg.add(
            var.set_learned_starts_sensor(
                await sensor.new_sensor(config[CONF_LEARNED_STARTS])
            )
        )
    if CONF_RUNNING in config:
        cg.add(
            var.set_running_sensor(
                await binary_sensor.new_binary_sensor(config[CONF_RUNNING])
            )
        )
    if CONF_SYSTEM_STATE in config:
        cg.add(
            var.set_state_text_sensor(
                await text_sensor.new_text_sensor(config[CONF_SYSTEM_STATE])
            )
        )
