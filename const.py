"""Constants for the Siemens Climatix IC integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "climatix_ic"

# Shared Ocp-Apim-Subscription-Key, as used by the Siemens RDS mobile app.
SUBSCRIPTION_KEY = "2d4b11765cbe430d9728f4c9500bcb2a"

# Cloud API endpoints.
API_BASE = "https://api.climatixic.com"
TOKEN_URL = f"{API_BASE}/Token"
PLANTS_URL = f"{API_BASE}/Plants"
VALUES_URL = f"{API_BASE}/DataPoints/Values"
DATAPOINT_URL = f"{API_BASE}/DataPoints"

# Polling. openHAB's binding allows 8..60s and recommends 60; the shared
# subscription key is rate limited, so we poll conservatively.
DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)
REQUEST_TIMEOUT = 20

MANUFACTURER = "Siemens"
DEFAULT_MODEL = "RDS110"

# Application-set (asn) codes we ask the cloud to return during discovery.
SUPPORTED_ASN = ["RDS110", "RDS120", "RDS110.R", "RDS120.B"]

# Operating-mode datapoint values.
MODE_PROTECTION = 1  # standby ("off")
MODE_COMFORT = 3     # active ("heat")

# Datapoint suffixes for the RDS110 application set ("STH-RDS110").
# These are defined by the Siemens application set and are therefore constant
# across RDS110 units; only the plant-id prefix differs per device. The full
# datapoint id sent to the API is always "<plantId>;<suffix>".
DP_TARGET_SETPOINT = "1!002000083000055"
DP_SETPOINT_OFFSET = "1!002000084000055"
DP_HUMIDITY = "1!002000085000055"
DP_ROOM_TEMP = "1!002000086000055"
DP_OPERATING_MODE = "1!013000051000055"
DP_HEATING_SWITCH = "1!013000052000055"
DP_WATER_SWITCH = "1!013000053000055"

# Logical key -> datapoint suffix. The coordinator polls every suffix here for
# every discovered plant and exposes the result under coordinator.data[plant_id].
DATAPOINTS: dict[str, str] = {
    "target_setpoint": DP_TARGET_SETPOINT,
    "setpoint_offset": DP_SETPOINT_OFFSET,
    "humidity": DP_HUMIDITY,
    "room_temperature": DP_ROOM_TEMP,
    "operating_mode": DP_OPERATING_MODE,
    "heating_switch": DP_HEATING_SWITCH,
    "water_switch": DP_WATER_SWITCH,
}
