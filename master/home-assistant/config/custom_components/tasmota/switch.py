import voluptuous as vol
import logging
import asyncio

import homeassistant.helpers.config_validation as cv

from homeassistant.const import ( 
    CONF_PLATFORM, 
    CONF_NAME,
    CONF_BRIGHTNESS,
    CONF_COLOR_TEMP,
    CONF_DEVICE,
    CONF_EFFECT,
    CONF_HS,
    CONF_NAME,
    CONF_OPTIMISTIC,
    CONF_PAYLOAD_OFF,
    CONF_PAYLOAD_ON,
    CONF_RGB,
    CONF_STATE,
    CONF_VALUE_TEMPLATE,
    CONF_WHITE_VALUE,
    CONF_XY
)

from . import motion
# from . import sensor

from ..sarah import (
    CONF_INTERNAL_ID,
    CONF_TYPE,
    CONF_AVAILABILITY_TOPIC,
    CONF_COMMAND_TOPIC,
    CONF_QOS,
    CONF_RETAIN,
    CONF_STATE_TOPIC,
    CONF_PAYLOAD_NOT_AVAILABLE,
    CONF_PAYLOAD_AVAILABLE
)

from homeassistant.components.mqtt.switch import ( 
    MqttSwitch
)

_TYPE_COMMON = "common"

_TYPES = {
    _TYPE_COMMON: {
        CONF_OPTIMISTIC: False,
        CONF_RETAIN: False,
        CONF_QOS: 1,
        CONF_COMMAND_TOPIC: "cmnd/{internal_id}/POWER",
        CONF_STATE_TOPIC: "stat/{internal_id}/POWER",
        CONF_AVAILABILITY_TOPIC: "tele/{internal_id}/LWT",
        CONF_PAYLOAD_ON: "ON",
        CONF_PAYLOAD_OFF: "OFF",
        CONF_PAYLOAD_AVAILABLE: "Online",
        CONF_PAYLOAD_NOT_AVAILABLE: "Offline"
    },
    "basic": {}
}

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = vol.Schema({
    vol.Required(CONF_PLATFORM): cv.string,
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_INTERNAL_ID): cv.string,
    vol.Required(CONF_TYPE): cv.string
}, extra = vol.ALLOW_EXTRA)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up Tasmota switch through configuration.yaml."""
    await _async_setup_entity(hass, config, async_add_entities)
    # await sensor.async_setup_platform(hass, config, async_add_entities)

async def _async_setup_entity(hass, config, async_add_entities, config_entry=None, discovery_hash=None):
    async_add_entities([TasmotaSwitch(hass, config, config_entry, discovery_hash)])

class TasmotaSwitch(MqttSwitch):

    def __init__(self, hass, config, config_entry, discovery_data):
        """Initializes a Tasmota light."""
        self._internal_id = config.get(CONF_INTERNAL_ID, None)
        self._hass = hass
        self._loop = asyncio.new_event_loop()
        _LOGGER.info("Initializing %s" % self._internal_id)
        MqttSwitch.__init__(self, hass = self._hass, config = self._get_config(config), config_entry = config_entry, discovery_data = discovery_data)
        asyncio.set_event_loop(self._loop)

        if "motion_iterval" in config:
            self.motionTimer = motion.Timer(hass, _LOGGER, config, self)

    def _get_config(self, config):
        self.set_config(config, _TYPES.get(_TYPE_COMMON))
        if CONF_TYPE in config and config.get(CONF_TYPE) in _TYPES:
            self.set_config(config, _TYPES.get(config.get(CONF_TYPE)))

        return config

    def set_config(self, config, data):
        _environment_values = {
            "internal_id": self._internal_id
        }
        for key in data:
            _value = data.get(key)
            if isinstance(_value, str):
                _value = _value.format(**_environment_values)
            config.setdefault(key, _value)

    def turn_on(self):
        self._loop.run_until_complete(self.async_turn_on())
    
    def turn_off(self):
        self._loop.run_until_complete(self.async_turn_off())
