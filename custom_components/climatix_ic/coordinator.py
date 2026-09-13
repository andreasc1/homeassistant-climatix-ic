"""DataUpdateCoordinator for Climatix IC API."""

from datetime import timedelta
import json
import logging
import requests

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    DP_HEATING_SWITCH,
    DP_HUMIDITY,
    DP_OPERATING_MODE,
    DP_ROOM_TEMP,
    DP_SETPOINT_OFFSET,
    DP_TARGET_SETPOINT,
    DP_WATER_SWITCH,
    SUBSCRIPTION_KEY,
)

_LOGGER = logging.getLogger(__name__)

FALLBACK_PLANT_ID = "P55c454e2-d8ae-4f95-8991-d818d5c5d1b7"


class ClimatixDataUpdateCoordinator(DataUpdateCoordinator):
  """Coordinator for fetching and discovering Climatix IC endpoints."""

  def __init__(self, hass: HomeAssistant, username: str, password: str) -> None:
    super().__init__(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_interval=timedelta(seconds=15),  # Faster polling for testing
    )
    self.username = username
    self.password = password
    self.plant_id = None
    self.token = None
    self.headers = {}

  def authenticate_and_discover(self) -> None:
    """Authenticate and dynamically resolve Plant ID."""
    url = "https://api.climatixic.com/Token"
    headers = {
        "Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*",
    }
    payload = {
        "grant_type": "password",
        "username": self.username,
        "password": self.password,
    }

    res = requests.post(url, headers=headers, data=payload, timeout=12)
    if res.status_code in (400, 401):
      raise ConfigEntryAuthFailed("Invalid username or password")
    res.raise_for_status()

    data = res.json()
    self.token = data.get("access_token") if isinstance(data, dict) else data

    self.headers = {
        "Authorization": f"Bearer {self.token}",
        "Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
    }

    filter_param = json.dumps([
        {"asn": "RDS110"},
        {"asn": "RDS120"},
        {"asn": "RDS110.R"},
        {"asn": "RDS120.B"},
        {"assigned": True},
    ])
    plants_url = f"https://api.climatixic.com/Plants?filterId={filter_param}&skip=0&take=100"

    try:
      plants_res = requests.get(plants_url, headers=self.headers, timeout=12)
      plants_res.raise_for_status()
      plants_data = plants_res.json()

      plant_items = (
          plants_data
          if isinstance(plants_data, list)
          else plants_data.get("plants", [])
      )

      if plant_items:
        first = plant_items[0]
        self.plant_id = (
            first.get("id")
            or first.get("plantId")
            or first.get("asn")
            or first.get("name")
        )
      else:
        self.plant_id = FALLBACK_PLANT_ID

    except Exception:
      self.plant_id = FALLBACK_PLANT_ID

  async def _async_update_data(self) -> dict:
    return await self.hass.async_add_executor_job(self._fetch_data)

  def _fetch_data(self) -> dict:
    if not self.token or not self.plant_id:
      self.authenticate_and_discover()

    dp_suffixes = [
        DP_TARGET_SETPOINT,
        DP_SETPOINT_OFFSET,
        DP_HUMIDITY,
        DP_ROOM_TEMP,
        DP_OPERATING_MODE,
        DP_HEATING_SWITCH,
        DP_WATER_SWITCH,
    ]
    filter_list = [f"{self.plant_id};{suffix}" for suffix in dp_suffixes]
    endpoint = f"https://api.climatixic.com/DataPoints/Values?filterId={json.dumps(filter_list)}"

    try:
      res = requests.get(endpoint, headers=self.headers, timeout=12)
      if res.status_code == 401:
        self.authenticate_and_discover()
        res = requests.get(endpoint, headers=self.headers, timeout=12)
      res.raise_for_status()
    except Exception as err:
      raise UpdateFailed(f"Error communicating with Climatix IC API: {err}") from err

    raw_data = res.json()
    parsed = {}
    values_dict = raw_data.get("values", {})

    for dp_id, dp_data in values_dict.items():
      inner = dp_data.get("value", {})
      val = inner.get("value") if isinstance(inner, dict) else inner
      if isinstance(val, float):
        val = round(val, 2)

      if DP_TARGET_SETPOINT in dp_id:
        parsed["target_setpoint"] = val
      elif DP_SETPOINT_OFFSET in dp_id:
        parsed["setpoint_offset"] = val
      elif DP_HUMIDITY in dp_id:
        parsed["humidity"] = val
      elif DP_ROOM_TEMP in dp_id:
        parsed["room_temperature"] = val
      elif DP_OPERATING_MODE in dp_id:
        parsed["operating_mode"] = val
      elif DP_HEATING_SWITCH in dp_id:
        parsed["heating_switch"] = val
      elif DP_WATER_SWITCH in dp_id:
        parsed["water_switch"] = val

    return parsed

  def set_datapoint(self, dp_suffix: str, value: float) -> None:
    if not self.token or not self.plant_id:
      self.authenticate_and_discover()

    dp_id = f"{self.plant_id};{dp_suffix}"
    endpoint = f"https://api.climatixic.com/DataPoints/{dp_id}"
    payload = {"value": value}

    res = requests.put(
        endpoint, headers=self.headers, json=payload, timeout=12
    )
    if res.status_code == 401:
      self.authenticate_and_discover()
      res = requests.put(
          endpoint, headers=self.headers, json=payload, timeout=12
      )
    res.raise_for_status()