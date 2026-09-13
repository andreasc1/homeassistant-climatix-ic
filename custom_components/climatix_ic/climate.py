"""Climate platform for Siemens Climatix IC Thermostat."""

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DP_OPERATING_MODE, DP_TARGET_SETPOINT


async def async_setup_entry(hass, entry, async_add_entities):
  """Set up the Climatix IC climate platform."""
  coordinator = hass.data[DOMAIN][entry.entry_id]
  async_add_entities([ClimatixThermostat(coordinator)])


class ClimatixThermostat(CoordinatorEntity, ClimateEntity):
  """Representation of the Siemens RDS110 Thermostat as a Home Assistant Climate entity."""

  _attr_temperature_unit = UnitOfTemperature.CELSIUS
  _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
  _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
  _attr_min_temp = 6.5
  _attr_max_temp = 35.0
  _attr_target_temperature_step = 0.5

  def __init__(self, coordinator):
    super().__init__(coordinator)
    self._attr_name = "Climatix Thermostat"
    self._attr_unique_id = f"{coordinator.plant_id}_climate"

  @property
  def current_temperature(self) -> float | None:
    """Return the current room temperature."""
    return self.coordinator.data.get("room_temperature")

  @property
  def target_temperature(self) -> float | None:
    """Return the target temperature setpoint."""
    return self.coordinator.data.get("target_setpoint")

  @property
  def current_humidity(self) -> float | None:
    """Return the relative humidity percentage."""
    return self.coordinator.data.get("humidity")

  @property
  def hvac_mode(self) -> HVACMode:
    """Return current HVAC mode (Mode 3 = HEAT, Mode 1 = OFF)."""
    mode = self.coordinator.data.get("operating_mode")
    if mode == 3:
      return HVACMode.HEAT
    return HVACMode.OFF

  async def async_set_temperature(self, **kwargs) -> None:
    """Set new target setpoint temperature via API."""
    if (temp := kwargs.get(ATTR_TEMPERATURE)) is not None:
      await self.hass.async_add_executor_job(
          self.coordinator.set_datapoint, DP_TARGET_SETPOINT, float(temp)
      )
      await self.coordinator.async_request_refresh()

  async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
    """Set HVAC mode (HEAT = Mode 3, OFF = Mode 1)."""
    target_mode = 3 if hvac_mode == HVACMode.HEAT else 1
    await self.hass.async_add_executor_job(
        self.coordinator.set_datapoint, DP_OPERATING_MODE, target_mode
    )
    await self.coordinator.async_request_refresh()