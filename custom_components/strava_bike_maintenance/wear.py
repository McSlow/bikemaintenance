"""Wear counter management for Strava Bike Maintenance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION, WEAR_PARTS


@dataclass
class BikeWearState:
    """In-memory representation of wear data for a single bike."""

    last_total_distance_km: float | None
    counters_km: Dict[str, float]


class WearCounterManager:
    """Synchronises wear counters between Strava updates and Home Assistant."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._store = Store[dict[str, Any]](
            hass, STORAGE_VERSION, STORAGE_KEY, private=True
        )
        self._states: Dict[str, BikeWearState] = {}
        self._loaded = False

    async def async_load(self) -> None:
        """Load persisted wear counter data."""
        if self._loaded:
            return

        data = await self._store.async_load() or {}
        bikes: Dict[str, BikeWearState] = {}
        for bike_id, persisted in data.get("bikes", {}).items():
            last_total = persisted.get("last_total_distance_km")
            counters = {
                part: float(persisted.get("counters", {}).get(part, 0.0))
                for part in WEAR_PARTS
            }
            bikes[bike_id] = BikeWearState(last_total, counters)
        self._states = bikes
        self._loaded = True

    async def async_save(self) -> None:
        """Persist wear counter data."""
        await self._store.async_save(
            {
                "bikes": {
                    bike_id: {
                        "last_total_distance_km": state.last_total_distance_km,
                        "counters": state.counters_km,
                    }
                    for bike_id, state in self._states.items()
                }
            }
        )

    async def async_process_bikes(
        self, bike_distances_km: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """Update counters based on fresh bike distances and return wear data."""
        await self.async_load()

        wear_snapshot: Dict[str, Dict[str, float]] = {}

        for bike_id, total_km in bike_distances_km.items():
            state = self._states.get(
                bike_id,
                BikeWearState(last_total_distance_km=None, counters_km={}),
            )

            # Ensure counters exist for all wear parts
            for part in WEAR_PARTS:
                state.counters_km.setdefault(part, 0.0)

            if state.last_total_distance_km is None:
                # First observation - treat as baseline with no accrued wear.
                state.last_total_distance_km = total_km
            else:
                # Strava can only increase cumulative distance, so ignore non-positive deltas.
                delta = total_km - state.last_total_distance_km
                if delta > 0:
                    for part in WEAR_PARTS:
                        state.counters_km[part] += delta
                state.last_total_distance_km = total_km

            self._states[bike_id] = state
            wear_snapshot[bike_id] = dict(state.counters_km)

        await self.async_save()
        return wear_snapshot

    async def async_reset_counter(self, bike_id: str, part: str) -> None:
        """Reset a wear counter for a bike and persist the change."""
        await self.async_load()

        if part not in WEAR_PARTS:
            raise ValueError(f"Unknown wear part '{part}'")

        state = self._states.setdefault(
            bike_id,
            BikeWearState(last_total_distance_km=None, counters_km={}),
        )
        state.counters_km.setdefault(part, 0.0)
        state.counters_km[part] = 0.0

        self._states[bike_id] = state
        await self.async_save()

    async def async_get_wear_snapshot(self, bike_id: str) -> Dict[str, float]:
        """Return the current wear counters for a bike."""
        await self.async_load()
        state = self._states.get(
            bike_id,
            BikeWearState(last_total_distance_km=None, counters_km={}),
        )
        for part in WEAR_PARTS:
            state.counters_km.setdefault(part, 0.0)
        return dict(state.counters_km)
