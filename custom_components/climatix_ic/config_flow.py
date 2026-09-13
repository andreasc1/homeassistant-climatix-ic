"""Config flow for Siemens Climatix IC integration."""

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .coordinator import ClimatixDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
  """Handle a config flow for Siemens Climatix IC."""

  VERSION = 1

  async def async_step_user(self, user_input=None) -> FlowResult:
    errors = {}

    if user_input is not None:
      coordinator = ClimatixDataUpdateCoordinator(
          self.hass,
          user_input[CONF_USERNAME],
          user_input[CONF_PASSWORD],
      )

      try:
        await self.hass.async_add_executor_job(
            coordinator.authenticate_and_discover
        )
      except Exception as err:
        _LOGGER.error("Climatix IC authentication error: %s", err)
        errors["base"] = "invalid_auth"
      else:
        return self.async_create_entry(
            title=f"Climatix IC ({user_input[CONF_USERNAME]})",
            data={
                CONF_USERNAME: user_input[CONF_USERNAME],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                "plant_id": coordinator.plant_id,
            },
        )

    return self.async_show_form(
        step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
    )