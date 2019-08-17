import voluptuous as vol
import logging
import ptvsd

from homeassistant.core import callback
from homeassistant.const import DEVICE_DEFAULT_NAME
import homeassistant.helpers.config_validation as cv

from homeassistant.components.mqtt.light.schema_basic import ( 
    MqttLight,
    DEFAULT_ON_COMMAND_TYPE,
    CONF_BRIGHTNESS_SCALE,
    CONF_ON_COMMAND_TYPE
)

from homeassistant.components.mqtt import (
    CONF_COMMAND_TOPIC,
    CONF_AVAILABILITY_TOPIC,
    CONF_QOS,
    CONF_RETAIN,
    CONF_STATE_TOPIC,
    CONF_UNIQUE_ID,
    CONF_PAYLOAD_NOT_AVAILABLE,
    CONF_PAYLOAD_AVAILABLE
)

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

ptvsd.enable_attach()
#ptvsd.wait_for_attach()

_LOGGER = logging.getLogger(__name__)

_CONF_INTERNAL_ID = "internal_id"

PLATFORM_SCHEMA = vol.Schema({
    vol.Required(CONF_PLATFORM): cv.string,
    vol.Required(CONF_NAME): cv.string,
    vol.Required(_CONF_INTERNAL_ID): cv.string
}, extra = vol.ALLOW_EXTRA)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up Tasmota light through configuration.yaml."""
    await _async_setup_entity(config, async_add_entities)

async def _async_setup_entity(config, async_add_entities, config_entry=None, discovery_hash=None):
    async_add_entities([TasmotaLight(config, config_entry, discovery_hash)])

class TasmotaLight(MqttLight):

    def __init__(self, config, config_entry, discovery_hash):
        """Initializes a Tasmota light."""
        self._internal_id = config.get(_CONF_INTERNAL_ID, None)
        _LOGGER.info("Initializing %s" % self._internal_id)
        MqttLight.__init__(self, self._get_config(config), config_entry, discovery_hash)

    def _get_config(self, config):
        config[CONF_COMMAND_TOPIC] = "cmnd/%s/POWER" % self._internal_id
        config[CONF_STATE_TOPIC] = "stat/%s/POWER" % self._internal_id
        config[CONF_AVAILABILITY_TOPIC] = "tele/%s/LWT" % self._internal_id
        config[CONF_PAYLOAD_ON] = "ON"
        config[CONF_PAYLOAD_OFF] = "OFF"
        config[CONF_PAYLOAD_AVAILABLE] = "Online"
        config[CONF_PAYLOAD_NOT_AVAILABLE] = "Offline"
        config[CONF_OPTIMISTIC] = False
        config[CONF_QOS] = 0
        config[CONF_RETAIN] = False
        config[CONF_ON_COMMAND_TYPE] = DEFAULT_ON_COMMAND_TYPE

        config[CONF_BRIGHTNESS_SCALE] = 100
        config["brightness_command_topic"] = "cmnd/%s/DIMMER" % self._internal_id
        config["brightness_state_topic"] = "stat/%s/RESULT" % self._internal_id
        config["brightness_value_template"] = "{%- if value_json.Dimmer is defined -%}{{ value_json.Dimmer | default(0) }}{%- endif -%}"
        
        return config
