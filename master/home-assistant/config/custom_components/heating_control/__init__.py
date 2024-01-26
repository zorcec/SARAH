import logging
import json
import threading
import pytz
import time

from functools import partial
from datetime import datetime, timedelta
from homeassistant import config_entries, core
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import STATE_OFF, STATE_ON

DOMAIN = "heating_control"
CONF_HEATING_PHAZE = "heating_phaze"
CONF_WAITING_PHAZE = "waiting_phaze"

ATTR_HEATING_OVERRIDE_VALUE = "value"

_STATE_STATUS = "status"
_STATE_UNTIL_NEXT_PHAZE = "until_next_phaze"
_STATE_NEXT_PHAZE = "next_phaze"
_STATE_NEXT_PHAZE_FORMATTED = "next_phaze_formatted"

_STATE_STATUS_ON = "on"
_STATE_STATUS_WAITING = "waiting"
_STATE_STATUS_OFF_PROTECTION = "waiting"
_STATE_STATUS_OVERRIDE = "override"

_STATE_PHAZE_WAIT = "wait"
_STATE_PHAZE_HEAT = "heat"

_LOGGER = logging.getLogger(__name__)
_VENT_OPEN_TIME = 0#180 # 3 mins
_VENT_ENTITIES = [
    "switch.down_backup_vent",
    "switch.down_hallway_vent",
    "switch.down_kitchen_vent",
    "switch.down_toilet_vent",
    "switch.top_bathroom_valve",
    "switch.top_bedroom_valve",
    "switch.top_kid_valve",
    "switch.top_livingroom_valve",
    "switch.top_wc_valve"
    ]
_PUMP_ENTITY_ID = "switch.heating_pump"
_HEAT_PHAZE_DEFAULT = 20
_WAIT_PHAZE_DEFAULT = 0

_STATUS_STATE_NAME = "{}.{}".format(DOMAIN, _STATE_STATUS)
_STATUS_HEAT_PHAZE_NAME = "input_number.heat_phaze"
_STATUS_WAIT_PHAZE_NAME = "input_number.wait_phaze"
_STATUS_HEATING_TYPE_NAME = "input_select.heating_type"
_STATUS_TARGET_OUTPUT_NAME = "input_number.target_output"
_STATUS_UNTIL_NEXT_PHAZE_NAME = "{}.{}".format(DOMAIN, _STATE_UNTIL_NEXT_PHAZE)
_STATUS_NEXT_PHAZE_NAME = "{}.{}".format(DOMAIN, _STATE_NEXT_PHAZE)
_STATUS_UNTIL_NEXT_PHAZE_FORMATTED_NAME = "{}.{}".format(DOMAIN, _STATE_NEXT_PHAZE_FORMATTED)

_UTC = pytz.UTC

def setup(hass, config):

    def skip_current_phaze(call):
        _LOGGER.info("Skipping current phaze in 5s")
        hass.states.set(_STATUS_UNTIL_NEXT_PHAZE_NAME, 5)

    # services registration
    hass.services.async_register(DOMAIN, "skip_current_phaze", skip_current_phaze)

    # subscriptions
    async_track_state_change_event(hass, _VENT_ENTITIES, partial(pump_protection_check, hass))

    # INITIAL PHAZE TIMES
    # TODO create "input_number.heat_phaze" and "input_number.wait_phaze" by this integration
    # _heat_phaze_time_state = hass.states.get(_STATUS_HEAT_PHAZE_NAME)
    # if not _heat_phaze_time_state or not _heat_phaze_time_state.state:
    #     hass.states.set(_STATUS_HEAT_PHAZE_NAME, _HEAT_PHAZE_DEFAULT)
    
    # _wait_phaze_time_state = hass.states.get(_STATUS_WAIT_PHAZE_NAME)
    # if not _wait_phaze_time_state or not _wait_phaze_time_state.state:
    #     hass.states.set(_STATUS_WAIT_PHAZE_NAME, _WAIT_PHAZE_DEFAULT)

    hass.states.set(_STATUS_STATE_NAME, _STATE_STATUS_WAITING)
    turn_pump_off(hass)
    queue_heat_phaze(hass, _VENT_OPEN_TIME + 10)

    tick(hass)

    _LOGGER.info("Heating control is initialized")

    return True


async def async_setup_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry):
    """Config flow"""
    return True


async def async_unload_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry):
    _LOGGER.warning("Heating control is unloaded")
    return True


def start_next_phaze(hass):
    _heat_type_state = hass.states.get(_STATUS_HEATING_TYPE_NAME)
    if not _heat_type_state or _heat_type_state.state == "Target":
        output_temp_too_low = False
        target_temperature = (float)(hass.states.get(_STATUS_TARGET_OUTPUT_NAME).state)
        temperature_down = (float)(hass.states.get("sensor.heating_controller_1_output_temperature").state)
        temperature_top =  (float)(hass.states.get("sensor.heating_controller_2_output_temperature").state)
        for vent_entity in _VENT_ENTITIES:
            _vent_states = hass.states.get(vent_entity)
            if _vent_states and _vent_states.state == STATE_ON:
                if "down" in _vent_states.entity_id and temperature_down <= target_temperature:
                    output_temp_too_low = True
                if "top" in _vent_states.entity_id and temperature_top <= target_temperature:
                    output_temp_too_low = True
        if output_temp_too_low:
            _LOGGER.info("Output temp. is too low")
            turn_pump_on(hass)
            hass.states.set(_STATUS_STATE_NAME, _STATE_STATUS_ON)
        else:
            _LOGGER.info("Heating is not needed")
            turn_pump_off(hass)
            hass.states.set(_STATUS_STATE_NAME, _STATE_STATUS_WAITING)
        queue_heat_phaze(hass, 60)
    elif _heat_type_state.state == "Continuous":
        if should_heat(hass) and queue_heat_phaze(hass, _until_heating):
            turn_pump_on(hass)
            hass.states.set(_STATUS_STATE_NAME, _STATE_STATUS_ON)
        else:
            delay_phaze(hass, 60)
    elif _heat_type_state.state == "Cycles":
        _next_phaze_status = hass.states.get(_STATUS_NEXT_PHAZE_NAME)
        if _next_phaze_status and _next_phaze_status.state == _STATE_PHAZE_HEAT and should_heat(hass):
            if queue_wait_phaze(hass):
                turn_pump_on(hass)
                hass.states.set(_STATUS_STATE_NAME, _STATE_STATUS_ON)
        else:
            delay_phaze(hass, 60)


def delay_phaze(hass, delay = 60):
    _until_heating = None if should_heat(hass) else delay
    if queue_heat_phaze(hass, _until_heating):
        turn_pump_off(hass)
        hass.states.set(_STATUS_STATE_NAME, _STATE_STATUS_WAITING)


def turn_pump_on(hass):
    _pump_state = hass.states.get(_PUMP_ENTITY_ID)
    if _pump_state:
        if _pump_state.state == STATE_OFF:
            if should_heat(hass):
                _LOGGER.info("Turning pump on")
                hass.services.call("switch", "turn_on", {
                    "entity_id": _PUMP_ENTITY_ID
                })
        else:
            _LOGGER.info("Pump is already on, ignoring")
    else:
        _LOGGER.info("Pump state is not known, ignoring")


def turn_pump_off(hass):
    _pump_state = hass.states.get(_PUMP_ENTITY_ID)
    if _pump_state:
        if _pump_state.state == STATE_ON:
            _LOGGER.info("Turning pump off and waiting")
            hass.services.call("switch", "turn_off", {
                "entity_id": _PUMP_ENTITY_ID
            })
        else:
            _LOGGER.info("Pump is already off, ignoring")
    else:
        _LOGGER.info("Pump state is not known, ignoring")


def should_heat(hass):
    """ Checks if we should start the heating pump; Vent open time is considered in it"""
    for vent_entity in _VENT_ENTITIES:
        _vent_states = hass.states.get(vent_entity)
        if _vent_states:
            _vent_state = _vent_states.state
            _vent_state_changed = _vent_states.last_changed
            # it is assumed HA saves state with the UTC timestamp
            _current_time = _UTC.localize(datetime.utcnow())
            # If vent is still not ready (check vent open time); it will be ignored
            if _vent_state == STATE_ON and _current_time >= _vent_state_changed + timedelta(seconds=_VENT_OPEN_TIME):
                _LOGGER.info("Vent is ready: {}, changed at {}".format(vent_entity, _vent_state_changed))
                return True

    return False


def pump_protection_check(hass, event):
    """Called when vent state is changed"""
    if not should_heat(hass):
        _LOGGER.info("All vents are in closed state, turning pump off (pump protection)")
        turn_pump_off(hass)
        hass.states.set(_STATUS_STATE_NAME, _STATE_STATUS_OFF_PROTECTION)
        queue_heat_phaze(hass, 60)


def queue_wait_phaze(hass, seconds=None):
    _heat_phaze_time = _HEAT_PHAZE_DEFAULT
    if not seconds:
        _heat_phaze_time_state = hass.states.get(_STATUS_HEAT_PHAZE_NAME)
        _heat_phaze_time = (float)(_heat_phaze_time_state.state)

    _next_phaze_time_seconds = seconds or _heat_phaze_time * 60
    hass.states.set(_STATUS_NEXT_PHAZE_NAME, _STATE_PHAZE_WAIT)
    hass.states.set(_STATUS_UNTIL_NEXT_PHAZE_NAME, _next_phaze_time_seconds)

    return _next_phaze_time_seconds > 0


def queue_heat_phaze(hass, seconds=None):
    _wait_phaze_time = _WAIT_PHAZE_DEFAULT
    if not seconds:
        _wait_phaze_time_state = hass.states.get(_STATUS_WAIT_PHAZE_NAME)
        _wait_phaze_time = (float)(_wait_phaze_time_state.state)

    _next_phaze_time_seconds = seconds or _wait_phaze_time * 60
    hass.states.set(_STATUS_NEXT_PHAZE_NAME, _STATE_PHAZE_HEAT)
    hass.states.set(_STATUS_UNTIL_NEXT_PHAZE_NAME, _next_phaze_time_seconds)

    return _next_phaze_time_seconds > 0


def tick(hass):
    """Called every second"""
    _until_next_phaze_state = hass.states.get(_STATUS_UNTIL_NEXT_PHAZE_NAME)
    if _until_next_phaze_state and _until_next_phaze_state.state:
        _time_left = (float)(_until_next_phaze_state.state) - 1
        if _time_left > 0:
            hass.states.set(_STATUS_UNTIL_NEXT_PHAZE_NAME, _time_left)
            hass.states.set(_STATUS_UNTIL_NEXT_PHAZE_FORMATTED_NAME, timedelta(seconds=_time_left))
        else:
            start_next_phaze(hass)

    threading.Timer(1, tick, [hass]).start()