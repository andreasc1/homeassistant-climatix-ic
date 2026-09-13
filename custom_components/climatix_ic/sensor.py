"""Sensors platform for Climatix IC."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
  coordinator = hass.data[DOMAIN][entry.entry_id]

  sensors = [
      ClimatixSensor(
          coordinator,
          "room_temperature",
          "Room Temperature",
          UnitOfTemperature.CELSIUS,
          SensorDeviceClass.TEMPERATURE,
      ),
      ClimatixSensor(
          coordinator,
          "target_setpoint",
          "Target Setpoint",
          UnitOfTemperature.CELSIUS,
          SensorDeviceClass.TEMPERATURE,
      ),
      ClimatixSensor(
          coordinator,
          "setpoint_offset",
          "Setpoint Offset",
          UnitOfTemperature.CELSIUS,
          SensorDeviceClass.TEMPERATURE,
      ),
      ClimatixSensor(
          coordinator,
          "humidity",
          "Relative Humidity",
          PERCENTAGE,
          SensorDeviceClass.HUMIDITY,
      ),
      ClimatixSensor(coordinator, "operating_mode", "Operating Mode", None, None),
  ]

  async_add_entities(sensors)


class ClimatixSensor(CoordinatorEntity, SensorEntity):

  def __init__(self, coordinator, key, name, unit, device_class):
    super().__init__(coordinator)
    self.key = key
    self._attr_name = f"Climatix {name}"
    self._attr_unique_id = f"{coordinator.plant_id}_{key}"
    self._attr_native_unit_of_measurement = unit
    self._attr_device_class = device_class
    if device_class:
      self._attr_state_class = SensorStateClass.MEASUREMENT

  @property
  def native_value(self):
    return self.coordinator.data.get(self.key)