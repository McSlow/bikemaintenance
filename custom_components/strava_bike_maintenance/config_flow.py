"""Config flow for the Strava Bike Maintenance integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.network import NoURLAvailableError, get_url

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
        # We always show a callback hint; fall back to an internal URL so users
        # have something to copy even before an external URL is configured.
        placeholder_callback = _compute_callback_url(
            self.hass, allow_internal_fallback=True
        )

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                # Strava must be able to reach the redirect, so refuse to continue
                # if Home Assistant cannot provide an externally accessible URL.
                redirect_uri = _compute_callback_url(self.hass, allow_internal_fallback=False)
            except HomeAssistantError:
                errors["base"] = "missing_external_url"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                self._client_id = user_input[CONF_CLIENT_ID]
                self._client_secret = user_input[CONF_CLIENT_SECRET]

                self.flow_impl = StravaOAuth2Implementation(
                    self.hass,
                    DOMAIN,
                    self._client_id,
                    self._client_secret,
                    API_AUTHORIZE_URL,
                    API_TOKEN_URL,
                    redirect_uri,
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
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict):
        """Handle re-authentication with existing credentials."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        assert entry is not None  # nosec
        # Reauth always re-validates that an external callback URL is available.
        redirect_uri = _compute_callback_url(self.hass, allow_internal_fallback=False)

        self._client_id = entry.data[CONF_CLIENT_ID]
        self._client_secret = entry.data[CONF_CLIENT_SECRET]

        self.flow_impl = StravaOAuth2Implementation(
            self.hass,
            DOMAIN,
            self._client_id,
            self._client_secret,
            API_AUTHORIZE_URL,
            API_TOKEN_URL,
            redirect_uri,
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
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Options flow entry point."""
        return self.async_create_entry(title="", data={})


class StravaOAuth2Implementation(
    config_entry_oauth2_flow.LocalOAuth2Implementation
):
    """Local OAuth implementation with stricter redirect handling."""

    def __init__(
        self,
        hass: HomeAssistant,
        domain: str,
        client_id: str,
        client_secret: str,
        authorize_url: str,
        token_url: str,
        redirect_uri: str,
    ) -> None:
        super().__init__(
            hass,
            domain,
            client_id,
            client_secret,
            authorize_url,
            token_url,
        )
        self._redirect_uri = redirect_uri

    @property
    def redirect_uri(self) -> str:
        """Return the redirect URI used for Strava OAuth."""
        return self._redirect_uri


def _compute_callback_url(
    hass: HomeAssistant,
    *,
    allow_internal_fallback: bool,
) -> str:
    """Best-effort computation of a usable callback URL."""
    default = (
        f"https://<your-home-assistant>"
        f"{config_entry_oauth2_flow.AUTH_CALLBACK_PATH}"
    )

    try:
        base_url = get_url(
            hass,
            prefer_external=True,
            allow_cloud=False,
            allow_ip=False,
        )
    except (HomeAssistantError, NoURLAvailableError):
        if not allow_internal_fallback:
            raise HomeAssistantError("external_url_not_configured")

        try:
            base_url = get_url(
                hass,
                allow_internal=True,
                allow_cloud=False,
                allow_ip=False,
            )
        except (HomeAssistantError, NoURLAvailableError):
            return default

    return f"{base_url.rstrip('/')}{config_entry_oauth2_flow.AUTH_CALLBACK_PATH}"
