import voluptuous as vol
import logging
import ptvsd
import json
import re

from homeassistant.helpers.entity import Entity
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
import homeassistant.components.mqtt as mqtt

from homeassistant.const import ( 
    CONF_PLATFORM, 
    CONF_NAME
)

ptvsd.enable_attach()
#ptvsd.wait_for_attach()

_LOGGER = logging.getLogger(__name__)

CONF_ROOM_NAME = "room_name"
CONF_INTERNAL_ID = "internal_id"
CONF_TYPE = "type"

ICON_MOTION_SENSOR = "mdi:motion-sensor"
ICON_GENERIC = "mdi:cupcake"
TYPE_WALL_MOUNT = "wall_mount"
TYPE_BOX = "box"

PLATFORM_SCHEMA = vol.Schema({
    vol.Required(CONF_PLATFORM): cv.string,
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_ROOM_NAME): cv.string,
    vol.Required(CONF_INTERNAL_ID): cv.string,
    vol.Required(CONF_TYPE): cv.string
}, extra = vol.ALLOW_EXTRA)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up Sensorio through configuration.yaml."""
    await _async_setup_entity(hass, config, async_add_entities)

async def _async_setup_entity(hass, config, async_add_entities, config_entry=None, discovery_hash=None):
    sensorio_entity = Sensorio(hass, config, config_entry, discovery_hash)
    await sensorio_entity.subscribe()
    async_add_entities([sensorio_entity])

class Sensorio(Entity):

    def __init__(self, hass, config, config_entry, discovery_hash):
        """Initializes a Sensorio device"""
        self._name = config.get("name")
        self._internal_id = config.get(CONF_INTERNAL_ID, None)
        self._state = None
        self._attr = {}
        self._type = config.get(CONF_TYPE)
        self._hass = hass
        _LOGGER.info("Initializing %s" % self._internal_id)

    async def subscribe(self):
        _data_topic = "/sensorio/%s/DATA" % self._internal_id
        _event_topic = "/sensorio/%s/EVENT/#" % self._internal_id

        @callback
        def data_message(topic, payload, qos):
            """Handle received MQTT message."""
            _LOGGER.debug("Received data: %s" % self._internal_id)
            data = json.loads(payload)
            for key in data:
                self._attr[key] = data[key]

        @callback
        def event_message(topic, payload, qos):
            """Handle received MQTT message."""
            _data = json.loads(payload)
            _event_name = re.split(".*/EVENT/", topic)[1]
            _LOGGER.debug("Event received: %s, %s" % (self._internal_id, _event_name))
            self._hass.bus.fire("sensorio:%s" % _event_name.lower(), {
                **_data,
                "internal_name": self._internal_id
            })

        await mqtt.async_subscribe(self._hass, _data_topic, data_message)
        await mqtt.async_subscribe(self._hass, _event_topic, event_message)

    @property
    def device_info(self):
        return {
            "name": self._name,
            "manufacturer": "Tomislav Zorcec <https://github.com/zorcec>",
        }

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attr

    @property
    def icon(self):
        """Return the icon of the sensor."""
        if self._type == TYPE_WALL_MOUNT:
            return ICON_MOTION_SENSOR
        else:
            return ICON_GENERIC
