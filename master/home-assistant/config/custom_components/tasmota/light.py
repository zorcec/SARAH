import voluptuous as vol
import logging
import ptvsd
import asyncio

from homeassistant.core import callback

import homeassistant.components.mqtt as mqtt
import homeassistant.helpers.config_validation as cv

from homeassistant.components.mqtt.light.schema_basic import ( 
    MqttLight
)

from homeassistant.const import ( 
    CONF_PLATFORM, 
    CONF_NAME
)

from homeassistant.components.mqtt import (
    CONF_COMMAND_TOPIC
)

from . import motion
from . import configurator
from . import sensor

from ..sarah import (
    CONF_INTERNAL_ID,
    CONF_TYPE
)

# centralize
_EVENT_SENSORIO_MOTION = "sensorio:motion"
_TOPIC_MOTION_EVENT = "motion_event_topic"

ptvsd.enable_attach()
#ptvsd.wait_for_attach()

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = vol.Schema({
    vol.Required(CONF_PLATFORM): cv.string,
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_INTERNAL_ID): cv.string,
    vol.Required(CONF_TYPE): cv.string
}, extra = vol.ALLOW_EXTRA)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up Tasmota light through configuration.yaml."""
    await _async_setup_entity(hass, config, async_add_entities)
    await sensor.async_setup_platform(hass, config, async_add_entities)

async def _async_setup_entity(hass, config, async_add_entities, config_entry=None, discovery_hash=None):
    internal_id = config.get(CONF_INTERNAL_ID, None)
    async_add_entities([await TasmotaLight(hass, config_entry, internal_id, discovery_hash).create(config)])

class TasmotaLight(MqttLight):

    def __init__(self, hass, config_entry, internal_id, discovery_hash):
        """Initializes a Tasmota light."""
        self._internal_id = internal_id
        self._hass = hass
        self._config_entry = config_entry
        self._discovery_hash = discovery_hash
        self._loop = asyncio.new_event_loop()
        _LOGGER.info("Initializing %s" % self._internal_id)
        asyncio.set_event_loop(self._loop)

    async def create(self, config):
        self.configurator = configurator.Configurator(self._hass, config)
        self._config = self.configurator.getConfig()
        MqttLight.__init__(self, config, self._config_entry, self._discovery_hash)

        self.refresh()

        if "motion_iterval" in self._config:
            self.motionTimer = motion.Timer(self._hass, _LOGGER, self._config, self)

        if "motion_event_topic" in self._config:
            await self.simulate_sensorio_motion()

        return self

    def refresh(self):
        _request_topics = [
            self._config.get(CONF_COMMAND_TOPIC)
        ]
        for _request_topic in _request_topics:
            mqtt.async_publish(self._hass, _request_topic, "")

    async def simulate_sensorio_motion(self):

        @callback
        def event_message(topic, payload, qos):
            """Handle received MQTT message."""
            _data = "0"
            if payload == "ON":
                _data = "1"
            _LOGGER.debug("Simulating sensorio event: %s, %s, %s" % (self._internal_id, _EVENT_SENSORIO_MOTION, _data))
            self._hass.bus.async_fire(_EVENT_SENSORIO_MOTION, {
                "data": _data,
                "internal_id": self._internal_id
            })
            
        if self._config.get(_TOPIC_MOTION_EVENT):
            _LOGGER.debug("Simulating sensorio motion on tasmota: %s, %s" % (self._internal_id, self._config.get(_TOPIC_MOTION_EVENT)))
            await mqtt.async_subscribe(self._hass, self._config.get(_TOPIC_MOTION_EVENT), event_message)

    def turn_on(self):
        self._loop.run_until_complete(self.async_turn_on())
    
    def turn_off(self):
        self._loop.run_until_complete(self.async_turn_off())
