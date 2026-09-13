# Siemens Climatix IC (RDS110) for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/andreasc1/homeassistant-climatix-ic?style=flat-slate)](https://github.com/andreasc1/homeassistant-climatix-ic/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Custom Home Assistant integration for controlling the **Siemens RDS110 Smart Thermostat** via the Siemens Climatix IC cloud platform. 

---

## 🚀 Easy Installation via HACS

Click the button below to add this repository directly to your HACS Custom Repositories:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?target=andreasc1%2Fhomeassistant-climatix-ic&category=integration)

*(Or follow the manual HACS steps below)*

---

## 📌 Features & Functions

- **Native Climate Control (`climate.climatix_thermostat`)**:
  - Direct target setpoint adjustments ($6.5^\circ\text{C}$ – $35.0^\circ\text{C}$).
  - Full HVAC mode switching: **HEAT** (Comfort Mode / `3`) and **OFF** (Protection Mode / `1`).
  - Real-time room temperature and humidity tracking.
- **Dual Zone Switch Control**:
  - **Zone 1 (Hot Water)**: Independent switch control with integrated inverted logic handling.
  - **Zone 2 (Space Heating)**: Independent relay state switch.
- **Main Power Switch**: Toggle the thermostat between active Comfort Mode and standby Protection Mode.
- **Dynamic Plant ID & Token Management**: Auto-discovers account resources and handles OAuth token renewals under the hood without hardcoded user IDs.

---

## 📊 Exposed Entities

| Entity ID | Name | Type | Description |
| :--- | :--- | :--- | :--- |
| `climate.climatix_thermostat` | Climatix Thermostat | Climate | Full setpoint and HVAC mode control |
| `switch.climatix_thermostat_power` | Climatix Thermostat Power | Switch | Toggle between Comfort (ON) and Protection (OFF) |
| `switch.climatix_hot_water_heater` | Climatix Hot Water Heater | Switch | Zone 1 Hot Water Relay (Inverted Logic) |
| `switch.climatix_space_heating` | Climatix Space Heating | Switch | Zone 2 Space Heating Relay |
| `sensor.climatix_room_temperature` | Climatix Room Temperature | Sensor | Current ambient temperature ($^\circ\text{C}$) |
| `sensor.climatix_target_setpoint` | Climatix Target Setpoint | Sensor | Current target temperature setpoint ($^\circ\text{C}$) |
| `sensor.climatix_relative_humidity` | Climatix Relative Humidity | Sensor | Current relative humidity percentage ($\%$) |
| `sensor.climatix_setpoint_offset` | Climatix Setpoint Offset | Sensor | Setpoint offset measurement ($^\circ\text{C}$) |
| `sensor.climatix_operating_mode` | Climatix Operating Mode | Sensor | Raw operating mode state (`3` = Comfort, `1` = Off) |

---

## 🛠️ Installation

### Method 1: HACS (Recommended)

1. Open **HACS** in your Home Assistant sidebar.
2. Click the three dots **`⋮`** in the top-right corner and select **Custom repositories**.
3. Enter `https://github.com/andreasc1/homeassistant-climatix-ic` into the Repository URL field.
4. Select **Integration** as the Category and click **Add**.
5. Click **Download** on the Siemens Climatix IC card.
6. **Restart Home Assistant**.

### Method 2: Manual Copy

1. Download the latest source archive from the [Releases](https://github.com/andreasc1/homeassistant-climatix-ic/releases) page.
2. Copy the `climatix_ic` folder into your Home Assistant installation directory under `/config/custom_components/`.
3. **Restart Home Assistant**.

---

## ⚙️ Setup & Configuration

1. Go to **Settings** $\rightarrow$ **Devices & Services**.
2. Click **Add Integration** (bottom right).
3. Search for **Siemens Climatix IC RDS110**.
4. Enter your Climatix IC **Email Address** and **Password**.
5. Click **Submit**.

---

## 🎨 Recommended Dashboard UI Card

![Siemens Climatix Dashboard Card](./dashboard_card.png)

Add this compact grid control card to your Lovelace dashboard via **Edit Dashboard** $\rightarrow$ **Add Card** $\rightarrow$ **Manual**:

```yaml
type: grid
columns: 1
square: false
cards:
  - type: thermostat
    entity: climate.climatix_thermostat

  - type: grid
    columns: 2
    square: false
    cards:
      - type: button
        entity: switch.climatix_hot_water_heater
        name: Hot Water
        icon: mdi:water-boiler
        show_state: true
        tap_action:
          action: toggle

      - type: button
        entity: switch.climatix_thermostat_power
        name: Power Mode
        icon: mdi:power
        show_state: true
        tap_action:
          action: toggle

  - type: glance
    entities:
      - entity: sensor.climatix_room_temperature
        name: Room Temp
      - entity: sensor.climatix_relative_humidity
        name: Humidity
      - entity: sensor.climatix_target_setpoint
        name: Target
