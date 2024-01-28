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

_DEBUG = False
_DEBUG_LOG = True

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
_VENT_OPEN_TIME = 5 if _DEBUG else 180 # 3 mins
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
_OUTPUT_DOWN_ID = "sensor.heating_controller_1_output_temperature"
_OUTPUT_TOP_ID = "sensor.heating_controller_2_output_temperature"
_HEAT_PHAZE_DEFAULT = 20
_WAIT_PHAZE_DEFAULT = 0

_STATUS_STATE_NAME = "{}.{}".format(DOMAIN, _STATE_STATUS)
_STATUS_HEAT_PHAZE_NAME = "input_number.heat_phaze"
_STATUS_WAIT_PHAZE_NAME = "input_number.wait_phaze"
_STATUS_HEATING_TYPE_NAME = "input_select.heating_type"
_STATUS_TARGET_OUTPUT_NAME = "input_number.target_output"
_STATUS_TARGET_TEMPERATURE_DROP_NAME = "input_number.target_output_drop" 
_STATUS_UNTIL_NEXT_PHAZE_NAME = "{}.{}".format(DOMAIN, _STATE_UNTIL_NEXT_PHAZE)
_STATUS_NEXT_PHAZE_NAME = "{}.{}".format(DOMAIN, _STATE_NEXT_PHAZE)
_STATUS_UNTIL_NEXT_PHAZE_FORMATTED_NAME = "{}.{}".format(DOMAIN, _STATE_NEXT_PHAZE_FORMATTED)

_TARGET_MODE_VALVES = []

_UTC = pytz.UTC

_HYBRID_VALVE_NEW = "new"
_HYBRID_VALVE_OFF = "off"
_HYBRID_LOCK_UNTIL = _UTC.localize(datetime.utcnow())

def setup(hass, config):

    def skip_current_phaze(call):
        global _HYBRID_LOCK_UNTIL
        _LOGGER.info("Skipping current phaze in 5s, and reseting the hybrid lock")
        hass.states.set(_STATUS_UNTIL_NEXT_PHAZE_NAME, 5)
        _HYBRID_LOCK_UNTIL = _UTC.localize(datetime.utcnow())

    # services registration
    hass.services.async_register(DOMAIN, "skip_current_phaze", skip_current_phaze)

    # subscriptions
    async_track_state_change_event(hass, _VENT_ENTITIES, partial(pump_protection_check, hass))
    async_track_state_change_event(hass, _VENT_ENTITIES, partial(hybrid_vent_state_changed, hass))
    async_track_state_change_event(hass, [_OUTPUT_DOWN_ID, _OUTPUT_TOP_ID], partial(hybrid_temperature_changed, hass))

    hass.states.set(_STATUS_STATE_NAME, _STATE_STATUS_WAITING)
    queue_heat_phaze(hass, _VENT_OPEN_TIME + 10)

    turn_pump_off(hass)
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
    global _TARGET_MODE_VALVES
    _current_time = _UTC.localize(datetime.utcnow())
    _heat_type_state = hass.states.get(_STATUS_HEATING_TYPE_NAME)
    if not _heat_type_state or _heat_type_state.state == "Hybrid":
        """
        --- HYBRID IS FULLY ASYNC ---

        vent changed
        -> off -> HEAT(off) // already handled in pump protection
        -> on -> delay vent open time -> HEAT(new)

        HEAT
        -> if "off" and all closed -> OFF -> END
        -> elif "new" -> ON -> "lock for heat cycle" -> END
        -> else -> ON -> END

        temp changed
        -> if temp >= limit and not "locked" -> OFF -> trigger after wait cycle -> HEAT
        """
    elif _heat_type_state.state == "Target":
        open_valves = get_open_valves(hass)
        if open_valves == _TARGET_MODE_VALVES or len(open_valves) < len(_TARGET_MODE_VALVES):
            _TARGET_MODE_VALVES = open_valves
            output_temp_too_low = False
            target_temperature = (float)(hass.states.get(_STATUS_TARGET_OUTPUT_NAME).state)
            target_temperature_drop = (float)(hass.states.get(_STATUS_TARGET_TEMPERATURE_DROP_NAME).state)
            temperature_down = (float)(hass.states.get(_OUTPUT_DOWN_ID).state)
            temperature_top =  (float)(hass.states.get(_OUTPUT_TOP_ID).state)
            for vent_entity in _VENT_ENTITIES:
                _vent_states = hass.states.get(vent_entity)
                if _vent_states and _vent_states.state == STATE_ON:
                    if hass.states.get(_STATUS_STATE_NAME) == _STATE_STATUS_WAITING:
                        target_temperature = target_temperature_drop
                    if "down" in _vent_states.entity_id and temperature_down <= target_temperature:
                        output_temp_too_low = True
                    if "top" in _vent_states.entity_id and temperature_top <= target_temperature:
                        output_temp_too_low = True
            if output_temp_too_low and should_heat(hass):
                turn_pump_on(hass)
                hass.states.set(_STATUS_STATE_NAME, _STATE_STATUS_ON)
                queue_heat_phaze(hass, 300) # 5 mins
            else:
                turn_pump_off(hass)
                hass.states.set(_STATUS_STATE_NAME, _STATE_STATUS_WAITING)
                queue_heat_phaze(hass, 60)
        else:
            # new valve was opened
            _TARGET_MODE_VALVES = open_valves
            turn_pump_on(hass)
            hass.states.set(_STATUS_STATE_NAME, _STATE_STATUS_ON)
            queue_heat_phaze(hass, 900) # 15 mins
            _LOGGER.info("New valve was opened, heating for at least 15 min")
    elif _heat_type_state.state == "Continuous":
        if should_heat(hass):
            turn_pump_on(hass)
            hass.states.set(_STATUS_STATE_NAME, _STATE_STATUS_ON)
        else:
            turn_pump_off(hass)
            hass.states.set(_STATUS_STATE_NAME, _STATE_STATUS_WAITING)
        queue_heat_phaze(hass, 60)
    elif _heat_type_state.state == "Cycles":
        _next_phaze_status = hass.states.get(_STATUS_NEXT_PHAZE_NAME)
        if _next_phaze_status and _next_phaze_status.state == _STATE_PHAZE_HEAT and should_heat(hass):
            if queue_wait_phaze(hass):
                turn_pump_on(hass)
                hass.states.set(_STATUS_STATE_NAME, _STATE_STATUS_ON)
        else:
            delay_phaze(hass)


def is_hybrid(hass):
    _heat_type_state = hass.states.get(_STATUS_HEATING_TYPE_NAME)
    return not _heat_type_state or _heat_type_state.state == "Hybrid"


def hybrid_heat(hass, action):
    debug(hass, "[HYBRID] Hybrid heat: %s" % action)
    if not should_heat(hass):
        debug(hass, "[HYBRID] Hybrid heat: OFF")
        hybrid_off(hass)
    elif action == _HYBRID_VALVE_NEW:
        debug(hass, "[HYBRID] Hybrid heat: ON + LOCK")
        hybrid_on(hass)
        hybrid_set_lock(hass, "heat")
    else:
        debug(hass, "[HYBRID] Hybrid heat: ON")
        hybrid_on(hass)


def hybrid_off(hass):
    turn_pump_off(hass)
    hybrid_set_status(hass, _STATE_STATUS_WAITING)


def hybrid_on(hass):
    turn_pump_on(hass)
    hybrid_set_status(hass, _STATE_STATUS_ON)


def hybrid_set_lock(hass, type):
    global _HYBRID_LOCK_UNTIL
    duration = 0
    if type == "heat":
        duration = get_heat_duration(hass)
    else:
       duration = get_wait_duration(hass)
    _HYBRID_LOCK_UNTIL = _UTC.localize(datetime.utcnow()) + timedelta(minutes=duration)
    debug(hass, "[HYBRID] Lock was set for %sm" % duration)
    hybrid_set_status(hass, "", duration * 60)
    

def hybrid_set_status(hass, text="", seconds=0):
    if text:
        hass.states.set(_STATUS_STATE_NAME, text)
    if seconds:
        hass.states.set(_STATUS_UNTIL_NEXT_PHAZE_NAME, seconds)


def get_wait_duration(hass):
    _wait_phaze_time_state = hass.states.get(_STATUS_WAIT_PHAZE_NAME)
    return (float)(_wait_phaze_time_state.state)


def get_heat_duration(hass):
    _heat_phaze_time_state = hass.states.get(_STATUS_HEAT_PHAZE_NAME)
    return (float)(_heat_phaze_time_state.state)


def hybrid_is_locked(hass):
    global _HYBRID_LOCK_UNTIL
    _current_time = _UTC.localize(datetime.utcnow())
    if _current_time <= _HYBRID_LOCK_UNTIL:
        return True
    return False


def hybrid_is_temperature_high(hass):
    output_down_states = hass.states.get(_OUTPUT_DOWN_ID)
    output_top_states = hass.states.get(_OUTPUT_TOP_ID)
    target_output_states = hass.states.get(_STATUS_TARGET_OUTPUT_NAME)
    temperature_down = (float)(output_down_states.state) if output_down_states else 40
    temperature_top =  (float)(output_top_states.state) if output_down_states else 40
    target_temperature = (float)(target_output_states.state) if target_output_states else 0
    debug(hass, "[HYBRID] Temperature down: %s, top: %s, target: %s" % (temperature_down, temperature_top, target_temperature))
    for vent_entity in _VENT_ENTITIES:
        _vent_states = hass.states.get(vent_entity)
        if _vent_states and _vent_states.state == STATE_ON:
            if "down" in _vent_states.entity_id and temperature_down >= target_temperature:
                return True
            if "top" in _vent_states.entity_id and temperature_top >= target_temperature:
                return True
    return False


def hybrid_temperature_changed(hass, event):
   if is_hybrid(hass) and not hybrid_is_locked(hass):
        is_temperature_high = hybrid_is_temperature_high(hass)
        debug(hass, "[HYBRID] Is temperature high: %s" % is_temperature_high)
        if is_temperature_high:
            hybrid_off(hass)
            threading.Timer(get_wait_duration(hass) + 5, hybrid_on, [hass]).start()


def hybrid_vent_state_changed(hass, event):
    if is_hybrid(hass):
        debug(hass, "[HYBRID] Vent state changed %s" % event)
        if event.data["new_state"].state == STATE_ON and event.data["old_state"].state == STATE_OFF:
            debug(hass, "[HYBRID] Delay vent_open_time")
            threading.Timer(_VENT_OPEN_TIME + 5, hybrid_heat, [hass, _HYBRID_VALVE_NEW]).start()


def delay_phaze(hass, delay = 60):
    if queue_heat_phaze(hass, delay):
        turn_pump_off(hass)
        hass.states.set(_STATUS_STATE_NAME, _STATE_STATUS_WAITING)


def turn_pump_on(hass):
    _pump_state = hass.states.get(_PUMP_ENTITY_ID)
    if _pump_state:
        if _pump_state.state == STATE_OFF:
            if should_heat(hass):
                _LOGGER.info("Turning pump on")
                if not _DEBUG:
                    hass.services.call("switch", "turn_on", {
                        "entity_id": _PUMP_ENTITY_ID
                    })
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
            elif _vent_state == STATE_ON:
                debug(hass, "Vent not ready: %s" % _vent_states)

    return False


def get_open_valves(hass):
    _valves = []
    for vent_entity in _VENT_ENTITIES:
        _vent_states = hass.states.get(vent_entity)
        if _vent_states and _vent_states.state == STATE_ON:
            _valves.append(vent_entity)
    return sorted(_valves)


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


def debug(hass, message):
    if _DEBUG_LOG:
        _LOGGER.info(message)

