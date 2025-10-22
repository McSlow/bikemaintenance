"""Home Assistant integration for Strava bike maintenance tracking."""

from __future__ import annotations

from functools import partial
import logging
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_entry_oauth2_flow

from .api import StravaApiClient
from .const import (
    API_AUTHORIZE_URL,
    API_TOKEN_URL,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    DOMAIN,
    WEAR_PARTS,
)
from .coordinator import StravaDataUpdateCoordinator
from .wear import WearCounterManager

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, _: Dict[str, Any]) -> bool:
    """Set up the Strava Bike Maintenance domain."""
    hass.data.setdefault(DOMAIN, {"entries": {}, "service_registered": False})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Strava Bike Maintenance from a config entry."""
    domain_data = hass.data.setdefault(
        DOMAIN, {"entries": {}, "service_registered": False}
    )

    client_id = entry.data[CONF_CLIENT_ID]
    client_secret = entry.data[CONF_CLIENT_SECRET]

    implementation = config_entry_oauth2_flow.LocalOAuth2Implementation(
        hass,
        DOMAIN,
        client_id,
        client_secret,
        API_AUTHORIZE_URL,
        API_TOKEN_URL,
    )
    session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)

    wear_manager = WearCounterManager(hass)
    coordinator = StravaDataUpdateCoordinator(
        hass,
        StravaApiClient(session),
        wear_manager,
    )

    await coordinator.async_config_entry_first_refresh()

    domain_data["entries"][entry.entry_id] = {
        "coordinator": coordinator,
        "wear_manager": wear_manager,
    }

    if not domain_data["service_registered"]:
        hass.services.async_register(
            DOMAIN,
            "reset_wear_counter",
            partial(_async_handle_reset_service, hass),
        )
        domain_data["service_registered"] = True

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Strava Bike Maintenance config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        domain_data = hass.data.get(DOMAIN)
        if domain_data:
            domain_data["entries"].pop(entry.entry_id, None)
    return unload_ok


async def _async_handle_reset_service(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle the reset_wear_counter service call."""
    bike_id: str = call.data["bike_id"]
    part: str = call.data["part"]

    if part not in WEAR_PARTS:
        raise HomeAssistantError(f"Unknown wear part '{part}'.")

    domain_data = hass.data.get(DOMAIN, {})
    entries: Dict[str, Dict[str, Any]] = domain_data.get("entries", {})

    if not entries:
        raise HomeAssistantError("Strava Bike Maintenance is not configured.")

    handled = False

    for entry_data in entries.values():
        coordinator: StravaDataUpdateCoordinator = entry_data["coordinator"]
        wear_manager: WearCounterManager = entry_data["wear_manager"]

        if bike_id not in coordinator.data:
            continue

        await wear_manager.async_reset_counter(bike_id, part)
        wear_snapshot = await wear_manager.async_get_wear_snapshot(bike_id)

        updated_data = dict(coordinator.data)
        bike_data = dict(updated_data[bike_id])
        bike_data["wear_counters"] = wear_snapshot
        updated_data[bike_id] = bike_data
        coordinator.async_set_updated_data(updated_data)
        handled = True

    if not handled:
        raise HomeAssistantError(
            f"Bike with id '{bike_id}' is not known to this integration."
        )
