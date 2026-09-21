"""Config flow for the Siemens Climatix IC integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import (
    ClimatixApiError,
    ClimatixAuthError,
    ClimatixDataUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def _validate(hass: HomeAssistant, username: str, password: str) -> None:
    """Validate credentials and that at least one thermostat exists.

    Raises ClimatixAuthError on bad credentials, ClimatixApiError otherwise.
    """
    coordinator = ClimatixDataUpdateCoordinator(hass, username, password)
    await coordinator.async_authenticate()
    await coordinator.async_discover_plants()


class ClimatixConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config and reauth flows for Siemens Climatix IC."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            await self.async_set_unique_id(username.casefold())
            self._abort_if_unique_id_configured()

            errors = await self._try_validate(username, user_input[CONF_PASSWORD])
            if not errors:
                return self.async_create_entry(
                    title=f"Climatix IC ({username})",
                    data={
                        CONF_USERNAME: username,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Handle re-authentication when the cloud rejects stored credentials."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Confirm re-authentication with a fresh password."""
        errors: dict[str, str] = {}
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        assert entry is not None
        username = entry.data[CONF_USERNAME]

        if user_input is not None:
            errors = await self._try_validate(username, user_input[CONF_PASSWORD])
            if not errors:
                self.hass.config_entries.async_update_entry(
                    entry,
                    data={**entry.data, CONF_PASSWORD: user_input[CONF_PASSWORD]},
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            description_placeholders={"username": username},
            errors=errors,
        )

    async def _try_validate(self, username: str, password: str) -> dict[str, str]:
        """Return an errors dict ({} on success)."""
        try:
            await _validate(self.hass, username, password)
        except ClimatixAuthError:
            return {"base": "invalid_auth"}
        except ClimatixApiError as err:
            _LOGGER.debug("Climatix IC connection error: %s", err)
            return {"base": "cannot_connect"}
        except Exception:  # noqa: BLE001 - surface anything unexpected safely
            _LOGGER.exception("Unexpected error validating Climatix IC credentials")
            return {"base": "unknown"}
        return {}
