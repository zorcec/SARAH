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

from ..sarah import (
    CONF_INTERNAL_ID,
    CONF_TYPE,
    ICON_GENERIC,
    CONF_INTERNAL_ID
)

ptvsd.enable_attach()
#ptvsd.wait_for_attach()

_LOGGER = logging.getLogger(__name__)

_CONF_SENSORS = "sensors"

_SENSOR_TYPES = {
    "temperature": {
        "attribute": "temperature",
        "icon": "mdi:temperature-celsius",
        "name": "Temperature"
    },
    "pressure": {
        "attribute": "pressure",
        "icon": "mdi:airballoon",
        "name": "Pressure"
    },
    "humidity": {
        "attribute": "humidity",
        "icon": "mdi:water",
        "name": "Humidity"
    },
    "brightness": {
        "attribute": "brightness",
        "icon": "mdi:brightness-6",
        "name": "Bightness"
    }
}

PLATFORM_SCHEMA = vol.Schema({
    vol.Required(CONF_PLATFORM): cv.string,
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_TYPE): cv.string
}, extra = vol.ALLOW_EXTRA)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up Sensorio through configuration.yaml."""
    await _async_setup_entity(hass, config, async_add_entities)

async def _async_setup_entity(hass, config, async_add_entities, config_entry=None, discovery_hash=None):
    sensorio_entity = Sensorio(hass, config, config_entry, discovery_hash, async_add_entities)
    for sensor_config in config.get(_CONF_SENSORS):
        sensor_entity = SensorioSensor(sensorio_entity, sensor_config)
        sensorio_entity.add_sensor(sensor_entity)
    async_add_entities([sensorio_entity])
    async_add_entities(sensorio_entity.get_sensors())
    await sensorio_entity.subscribe()
    await sensorio_entity.refresh()

class Sensorio(Entity):

    def __init__(self, hass, config, config_entry, discovery_hash, async_add_entities):
        """Initializes a Sensorio device"""
        self._name = config.get("name")
        self._internal_id = config.get(CONF_INTERNAL_ID, None)
        self._state = "on"
        self._attr = {}
        self._type = config.get(CONF_TYPE)
        self._hass = hass
        self._async_add_entities = async_add_entities
        self._sensors = []
        _LOGGER.info("Initializing %s" % self._internal_id)

    async def refresh(self):
        _LOGGER.debug("Refreshing data: %s" % self._internal_id)
        _cmd_data_topic = "/cmd/sensorio/%s/DATA" % self._internal_id
        mqtt.async_publish(self._hass, _cmd_data_topic, "")

    async def subscribe(self):
        _data_topic = "/sensorio/%s/DATA" % self._internal_id
        _event_topic = "/sensorio/%s/EVENT/#" % self._internal_id

        @callback
        def data_message(topic, payload, qos):
            """Handle received MQTT message."""
            data = json.loads(payload)
            for key in data:
                self._attr[key] = data[key]
            for sensor in self._sensors:
                sensor.update()

        @callback
        def event_message(topic, payload, qos):
            """Handle received MQTT message."""
            _data = json.loads(payload)
            _event_name = re.split(".*/EVENT/", topic)[1]
            _LOGGER.debug("Event received: %s, %s" % (self._internal_id, _event_name))
            self._hass.bus.async_fire("sensorio:%s" % _event_name.lower(), {
                **_data,
                "internal_id": self._internal_id
            })

        await mqtt.async_subscribe(self._hass, _data_topic, data_message)
        await mqtt.async_subscribe(self._hass, _event_topic, event_message)

    def add_sensor(self, sensor):
        self._sensors.append(sensor)

    def getAttribute(self, name):
        return self._attr.get(name, None)

    def get_sensors(self):
        return self._sensors

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
        return self._attr

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_GENERIC

class SensorioSensor(Entity):

    def __init__(self, sensorio_entity, sensor_config):
        self._sensorio_entity = sensorio_entity
        self._config = self.get_config(sensor_config)
        self._state = None

    def get_config(self, config):
        _type = config.get("type")
        if _type in _SENSOR_TYPES:
            return {
                **config,
                **_SENSOR_TYPES.get(_type)
            }
        return config

    def update(self):
        self._state = self._sensorio_entity.getAttribute(self._config.get("attribute"))
        #self.async_write_ha_state()

    @property
    def name(self):
        """Return the name of the sensor."""
        return "%s %s" % (self._sensorio_entity._name, self._config.get("name"))

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._config.get("icon", ICON_GENERIC)