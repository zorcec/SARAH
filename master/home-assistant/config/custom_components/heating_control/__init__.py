import logging
import json
import threading
import pytz

from datetime import datetime, timedelta
from homeassistant import config_entries, core
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import STATE_OFF, STATE_ON

DOMAIN = "heating_control"
CONF_HEATING_CYCLE = "heating_cycle"
CONF_HEAT_REQUEST_NAME = "request_name"
CONF_HEAT_REQUEST_STATE = "request_state"

STATE_HEATING_REQUESTS = "heating_requests"

_LOGGER = logging.getLogger(__name__)
_VENT_OPEN_TIME = 5 # TODO Should be corrected later
_VENT_ENTITIES = ["switch.tasmota_dc4f2255da78_switch_relay_1"]

_UTC = pytz.UTC

# TODO pump protection
# if all vents are getting closed, turn off the pump
# subscribe to all the vents states updates, and if changed, recheck should_heat() and turn off if needed

async def async_setup_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    _LOGGER.info("Heating control is initialized")
    heating_cycle(hass, entry.data[CONF_HEATING_CYCLE])
    return True

async def async_unload_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    _LOGGER.warning("Heating control is unloaded")
    return True

def heating_cycle(hass, heating_cycle_time, heatingUp = True):

    threading.Timer(heating_cycle_time, heating_cycle, [hass, heating_cycle_time, not heatingUp]).start()

    if heatingUp and should_heat(hass):
        heatingUpCycle()
    else:
        waitingCycle()

def heatingUpCycle():
    _LOGGER.info("Turning pump on")

def waitingCycle():
    _LOGGER.info("Turning pump off and waiting")

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
