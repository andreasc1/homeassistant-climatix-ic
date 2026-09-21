"""Sensor platform for the Siemens Climatix IC thermostat."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ClimatixDataUpdateCoordinator
from .entity import ClimatixEntity


@dataclass(frozen=True, kw_only=True)
class ClimatixSensorDescription(SensorEntityDescription):
    """Describes a Climatix sensor and the coordinator key it reads."""

    data_key: str


SENSOR_DESCRIPTIONS: tuple[ClimatixSensorDescription, ...] = (
    ClimatixSensorDescription(
        key="room_temperature",
        data_key="room_temperature",
        name="Climatix Room Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
    ),
    ClimatixSensorDescription(
        key="humidity",
        data_key="humidity",
        name="Climatix Relative Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
    ),
    ClimatixSensorDescription(
        key="target_setpoint",
        data_key="target_setpoint",
        name="Climatix Target Setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
    ),
    ClimatixSensorDescription(
        key="setpoint_offset",
        data_key="setpoint_offset",
        name="Climatix Setpoint Offset",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
    ),
    ClimatixSensorDescription(
        key="operating_mode",
        data_key="operating_mode",
        name="Climatix Operating Mode",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor entities for every discovered thermostat."""
    coordinator: ClimatixDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        ClimatixSensor(coordinator, plant, description)
        for plant in coordinator.plants
        for description in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


class ClimatixSensor(ClimatixEntity, SensorEntity):
    """A single read-only datapoint exposed as a sensor."""

    entity_description: ClimatixSensorDescription

    def __init__(
        self,
        coordinator: ClimatixDataUpdateCoordinator,
        plant: dict[str, Any],
        description: ClimatixSensorDescription,
    ) -> None:
        super().__init__(coordinator, plant)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{plant['id']}_{description.key}"

    @property
    def native_value(self) -> Any:
        return self._plant_data.get(self.entity_description.data_key)
