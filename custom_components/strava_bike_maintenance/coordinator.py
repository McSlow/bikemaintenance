"""Data coordinator for the Strava Bike Maintenance integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any, Dict

from aiohttp import ClientResponseError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import StravaApiClient
from .const import DOMAIN, UPDATE_INTERVAL_SECONDS
from .wear import WearCounterManager

_LOGGER = logging.getLogger(__name__)


class StravaDataUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Coordinates fetching Strava data and computing wear counters."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: StravaApiClient,
        wear_manager: WearCounterManager,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} data",
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )
        self._api_client = api_client
        self.wear_manager = wear_manager
        self.athlete: Dict[str, Any] | None = None

    async def _async_update_data(self) -> Dict[str, Any]:
        try:
            athlete_payload = await self._api_client.async_get_bikes()
        except ClientResponseError as err:
            raise UpdateFailed(f"Error communicating with Strava API: {err}") from err

        bike_distances_km = StravaApiClient.extract_bike_distances_km(athlete_payload)
        wear_snapshot = await self.wear_manager.async_process_bikes(bike_distances_km)

        data: Dict[str, Any] = {}
        for bike in athlete_payload.get("bikes", []):
            gear_id = bike.get("id")
            if gear_id is None:
                continue

            data[gear_id] = {
                "gear_id": gear_id,
                "name": bike.get("name") or gear_id,
                "brand_name": bike.get("brand_name"),
                "model_name": bike.get("model_name"),
                "frame_type": bike.get("frame_type"),
                "distance_km": bike_distances_km.get(gear_id, 0.0),
                "wear_counters": wear_snapshot.get(gear_id, {}),
            }

        self.athlete = {
            "id": athlete_payload.get("id"),
            "firstname": athlete_payload.get("firstname"),
            "lastname": athlete_payload.get("lastname"),
        }

        return data
