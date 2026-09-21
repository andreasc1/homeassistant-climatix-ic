"""Switch platform for the Siemens Climatix IC thermostat.

Three switches per thermostat:
  * Thermostat Power - operating mode Comfort (3) vs Protection (1).
  * Hot Water Heater - inverted datapoint (0 = ON, 1 = OFF).
  * Space Heating    - direct datapoint (1 = ON; anything else = OFF).

Note on Space Heating: the device reports its "off/idle" state as a non-1
value (observed as 5 on RDS110), which is why ``is_on`` tests ``== 1`` rather
than ``!= 0``. Turning the switch on writes 1 and off writes 0.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    DP_HEATING_SWITCH,
    DP_OPERATING_MODE,
    DP_WATER_SWITCH,
    MODE_COMFORT,
    MODE_PROTECTION,
)
from .coordinator import ClimatixDataUpdateCoordinator
from .entity import ClimatixEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch entities for every discovered thermostat."""
    coordinator: ClimatixDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SwitchEntity] = []
    for plant in coordinator.plants:
        entities.append(ClimatixPowerSwitch(coordinator, plant))
        entities.append(
            ClimatixZoneSwitch(
                coordinator,
                plant,
                data_key="water_switch",
                name="Hot Water Heater",
                dp_suffix=DP_WATER_SWITCH,
                icon="mdi:water-boiler",
                inverted=True,  # 0 = ON, 1 = OFF
            )
        )
        entities.append(
            ClimatixZoneSwitch(
                coordinator,
                plant,
                data_key="heating_switch",
                name="Space Heating",
                dp_suffix=DP_HEATING_SWITCH,
                icon="mdi:radiator",
                inverted=False,  # 1 = ON, non-1 = OFF
            )
        )
    async_add_entities(entities)


class ClimatixPowerSwitch(ClimatixEntity, SwitchEntity):
    """Main power: Comfort mode (on) vs Protection mode (off)."""

    _attr_icon = "mdi:power"

    def __init__(
        self, coordinator: ClimatixDataUpdateCoordinator, plant: dict[str, Any]
    ) -> None:
        super().__init__(coordinator, plant)
        self._attr_name = "Climatix Thermostat Power"
        self._attr_unique_id = f"{plant['id']}_thermostat_power"

    @property
    def is_on(self) -> bool:
        return self._plant_data.get("operating_mode") == MODE_COMFORT

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_value(
            self._plant_id, DP_OPERATING_MODE, MODE_COMFORT
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_value(
            self._plant_id, DP_OPERATING_MODE, MODE_PROTECTION
        )
        await self.coordinator.async_request_refresh()


class ClimatixZoneSwitch(ClimatixEntity, SwitchEntity):
    """A single on/off datapoint (heating or hot water)."""

    def __init__(
        self,
        coordinator: ClimatixDataUpdateCoordinator,
        plant: dict[str, Any],
        *,
        data_key: str,
        name: str,
        dp_suffix: str,
        icon: str,
        inverted: bool = False,
    ) -> None:
        super().__init__(coordinator, plant)
        self._data_key = data_key
        self._dp_suffix = dp_suffix
        self._inverted = inverted
        self._attr_name = f"Climatix {name}"
        self._attr_unique_id = f"{plant['id']}_{data_key}"
        self._attr_icon = icon

    @property
    def is_on(self) -> bool:
        raw_val = self._plant_data.get(self._data_key)
        if self._inverted:
            return raw_val == 0
        return raw_val == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        target = 0 if self._inverted else 1
        await self.coordinator.async_set_value(
            self._plant_id, self._dp_suffix, target
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        target = 1 if self._inverted else 0
        await self.coordinator.async_set_value(
            self._plant_id, self._dp_suffix, target
        )
        await self.coordinator.async_request_refresh()
