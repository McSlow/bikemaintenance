"""Config flow for the Strava Bike Maintenance integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_entry_oauth2_flow

from .const import (
    API_AUTHORIZE_URL,
    API_TOKEN_URL,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class StravaConfigFlow(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle a config flow for Strava Bike Maintenance."""

    DOMAIN = DOMAIN

    def __init__(self) -> None:
        """Initialise the config flow."""
        self._client_id: str | None = None
        self._client_secret: str | None = None

    @property
    def logger(self) -> logging.Logger:
        """Logger provided to the base flow."""
        return _LOGGER

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step of the flow."""
        placeholder_callback = _redirect_hint(self.hass)

        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            self._client_id = user_input[CONF_CLIENT_ID]
            self._client_secret = user_input[CONF_CLIENT_SECRET]

            self.flow_impl = config_entry_oauth2_flow.LocalOAuth2Implementation(
                self.hass,
                DOMAIN,
                self._client_id,
                self._client_secret,
                API_AUTHORIZE_URL,
                API_TOKEN_URL,
            )

            return await self.async_step_auth()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLIENT_ID): str,
                    vol.Required(CONF_CLIENT_SECRET): str,
                }
            ),
            description_placeholders={"callback_url": placeholder_callback},
        )

    async def async_step_reauth(self, entry_data: dict):
        """Handle re-authentication with existing credentials."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        assert entry is not None  # nosec
        self._client_id = entry.data[CONF_CLIENT_ID]
        self._client_secret = entry.data[CONF_CLIENT_SECRET]

        self.flow_impl = config_entry_oauth2_flow.LocalOAuth2Implementation(
            self.hass,
            DOMAIN,
            self._client_id,
            self._client_secret,
            API_AUTHORIZE_URL,
            API_TOKEN_URL,
        )

        return await self.async_step_auth()

    async def async_oauth_create_entry(self, data: dict) -> config_entries.ConfigEntry:
        """Create a config entry after successful OAuth authentication."""
        data = dict(data)
        data[CONF_CLIENT_ID] = self._client_id
        data[CONF_CLIENT_SECRET] = self._client_secret

        return self.async_create_entry(
            title="Strava Bike Maintenance",
            data=data,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow."""
        return StravaOptionsFlow(config_entry)

    @property
    def extra_authorize_data(self) -> dict:
        """Additional data to append to the authorisation URL."""
        return {
            "scope": "read",
            "approval_prompt": "auto",
        }


class StravaOptionsFlow(config_entries.OptionsFlow):
    """Placeholder for potential future options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Options flow entry point."""
        return self.async_create_entry(title="", data={})


def _redirect_hint(hass: HomeAssistant) -> str:
    """Return a callback hint for the form description."""
    try:
        return config_entry_oauth2_flow.async_get_redirect_uri(hass)
    except RuntimeError:
        return config_entry_oauth2_flow.MY_AUTH_CALLBACK_PATH
