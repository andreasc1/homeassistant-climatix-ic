"""DataUpdateCoordinator for the Siemens Climatix IC cloud API."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DATAPOINTS,
    DATAPOINT_URL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_MODEL,
    DOMAIN,
    PLANTS_URL,
    REQUEST_TIMEOUT,
    SUBSCRIPTION_KEY,
    SUPPORTED_ASN,
    TOKEN_URL,
    VALUES_URL,
)

_LOGGER = logging.getLogger(__name__)

# suffix -> logical key, for decoding responses.
_SUFFIX_TO_KEY = {suffix: key for key, suffix in DATAPOINTS.items()}


class ClimatixAuthError(Exception):
    """Raised when the cloud rejects the credentials."""


class ClimatixApiError(Exception):
    """Raised for connection or unexpected-response errors."""


class ClimatixDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Authenticate, discover plants, and poll datapoint values."""

    def __init__(self, hass: HomeAssistant, username: str, password: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self._username = username
        self._password = password
        self._session = async_get_clientsession(hass)
        self._token: str | None = None
        # Populated by discovery; one entry per thermostat on the account.
        self.plants: list[dict[str, Any]] = []

    # ------------------------------------------------------------------ auth

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
        }

    async def async_authenticate(self) -> None:
        """Obtain an OAuth token. Raises ClimatixAuthError / ClimatixApiError."""
        headers = {
            "Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json, text/plain, */*",
        }
        payload = {
            "grant_type": "password",
            "username": self._username,
            "password": self._password,
        }
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                resp = await self._session.post(
                    TOKEN_URL, headers=headers, data=payload
                )
                if resp.status in (400, 401):
                    raise ClimatixAuthError("Invalid username or password")
                if resp.status != 200:
                    raise ClimatixApiError(f"Auth returned HTTP {resp.status}")
                data = await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise ClimatixApiError(f"Connection error during auth: {err}") from err

        token = data.get("access_token") if isinstance(data, dict) else None
        if not token:
            raise ClimatixAuthError("No access token in response")
        self._token = token

    # -------------------------------------------------------------- requests

    async def _api_get(
        self, url: str, params: dict[str, str] | None = None, _retry: bool = True
    ) -> Any:
        """GET with a single transparent re-auth on 401."""
        if not self._token:
            await self.async_authenticate()
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                resp = await self._session.get(
                    url, headers=self._auth_headers, params=params
                )
                if resp.status == 401 and _retry:
                    self._token = None
                    return await self._api_get(url, params=params, _retry=False)
                if resp.status != 200:
                    text = await resp.text()
                    raise ClimatixApiError(
                        f"GET {url} returned HTTP {resp.status}: {text[:200]}"
                    )
                return await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise ClimatixApiError(f"Connection error: {err}") from err

    async def async_discover_plants(self) -> None:
        """Resolve every RDS thermostat on the account. Never falls back."""
        filter_param = json.dumps(
            [{"asn": asn} for asn in SUPPORTED_ASN] + [{"assigned": True}]
        )
        data = await self._api_get(
            PLANTS_URL,
            params={"filterId": filter_param, "skip": "0", "take": "100"},
        )

        items: list[Any] = []
        if isinstance(data, dict):
            items = data.get("items") or data.get("plants") or []
        elif isinstance(data, list):
            items = data

        plants: list[dict[str, Any]] = []
        for rec in items:
            if not isinstance(rec, dict):
                continue
            plant_id = rec.get("id") or rec.get("plantId")
            if not plant_id:
                continue
            plants.append(
                {
                    "id": plant_id,
                    "name": rec.get("name") or rec.get("serialNumber") or plant_id,
                    "model": rec.get("asn") or DEFAULT_MODEL,
                    "serial": rec.get("serialNumber"),
                    "city": rec.get("city") or "",
                    "sw_version": rec.get("bspVersion") or None,
                }
            )

        if not plants:
            # No device on the account (or the account is not an RDS account).
            raise ClimatixApiError("No RDS thermostats found on this account")

        self.plants = plants

    async def async_set_value(
        self, plant_id: str, suffix: str, value: float | int
    ) -> None:
        """Write a datapoint, with a single re-auth on 401."""
        if not self._token:
            await self.async_authenticate()
        url = f"{DATAPOINT_URL}/{plant_id};{suffix}"
        payload = {"value": value}
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                resp = await self._session.put(
                    url, headers=self._auth_headers, json=payload
                )
                if resp.status == 401:
                    self._token = None
                    await self.async_authenticate()
                    resp = await self._session.put(
                        url, headers=self._auth_headers, json=payload
                    )
                if resp.status not in (200, 204):
                    text = await resp.text()
                    raise ClimatixApiError(
                        f"PUT {url} returned HTTP {resp.status}: {text[:200]}"
                    )
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise ClimatixApiError(f"Error writing datapoint: {err}") from err

    # --------------------------------------------------------------- polling

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            if not self._token:
                await self.async_authenticate()
            if not self.plants:
                await self.async_discover_plants()

            full_ids = [
                f"{plant['id']};{suffix}"
                for plant in self.plants
                for suffix in DATAPOINTS.values()
            ]
            raw = await self._api_get(
                VALUES_URL, params={"filterId": json.dumps(full_ids)}
            )
        except ClimatixAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except ClimatixApiError as err:
            raise UpdateFailed(str(err)) from err

        values = raw.get("values", {}) if isinstance(raw, dict) else {}
        result: dict[str, dict[str, Any]] = {
            plant["id"]: {"_bounds": {}} for plant in self.plants
        }

        for full_id, entry in values.items():
            if ";" not in full_id:
                continue
            plant_id, suffix = full_id.split(";", 1)
            key = _SUFFIX_TO_KEY.get(suffix)
            if key is None or plant_id not in result:
                continue

            inner = entry.get("value") if isinstance(entry, dict) else entry
            if isinstance(inner, dict):
                val = inner.get("value")
                lo, hi = inner.get("minValue"), inner.get("maxValue")
                if lo is not None and hi is not None:
                    result[plant_id]["_bounds"][key] = (lo, hi)
            else:
                val = inner

            if isinstance(val, float):
                val = round(val, 2)
            result[plant_id][key] = val

        return result
