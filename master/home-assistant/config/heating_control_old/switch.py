import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import STATE_OFF, STATE_ON

_LOGGER = logging.getLogger(__name__)

_CONF_NAME = "name"
_CONF_ID = "id"
_CONF_ENTITY = "entity"

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up a valve through configuration.yaml."""
    async_add_entities([ValveSwitch(hass, config)])
    _LOGGER.info("New valve was added: {}".format(config.get(_CONF_ID)))

class ValveSwitch(SwitchEntity):

    def __init__(self, hass, config):
        self._config = config
        self._state = None

    async def async_turn_on(self, **kwargs):
        """Turn the device on."""
        _LOGGER.info("Opening the valve: {}".format(self._config.get(_CONF_NAME)))
        await self.async_turn_on()
        self._state = STATE_ON

    async def async_turn_off(self, **kwargs):
        """Turn the device off."""
        _LOGGER.info("Closing the valve: {}".format(self._config.get(_CONF_NAME)))
        await self.async_turn_off()
        self._state = STATE_OFF

    @property
    def name(self):
        """Return the switch name."""
        return self._config.get(_CONF_NAME)

    @property
    def unique_id(self):
        """Return the switch unique ID."""
        return self._config.get(_CONF_ID)

    @property
    def icon(self):
        """Return the icon of the valve."""
        return self._config.get("icon", "mdi:pipe-valve")

    @property
    def state(self) -> _State:
        """Return state of the Global task."""
        return self._state