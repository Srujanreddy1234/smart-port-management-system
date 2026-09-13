# DATASETS CATALOG — Smart Port Management System (Thoothukudi/V.O. Chidambaranar Port)

This catalog lists every dataset that is **100% needed and fully useful** for this project.
Each dataset maps directly to one or more data models in the backend (`backend/app/models/`).
Datasets not used by the project are intentionally excluded.

> **Actual integration status (see `README.md` and `processed/import_manifest.json`
> for current numbers):** only *some* years of each dataset are actually imported
> into the database -- not every year listed below turned out to be usable. In
> particular:
> - Air quality: only 2023-2025 are imported (2018-2021 are empty, 2022 is ~41%
>   populated in the downloaded data).
> - Marine data feeds a real `MarineReading` model and a "sea conditions" read
>   path, but it does **not** feed `Berth.can_accommodate()` -- that method only
>   compares static ship/berth dimensions and was never changed to use marine
>   data, despite the claim below when this catalog was first written.
> - Port traffic statistics are surfaced as a small **read-only annual
>   reference table** (`/api/v1/reports/port-traffic-annual`) on the Reports
>   page. They do **not** feed the Ship/Container models, dashboard charts, or
>   "vessel_type filter" as originally claimed below -- six annual rows are far
>   too coarse for that, and doing so would have meant fabricating daily/hourly
>   figures from an annual number.

---

## 0. Port Location (used by all API-based datasets)

| Field    | Value                                  |
|----------|----------------------------------------|
| Port     | V.O. Chidambaranar Port (Tuticorin)    |
| Latitude | 8.75°N                                 |
| Longitude| 78.20°E                                |
| Country  | India                                  |
| State    | Tamil Nadu                             |

---

## 1. Historical Weather Data (2018-01-01 → present)

| Attribute       | Detail                                                                 |
|-----------------|------------------------------------------------------------------------|
| **Source**      | Open-Meteo Historical Weather API (ERA5 reanalysis)                    |
| **API URL**     | `https://archive-api.open-meteo.com/v1/archive`                        |
| **Time range**  | 2018-01-01 → present (~7 years)                                        |
| **Resolution**  | Hourly                                                                 |
| **License**     | CC-BY 4.0 (free for commercial use with attribution)                   |
| **Script**      | `scripts/download_weather_data.py`                                     |
| **Output**      | `raw/weather/weather_YYYY.csv` (one CSV per year)                      |
| **Project Model**| `backend/app/models/environment.py` → `WeatherReading`               |

### Variables fetched → model field mapping

| Open-Meteo variable        | Unit  | WeatherReading field        |
|----------------------------|-------|-----------------------------|
| temperature_2m             | °C    | temperature                 |
| apparent_temperature        | °C    | feels_like                  |
| relative_humidity_2m       | %     | humidity                    |
| wind_speed_10m             | km/h  | wind_speed (converted m/s)  |
| wind_direction_10m         | °     | wind_direction              |
| wind_gusts_10m             | km/h  | wind_gust (converted m/s)   |
| pressure_msl               | hPa   | pressure                    |
| precipitation              | mm    | precipitation               |
| cloud_cover                | %     | cloud_cover                 |
| dew_point_2m               | °C    | dew_point                   |
| shortwave_radiation        | W/m²  | solar_radiation             |
| uv_index (from air-quality API) | index | uv_index              |
| (derived from apparent_temperature) | °C | heat_index             |
| (derived from wind/temp)   | °C    | wind_chill                  |
| (derived from weather_code)| text  | weather_condition           |
| (derived from weather_code)| text  | weather_description        |

> **Why 100% needed:** The `environment.html` page, the dashboard weather
> widget, and the `WeatherReading` model all require real meteorological data.

---

## 2. Air Quality Data (2018-01-01 → present)

| Attribute       | Detail                                                                 |
|-----------------|------------------------------------------------------------------------|
| **Source**      | Open-Meteo Air Quality API (CAMS European air quality)                |
| **API URL**     | `https://air-quality-api.open-meteo.com/v1/air-quality`               |
| **Time range**  | 2018-01-01 → present (~7 years)                                        |
| **Resolution**  | Hourly                                                                 |
| **License**     | CC-BY 4.0 (free with attribution to CAMS)                              |
| **Script**      | `scripts/download_air_quality_data.py`                                 |
| **Output**      | `raw/air_quality/air_quality_YYYY.csv` (one CSV per year)             |
| **Project Model**| `backend/app/models/environment.py` → `AirQualityReading`           |

### Variables fetched → model field mapping

| Open-Meteo variable | Unit  | AirQualityReading field |
|---------------------|-------|--------------------------|
| us_aqi              | index | aqi                      |
| (derived from AQI)  | text  | aqi_category             |
| pm2_5               | µg/m³ | pm25                     |
| pm10                | µg/m³ | pm10                     |
| nitrogen_dioxide    | µg/m³ | no2                      |
| sulphur_dioxide     | µg/m³ | so2                      |
| carbon_monoxide     | µg/m³ | co                       |
| ozone               | µg/m³ | o3                       |
| ammonia             | µg/m³ | nh3                      |

> **Why 100% needed:** The `environment.html` page has a dedicated Air Quality

---

## 3. Marine / Oceanographic Data (2022-01-01 → present)

| Attribute       | Detail                                                                 |
|-----------------|------------------------------------------------------------------------|
| **Source**      | Open-Meteo Marine Weather API                                         |
| **API URL**     | `https://marine-api.open-meteo.com/v1/marine`                         |
| **Time range**  | 2022-01-01 → present (~3 years; older dates return null)              |
| **Resolution**  | Hourly                                                                 |
| **License**     | CC-BY 4.0                                                             |
| **Script**      | `scripts/download_marine_data.py`                                      |
| **Output**      | `raw/marine/marine_YYYY.csv`                                          |
| **Project Model**| Used by berth operations, vessel approach monitoring                  |

### Variables fetched

| Open-Meteo variable       | Unit | Use in project                         |
|---------------------------|------|----------------------------------------|
| wave_height               | m    | Vessel approach safety, berth ops      |
| wave_direction            | °    | Navigation safety                      |
| wave_period               | s    | Vessel scheduling                      |
| sea_surface_temperature   | °C   | Environmental monitoring               |
| sea_level_height_msl      | m    | Tide / berth draft clearance           |

> **Why 100% needed:** Wave height and sea level directly affect vessel
> berthing decisions (the `berths.html` page and `Berth.can_accommodate()`
> logic). Note: only available from ~2022; older years return null.
> section and the dashboard KPI shows the latest AQI value. This is the only
> public source providing all these pollutants for Tuticorin.

---

## 4. Port Traffic Statistics — V.O. Chidambaranar Port (2018-2024)

| Attribute       | Detail                                                                 |
|-----------------|------------------------------------------------------------------------|
| **Source**      | Indian Ports Association (IPA), Ministry of Ports/Shipping/Waterways,  |
|                 | V.O. Chidambaranar Port Authority Annual Reports                      |
| **Web sources** | https://www.ipa.nic.in (traffic statistics)                           |
|                 | https://www.vocport.gov.in (annual reports)                           |
|                 | https://ship.gov.in (Ministry statistics)                             |
| **Time range**  | 2018-19 → 2023-24 (6 fiscal years)                                     |
| **Format**      | CSV (compiled from public annual reports)                              |
| **File**        | `raw/port_traffic/port_traffic_statistics.csv`                        |
| **Project Models**| `backend/app/models/ship.py` → `Ship`, `Berth`                      |
|                 | `backend/app/models/container.py` → `Container`                      |
|                 | `backend/app/api/dashboard.py` → KPIs, charts                         |
|                 | `backend/app/api/reports.py` → ship-traffic, container-throughput     |

### Data fields

| Field                  | Unit        | Project use                                        |
|------------------------|-------------|----------------------------------------------------|
| fiscal_year            | FY          | Reports date range, dashboard time axis            |
| total_cargo_mmt       | Million T   | Dashboard throughput chart                         |
| container_teu         | TEU         | Container throughput report, container charts     |
| vessel_calls          | count       | Vessel arrivals chart, ship stats                 |
| container_vessels     | count       | Ship model vessel_type filter                     |
| bulk_carrier_vessels  | count       | Ship model vessel_type filter                     |
| tanker_vessels        | count       | Ship model vessel_type filter                     |
| general_cargo_vessels | count       | Ship model vessel_type filter                     |
| avg_berth_occupancy_pct | %         | Berth occupancy chart                              |
| avg_pre_berthing_delay_hrs | hours   | Reports, dashboard KPI                            |
| avg_turnaround_time_hrs | hours     | Reports, vessel status                            |
| avg_output_per_ship_berth_day_t | T  | Reports, performance metrics                       |

> **Why 100% needed:** These are the foundational traffic statistics that
> populate the dashboard charts and report types. Without this, the Reports
> API and Dashboard charts would have no reference baseline.
