import voluptuous as vol
import logging
import ptvsd

from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

from homeassistant.const import ( 
    CONF_PLATFORM, 
    CONF_NAME
)

ptvsd.enable_attach()
#ptvsd.wait_for_attach()

_LOGGER = logging.getLogger(__name__)

CONF_ROOM_NAME = "room_name"
CONF_INTERNAL_ID = "internal_id"

PLATFORM_SCHEMA = vol.Schema({
    vol.Required(CONF_PLATFORM): cv.string,
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_ROOM_NAME): cv.string,
    vol.Required(CONF_INTERNAL_ID): cv.string
}, extra = vol.ALLOW_EXTRA)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up Sensorio through configuration.yaml."""
    await _async_setup_entity(hass, config, async_add_entities)

async def _async_setup_entity(hass, config, async_add_entities, config_entry=None, discovery_hash=None):
    async_add_entities([Sensorio(hass, config, config_entry, discovery_hash)])

class Sensorio(Entity):

    def __init__(self, hass, config, config_entry, discovery_hash):
        """Initializes a Sensorio device"""
        self._internal_id = config.get(CONF_INTERNAL_ID, None)
        self.hass = hass
        _LOGGER.info("Initializing %s" % self._internal_id)
