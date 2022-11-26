import logging
import json
import threading

from datetime import datetime, timedelta
from homeassistant import config_entries, core

DOMAIN = "heating_control"
CONF_HEATING_CYCLE = "heating_cycle"
CONF_HEAT_REQUEST_NAME = "request_name"
CONF_HEAT_REQUEST_STATE = "request_state"

STATE_HEATING_REQUESTS = "heating_requests"

_LOGGER = logging.getLogger(__name__)
_PUMP_DELAY = 5 # Should be ~60

_requests = {}

async def async_setup_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    _LOGGER.info("Heating control is initialized")
    heating_cycle(entry.data[CONF_HEATING_CYCLE])

    #hass.services.register(DOMAIN, "heat_request", handle_heat_request)

    return True

async def async_unload_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    _LOGGER.warning("Heating control is unloaded")
    return True

def heating_cycle(heating_cycle_time):

    threading.Timer(heating_cycle_time, heating_cycle, [heating_cycle_time]).start()

    if should_heat():
        heatingUpCycle()
    else:
        waitingCycle()

def heatingUpCycle():
    _LOGGER.info("Waiting for pump delay: {}".format(_PUMP_DELAY))
    time.sleep(_PUMP_DELAY)
    _LOGGER.info("Turning pump on")

def waitingCycle():
    _LOGGER.info("Turning pump off and waiting")

def should_heat():
    for _request in _requests:
        if _request + timedelta(seconds=_PUMP_DELAY) < datetime.now():
            return True
        else:
            return _PUMP_DELAY - (datetime.now() - _request)
    return False

def handle_heat_request(call):
    """Handle the service call."""
    _name = call.data.get(CONF_HEAT_REQUEST_NAME, None)
    _state = call.data.get(CONF_HEAT_REQUEST_STATE, False)
    if _state:
        _requests[_name] = datetime.now()
    else:
        _requests.pop(_name)
    hass.states.set(STATE_HEATING_REQUESTS, _requests)
