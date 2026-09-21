"""Climate platform for the Siemens Climatix IC thermostat."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    DP_OPERATING_MODE,
    DP_TARGET_SETPOINT,
    MODE_COMFORT,
    MODE_PROTECTION,
)
from .coordinator import ClimatixDataUpdateCoordinator
from .entity import ClimatixEntity

DEFAULT_MIN_TEMP = 6.5
DEFAULT_MAX_TEMP = 35.0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one climate entity per discovered thermostat."""
    coordinator: ClimatixDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ClimatixThermostat(coordinator, plant) for plant in coordinator.plants
    )


class ClimatixThermostat(ClimatixEntity, ClimateEntity):
    """A Siemens RDS thermostat exposed as a Home Assistant climate entity."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_target_temperature_step = 0.5
    # Opt in to the modern turn_on/turn_off behaviour (no deprecation shim).
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(
        self, coordinator: ClimatixDataUpdateCoordinator, plant: dict[str, Any]
    ) -> None:
        super().__init__(coordinator, plant)
        self._attr_name = "Climatix Thermostat"
        self._attr_unique_id = f"{plant['id']}_climate"

    @property
    def current_temperature(self) -> float | None:
        return self._plant_data.get("room_temperature")

    @property
    def target_temperature(self) -> float | None:
        return self._plant_data.get("target_setpoint")

    @property
    def current_humidity(self) -> float | None:
        return self._plant_data.get("humidity")

    @property
    def min_temp(self) -> float:
        bounds = self._plant_data.get("_bounds", {}).get("target_setpoint")
        return bounds[0] if bounds else DEFAULT_MIN_TEMP

    @property
    def max_temp(self) -> float:
        bounds = self._plant_data.get("_bounds", {}).get("target_setpoint")
        return bounds[1] if bounds else DEFAULT_MAX_TEMP

    @property
    def hvac_mode(self) -> HVACMode:
        if self._plant_data.get("operating_mode") == MODE_COMFORT:
            return HVACMode.HEAT
        return HVACMode.OFF

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set a new target setpoint."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return
        await self.coordinator.async_set_value(
            self._plant_id, DP_TARGET_SETPOINT, float(temp)
        )
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Switch between Comfort (HEAT) and Protection (OFF)."""
        mode = MODE_COMFORT if hvac_mode == HVACMode.HEAT else MODE_PROTECTION
        await self.coordinator.async_set_value(
            self._plant_id, DP_OPERATING_MODE, mode
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        await self.async_set_hvac_mode(HVACMode.OFF)
