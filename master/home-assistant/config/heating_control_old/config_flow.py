import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from typing import Any, Dict, Optional
from homeassistant import config_entries
from . import DOMAIN, CONF_HEATING_PHAZE

_LOGGER = logging.getLogger(__name__)

INPUT_SCHEMA = vol.Schema(
    {vol.Required(CONF_HEATING_PHAZE): cv.positive_int}
)

class FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            _LOGGER.info("Heating cycle was set: {}".format(user_input[CONF_HEATING_PHAZE]))
            return self.async_create_entry(title="Heating Control", data=user_input)
        
        return self.async_show_form(
            step_id="user", data_schema=INPUT_SCHEMA, errors=errors
        )
