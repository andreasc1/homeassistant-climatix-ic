"""Switches for Climatix IC (Main Thermostat Power, Hot Water, Space Heating)."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DP_HEATING_SWITCH, DP_OPERATING_MODE, DP_WATER_SWITCH


async def async_setup_entry(hass, entry, async_add_entities):
  coordinator = hass.data[DOMAIN][entry.entry_id]
  async_add_entities([
      ClimatixPowerSwitch(coordinator),
      ClimatixZoneSwitch(
          coordinator,
          "water_switch",
          "Hot Water Heater",
          DP_WATER_SWITCH,
          "mdi:water-boiler",
          inverted=True,  # 0 = ON, 1 = OFF
      ),
      ClimatixZoneSwitch(
          coordinator,
          "heating_switch",
          "Space Heating",
          DP_HEATING_SWITCH,
          "mdi:radiator",
          inverted=False,  # 1 = ON, 0 = OFF
      ),
  ])


class ClimatixPowerSwitch(CoordinatorEntity, SwitchEntity):
  """Main Thermostat Power Switch (Comfort Mode 3 vs Protection Mode 1)."""

  def __init__(self, coordinator):
    super().__init__(coordinator)
    self._attr_name = "Climatix Thermostat Power"
    self._attr_unique_id = f"{coordinator.plant_id}_thermostat_power"
    self._attr_icon = "mdi:power"

  @property
  def is_on(self) -> bool:
    return self.coordinator.data.get("operating_mode") == 3

  async def async_turn_on(self, **kwargs) -> None:
    await self.hass.async_add_executor_job(
        self.coordinator.set_datapoint, DP_OPERATING_MODE, 3
    )
    await self.coordinator.async_request_refresh()

  async def async_turn_off(self, **kwargs) -> None:
    await self.hass.async_add_executor_job(
        self.coordinator.set_datapoint, DP_OPERATING_MODE, 1
    )
    await self.coordinator.async_request_refresh()


class ClimatixZoneSwitch(CoordinatorEntity, SwitchEntity):

  def __init__(
      self, coordinator, data_key, name, dp_suffix, icon, inverted=False
  ):
    super().__init__(coordinator)
    self.data_key = data_key
    self.dp_suffix = dp_suffix
    self.inverted = inverted
    self._attr_name = f"Climatix {name}"
    self._attr_unique_id = f"{coordinator.plant_id}_{data_key}"
    self._attr_icon = icon

  @property
  def is_on(self) -> bool:
    raw_val = self.coordinator.data.get(self.data_key)
    if self.inverted:
      return raw_val == 0
    return raw_val == 1

  async def async_turn_on(self, **kwargs) -> None:
    target_val = 0 if self.inverted else 1
    await self.hass.async_add_executor_job(
        self.coordinator.set_datapoint, self.dp_suffix, target_val
    )
    await self.coordinator.async_request_refresh()

  async def async_turn_off(self, **kwargs) -> None:
    target_val = 1 if self.inverted else 0
    await self.hass.async_add_executor_job(
        self.coordinator.set_datapoint, self.dp_suffix, target_val
    )
    await self.coordinator.async_request_refresh()