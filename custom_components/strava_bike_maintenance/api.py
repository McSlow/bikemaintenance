"""Asynchronous client for the Strava API."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List

from aiohttp import ClientResponseError
from homeassistant.helpers import config_entry_oauth2_flow

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)


class StravaApiClient:
    """Wraps authenticated access to Strava endpoints."""

    def __init__(self, oauth_session: config_entry_oauth2_flow.OAuth2Session) -> None:
        self._session = oauth_session
        # Serialise outgoing requests so token refreshes from the session cannot race.
        self._lock = asyncio.Lock()

    async def async_get_bikes(self) -> Dict[str, Any]:
        """Fetch the authenticated athlete's bike data."""
        async with self._lock:
            try:
                data = await self._session.async_request(
                    "get",
                    f"{API_BASE_URL}/athlete",
                    raise_for_status=True,
                )
            except ClientResponseError as err:
                _LOGGER.error(
                    "Strava API request failed: status=%s message=%s",
                    err.status,
                    err.message,
                )
                raise

        return data

    @staticmethod
    def extract_bike_distances_km(athlete_payload: Dict[str, Any]) -> Dict[str, float]:
        """Return a mapping of bike ids to total distance in kilometres."""
        bikes: List[Dict[str, Any]] = athlete_payload.get("bikes", [])
        distances: Dict[str, float] = {}
        for bike in bikes:
            gear_id = bike.get("id")
            distance_meters = bike.get("distance")
            if gear_id is None or distance_meters is None:
                continue
            try:
                distance_km = float(distance_meters) / 1000
            except (TypeError, ValueError):
                continue
            distances[gear_id] = distance_km
        return distances
