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

_STATE_HEATING_OVERRIDE = "heating_override"

_LOGGER = logging.getLogger(__name__)
_VENT_OPEN_TIME = 5 # TODO Should be corrected later
_VENT_ENTITIES = ["switch.tasmota_dc4f2255da78_switch_relay_1"]
_PUMP_ENTITY_ID = "switch.tasmota"
_HEAT_PHAZE_OVERRIDE = 1200 # 20min, if not specified, the real config is taken
_WAIT_PHAZE_OVERRIDE = 900 # 15min, if not specified, the real config is taken

_OVERRIDE_STATE_NAME = "{}.{}".format(DOMAIN, _STATE_HEATING_OVERRIDE)

_UTC = pytz.UTC

def setup(hass, config):

    def heating_override_toggle(call):
        _heating_override = STATE_OFF
        override_states = hass.states.get(_OVERRIDE_STATE_NAME)
        if override_states and override_states.state == STATE_ON:
            _heating_override = STATE_OFF
        else:
            _heating_override = STATE_ON
        hass.states.set(_OVERRIDE_STATE_NAME, _heating_override)
        _LOGGER.info("Heating override was set to: {}".format(_heating_override))

    hass.services.register(DOMAIN, "heating_override_toggle", heating_override_toggle)

    return True


async def async_setup_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry):
    _LOGGER.info("Heating control is initialized")
    async_track_state_change_event(hass, _VENT_ENTITIES, partial(pump_protection_check, hass))
    heating_cycle(hass, _HEAT_PHAZE_OVERRIDE or entry.data[CONF_HEATING_PHAZE], _WAIT_PHAZE_OVERRIDE or entry.data[CONF_WAITING_PHAZE])
    return True


async def async_unload_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry):
    _LOGGER.warning("Heating control is unloaded")
    return True


def heating_cycle(hass, heating_phaze_time, waiting_phaze_time, heatingUp = True):

    _override_states = hass.states.get(_OVERRIDE_STATE_NAME)
    if _override_states and _override_states.state == STATE_ON:
        _LOGGER.info("Heating override enabled, do not chage the pump state (recheck in 60s)")
        threading.Timer(60, heating_cycle, [hass, heating_phaze_time, waiting_phaze_time, not heatingUp]).start()
    elif heatingUp and should_heat(hass):
        threading.Timer(heating_phaze_time, heating_cycle, [hass, heating_phaze_time, waiting_phaze_time, not heatingUp]).start()
        heatingUpCycle(hass)
    else:
        threading.Timer(waiting_phaze_time, heating_cycle, [hass, heating_phaze_time, waiting_phaze_time, not heatingUp]).start()
        waitingCycle(hass)


def heatingUpCycle(hass):
    _pump_state = hass.states.get(_PUMP_ENTITY_ID)
    if _pump_state:
        if _pump_state.state == STATE_OFF:
            _LOGGER.info("Turning pump on")
            hass.services.call("switch", "turn_on", {
                "entity_id": _PUMP_ENTITY_ID
            })
        else:
            _LOGGER.info("Pump is already on, ignoring")
    else:
        _LOGGER.info("Pump state is not known, ignoring")


def waitingCycle(hass):
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
            _current_time = _UTC.localize(datetime.now())
            # If went is still not ready (check vent open time); it will be ignored
            if _vent_state == STATE_ON and _current_time >= _vent_state_changed + timedelta(seconds=_VENT_OPEN_TIME):
                return True

    return False


def pump_protection_check(hass, event):
    """Called when vent state is changed"""
    if not should_heat(hass):
        _LOGGER.info("All vents are in closed state, turning pump off (pump protection)")
        waitingCycle(hass)
