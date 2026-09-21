"""Shared base entity for the Siemens Climatix IC integration."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_MODEL, DOMAIN, MANUFACTURER
from .coordinator import ClimatixDataUpdateCoordinator


def build_device_info(plant: dict[str, Any]) -> DeviceInfo:
    """Return DeviceInfo for a single thermostat (plant)."""
    model = plant.get("model") or DEFAULT_MODEL
    city = plant.get("city")
    name = f"{MANUFACTURER} {model}"
    if city:
        name = f"{name} ({city})"
    return DeviceInfo(
        identifiers={(DOMAIN, plant["id"])},
        manufacturer=MANUFACTURER,
        model=model,
        name=name,
        serial_number=plant.get("serial"),
        sw_version=plant.get("sw_version"),
    )


class ClimatixEntity(CoordinatorEntity[ClimatixDataUpdateCoordinator]):
    """Base class binding an entity to one plant on the account."""

    def __init__(
        self, coordinator: ClimatixDataUpdateCoordinator, plant: dict[str, Any]
    ) -> None:
        super().__init__(coordinator)
        self._plant = plant
        self._plant_id = plant["id"]
        self._attr_device_info = build_device_info(plant)

    @property
    def _plant_data(self) -> dict[str, Any]:
        """Return this plant's decoded datapoint values."""
        return self.coordinator.data.get(self._plant_id, {})

    @property
    def available(self) -> bool:
        """Available only when the last poll succeeded and this plant is present."""
        return super().available and self._plant_id in self.coordinator.data
