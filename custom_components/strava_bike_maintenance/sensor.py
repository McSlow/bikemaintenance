"""Sensor platform for Strava Bike Maintenance."""

from __future__ import annotations

from typing import Any, Dict, List

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, WEAR_PARTS
from .coordinator import StravaDataUpdateCoordinator

WEAR_ICONS = {
    "chain": "mdi:link-variant",
    "chain_waxing": "mdi:candle",
    "tires": "mdi:tire",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigType,
    async_add_entities,
) -> None:
    """Set up Strava Bike Maintenance sensors."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: StravaDataUpdateCoordinator = entry_data["coordinator"]

    known_bikes: set[str] = set()

    @callback
    def _add_new_bike_entities() -> None:
        """Create sensors for any bikes that appeared since the last refresh."""
        new_entities: List[SensorEntity] = []
        for gear_id in coordinator.data:
            if gear_id in known_bikes:
                continue
            known_bikes.add(gear_id)
            new_entities.append(StravaBikeDistanceSensor(coordinator, gear_id))
            for part in WEAR_PARTS:
                new_entities.append(StravaBikeWearSensor(coordinator, gear_id, part))
        if new_entities:
            async_add_entities(new_entities)

    _add_new_bike_entities()
    coordinator.async_add_listener(_add_new_bike_entities)


class StravaBikeBase(CoordinatorEntity[Dict[str, Dict[str, Any]]]):
    """Base entity shared between bike sensors."""

    def __init__(self, coordinator: StravaDataUpdateCoordinator, gear_id: str) -> None:
        super().__init__(coordinator)
        self._gear_id = gear_id

    @property
    def _bike_data(self) -> Dict[str, Any] | None:
        return self.coordinator.data.get(self._gear_id)

    @property
    def device_info(self) -> DeviceInfo:
        bike = self._bike_data or {}
        return DeviceInfo(
            identifiers={(DOMAIN, self._gear_id)},
            manufacturer=bike.get("brand_name") or "Strava",
            name=bike.get("name") or f"Strava Bike {self._gear_id}",
            model=bike.get("model_name"),
        )


class StravaBikeDistanceSensor(StravaBikeBase, SensorEntity):
    """Sensor measuring the total distance for a bike."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator: StravaDataUpdateCoordinator, gear_id: str) -> None:
        super().__init__(coordinator, gear_id)
        bike = self._bike_data or {}
        bike_name = bike.get("name") or gear_id
        self._attr_name = f"Strava {bike_name} Total Distance"
        self._attr_unique_id = f"{gear_id}_total_distance"

    @property
    def native_value(self) -> float | None:
        bike = self._bike_data
        if bike is None:
            return None
        return bike.get("distance_km")

    @property
    def extra_state_attributes(self) -> Dict[str, Any] | None:
        bike = self._bike_data
        if bike is None:
            return None
        return {
            "bike_id": self._gear_id,
            "brand": bike.get("brand_name"),
            "model": bike.get("model_name"),
        }


class StravaBikeWearSensor(StravaBikeBase, SensorEntity):
    """Sensor reporting the distance since last reset for a wear part."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        gear_id: str,
        part: str,
    ) -> None:
        super().__init__(coordinator, gear_id)
        self._part = part
        bike = self._bike_data or {}
        bike_name = bike.get("name") or gear_id
        part_label = WEAR_PARTS.get(part, part.title())
        self._attr_name = f"Strava {bike_name} {part_label}"
        self._attr_unique_id = f"{gear_id}_wear_{part}"
        self._attr_icon = WEAR_ICONS.get(part, "mdi:gauge")

    @property
    def native_value(self) -> float | None:
        bike = self._bike_data
        if bike is None:
            return None
        wear_counters = bike.get("wear_counters", {})
        return wear_counters.get(self._part)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        return {
            "bike_id": self._gear_id,
            "wear_part": self._part,
        }
