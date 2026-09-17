#!/usr/bin/env python3
"""
Import real historical environmental datasets into the Smart Port Management
System database.

This replaces the old datasets/scripts/import_all_data.py, which had drifted
out of sync with the current model schema (field names, enum values) and
never actually wrote marine or port-traffic data anywhere.

Only years with genuinely complete data are imported -- see DATASETS_CATALOG.md
and the per-source notes below for why each window was chosen. This script
is idempotent: re-running it clears and re-imports each dataset rather than
appending duplicates.

Run from the backend directory (so the app config / DATABASE_URL are picked
up correctly):
    cd backend && python ../datasets/scripts/import_to_database.py
"""

import os
import sys
import csv
import glob
import json
from datetime import datetime

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "backend")
sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault("FLASK_ENV", "development")

from app import create_app
from app.extensions import db
from app.models import (
    MonitoringStation, WeatherReading, AirQualityReading, MarineReading, PortTrafficAnnual
)

DATASETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# Only these years are imported per source -- chosen from the actual
# completeness of the downloaded data (see DATASETS_CATALOG.md):
#   weather:     ERA5 reanalysis is fully populated for every downloaded year;
#                a 6-year window is imported (2020-2025).
#   air_quality: CAMS reanalysis has NO data for 2018-2021 and only ~41%
#                coverage for 2022 in this dataset -- those years are
#                deliberately excluded rather than imported as if complete.
#                Only 2023-2025 (fully populated) are imported.
#   marine:      wave height/direction/period are populated from 2022 onward;
#                sea-surface-temp/sea-level are partially null in 2022-2023
#                (imported as NULL, not fabricated). All 4 available years
#                (2022-2025) are imported.
#   2026 is a partial (in-progress) year for weather/air_quality -- the
#   download scripts cap it at "today" rather than Dec 31, so it's imported
#   like any other year and simply has fewer hours than a full year.
WEATHER_YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]
AIR_QUALITY_YEARS = [2023, 2024, 2025, 2026]
MARINE_YEARS = [2022, 2023, 2024, 2025]


def parse_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def get_or_create_station(station_id, name, station_type, zone):
    station = MonitoringStation.query.filter_by(station_id=station_id).first()
    if not station:
        station = MonitoringStation(
            station_id=station_id,
            name=name,
            station_type=station_type,
            latitude=8.75,
            longitude=78.20,
            zone=zone,
            address="V.O. Chidambaranar Port, Thoothukudi, Tamil Nadu",
            is_active=True,
        )
        db.session.add(station)
        db.session.commit()
        print(f"  Created station: {station.name} (id={station.id})")
    return station


def import_weather(station_id):
    # The old synthetic seed script attached a fake WeatherReading to every
    # monitoring station regardless of type, so clear the whole table (100%
    # of existing rows are that fake data) rather than scoping by station_id.
    db.session.query(WeatherReading).delete()
    db.session.commit()

    total = 0
    for year in WEATHER_YEARS:
        path = os.path.join(DATASETS_DIR, "raw", "weather", f"weather_{year}.csv")
        if not os.path.exists(path):
            print(f"  [weather] {year}: file not found, skipping")
            continue
        batch = []
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                batch.append(WeatherReading(
                    station_id=station_id,
                    recorded_at=datetime.fromisoformat(row["recorded_at"]),
                    temperature=parse_float(row["temperature"]),
                    feels_like=parse_float(row["feels_like"]),
                    humidity=parse_float(row["humidity"]),
                    wind_speed=parse_float(row["wind_speed"]),
                    wind_direction=parse_float(row["wind_direction"]),
                    wind_gust=parse_float(row["wind_gust"]),
                    pressure=parse_float(row["pressure"]),
                    precipitation=parse_float(row["precipitation"]),
                    visibility=parse_float(row["visibility"]),
                    uv_index=parse_float(row["uv_index"]),
                    dew_point=parse_float(row["dew_point"]),
                    heat_index=parse_float(row["heat_index"]),
                    wind_chill=parse_float(row["wind_chill"]),
                    cloud_cover=parse_float(row["cloud_cover"]),
                    solar_radiation=parse_float(row["solar_radiation"]),
                    weather_condition=row["weather_condition"] or None,
                    weather_description=row["weather_description"] or None,
                ))
                if len(batch) >= 1000:
                    db.session.bulk_save_objects(batch)
                    db.session.commit()
                    total += len(batch)
                    batch = []
        if batch:
            db.session.bulk_save_objects(batch)
            db.session.commit()
            total += len(batch)
        print(f"  [weather] {year}: imported")
    return total


def import_air_quality(station_id):
    # Same reasoning as import_weather(): clear all existing (fake) rows.
    db.session.query(AirQualityReading).delete()
    db.session.commit()

    total = 0
    for year in AIR_QUALITY_YEARS:
        path = os.path.join(DATASETS_DIR, "raw", "air_quality", f"air_quality_{year}.csv")
        if not os.path.exists(path):
            print(f"  [air_quality] {year}: file not found, skipping")
            continue
        batch = []
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                if not row["aqi"]:
                    continue  # defensive: skip any residual empty rows even within a "good" year
                batch.append(AirQualityReading(
                    station_id=station_id,
                    recorded_at=datetime.fromisoformat(row["recorded_at"]),
                    aqi=int(float(row["aqi"])),
                    aqi_category=row["aqi_category"] or None,
                    pm25=parse_float(row["pm25"]),
                    pm10=parse_float(row["pm10"]),
                    no2=parse_float(row["no2"]),
                    so2=parse_float(row["so2"]),
                    co=parse_float(row["co"]),
                    o3=parse_float(row["o3"]),
                    nh3=parse_float(row["nh3"]),
                    temperature=parse_float(row["temperature"]),
                    humidity=parse_float(row["humidity"]),
                    wind_speed=parse_float(row["wind_speed"]),
                    wind_direction=parse_float(row["wind_direction"]),
                    pressure=parse_float(row["pressure"]),
                ))
                if len(batch) >= 1000:
                    db.session.bulk_save_objects(batch)
                    db.session.commit()
                    total += len(batch)
                    batch = []
        if batch:
            db.session.bulk_save_objects(batch)
            db.session.commit()
            total += len(batch)
        print(f"  [air_quality] {year}: imported")
    return total


def import_marine(station_id):
    db.session.query(MarineReading).filter_by(station_id=station_id).delete()
    db.session.commit()

    total = 0
    for year in MARINE_YEARS:
        path = os.path.join(DATASETS_DIR, "raw", "marine", f"marine_{year}.csv")
        if not os.path.exists(path):
            print(f"  [marine] {year}: file not found, skipping")
            continue
        batch = []
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                batch.append(MarineReading(
                    station_id=station_id,
                    recorded_at=datetime.fromisoformat(row["recorded_at"]),
                    wave_height_m=parse_float(row["wave_height_m"]),
                    wave_direction_deg=parse_float(row["wave_direction_deg"]),
                    wave_period_s=parse_float(row["wave_period_s"]),
                    sea_surface_temp_c=parse_float(row["sea_surface_temp_c"]),
                    sea_level_height_msl_m=parse_float(row["sea_level_height_msl_m"]),
                ))
                if len(batch) >= 1000:
                    db.session.bulk_save_objects(batch)
                    db.session.commit()
                    total += len(batch)
                    batch = []
        if batch:
            db.session.bulk_save_objects(batch)
            db.session.commit()
            total += len(batch)
        print(f"  [marine] {year}: imported")
    return total


def import_port_traffic():
    path = os.path.join(DATASETS_DIR, "raw", "port_traffic", "port_traffic_statistics.csv")
    if not os.path.exists(path):
        print("  [port_traffic] file not found, skipping")
        return 0

    count = 0
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            existing = PortTrafficAnnual.query.filter_by(fiscal_year=row["fiscal_year"]).first()
            values = dict(
                total_cargo_mmt=parse_float(row["total_cargo_mmt"]),
                container_teu=int(row["container_teu"]) if row["container_teu"] else None,
                vessel_calls=int(row["vessel_calls"]) if row["vessel_calls"] else None,
                container_vessels=int(row["container_vessels"]) if row["container_vessels"] else None,
                bulk_carrier_vessels=int(row["bulk_carrier_vessels"]) if row["bulk_carrier_vessels"] else None,
                tanker_vessels=int(row["tanker_vessels"]) if row["tanker_vessels"] else None,
                general_cargo_vessels=int(row["general_cargo_vessels"]) if row["general_cargo_vessels"] else None,
                avg_berth_occupancy_pct=parse_float(row["avg_berth_occupancy_pct"]),
                avg_pre_berthing_delay_hrs=parse_float(row["avg_pre_berthing_delay_hrs"]),
                avg_turnaround_time_hrs=parse_float(row["avg_turnaround_time_hrs"]),
                avg_output_per_ship_berth_day_t=parse_float(row["avg_output_per_ship_berth_day_t"]),
            )
            if existing:
                for key, value in values.items():
                    setattr(existing, key, value)
            else:
                db.session.add(PortTrafficAnnual(fiscal_year=row["fiscal_year"], **values))
            count += 1
    db.session.commit()
    print(f"  [port_traffic] {count} fiscal years imported/updated")
    return count


def write_manifest(weather_count, aq_count, marine_count, traffic_count):
    manifest = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "sources": {
            "weather": {
                "years_imported": WEATHER_YEARS,
                "years_excluded": [],
                "exclusion_reason": None,
                "records_imported": weather_count,
                "model": "WeatherReading",
                "station": "MS-004",
                "notes": "ERA5 reanalysis via Open-Meteo; fully populated for every downloaded year (2020-2025), plus the current in-progress year (2026, partial through today).",
            },
            "air_quality": {
                "years_imported": AIR_QUALITY_YEARS,
                "years_excluded": [2018, 2019, 2020, 2021, 2022],
                "exclusion_reason": "2018-2021 have 0% AQI coverage in the downloaded CAMS reanalysis data; 2022 has only ~41% coverage (3,571/8,760 hours). Importing partial years would misrepresent them as complete, so only the fully-populated years are loaded.",
                "records_imported": aq_count,
                "model": "AirQualityReading",
                "station": "MS-001",
            },
            "marine": {
                "years_imported": MARINE_YEARS,
                "years_excluded": [],
                "exclusion_reason": None,
                "records_imported": marine_count,
                "model": "MarineReading",
                "station": "MS-005",
                "notes": "Wave height/direction/period are populated from 2022 onward. sea_surface_temp_c and sea_level_height_msl_m are partially null in 2022-2023 (Open-Meteo Marine API backfill limitation) -- imported as NULL, not fabricated.",
            },
            "port_traffic": {
                "years_imported": "FY2018-19 through FY2023-24 (6 fiscal years)",
                "records_imported": traffic_count,
                "model": "PortTrafficAnnual",
                "notes": "Annual aggregate statistics only (Indian Ports Association / port authority reports). Deliberately NOT used to derive any daily/hourly figure -- too coarse for that.",
            },
        },
    }
    out_path = os.path.join(DATASETS_DIR, "processed", "import_manifest.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    # Preserve any keys this run doesn't produce (e.g. "storage_audit", a
    # point-in-time measurement recorded manually against production) --
    # re-running this script to pick up a new year's data shouldn't
    # silently erase that record.
    if os.path.exists(out_path):
        try:
            with open(out_path) as f:
                existing = json.load(f)
            for key, value in existing.items():
                manifest.setdefault(key, value)
        except (json.JSONDecodeError, OSError):
            pass
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest written to {out_path}")


def main():
    print("=" * 60)
    print("Smart Port Management System - Real Historical Data Import")
    print("=" * 60)

    app = create_app(os.environ.get("FLASK_ENV", "development"))
    with app.app_context():
        weather_station = get_or_create_station("MS-004", "Weather Station", "weather", "Central")
        aq_station = get_or_create_station("MS-001", "Main Terminal AQ Monitor", "air_quality", "Terminal 1")
        marine_station = get_or_create_station("MS-005", "Port Approach Marine Buoy", "marine", "Approach Channel")

        print(f"\nImporting weather ({WEATHER_YEARS[0]}-{WEATHER_YEARS[-1]})...")
        weather_count = import_weather(weather_station.id)

        print(f"\nImporting air quality ({AIR_QUALITY_YEARS[0]}-{AIR_QUALITY_YEARS[-1]}, only fully-populated years)...")
        aq_count = import_air_quality(aq_station.id)

        print(f"\nImporting marine ({MARINE_YEARS[0]}-{MARINE_YEARS[-1]})...")
        marine_count = import_marine(marine_station.id)

        print("\nImporting port traffic annual statistics...")
        traffic_count = import_port_traffic()

        write_manifest(weather_count, aq_count, marine_count, traffic_count)

        print("\n" + "=" * 60)
        print("IMPORT COMPLETE")
        print(f"  Weather readings:      {weather_count:,}")
        print(f"  Air quality readings:  {aq_count:,}")
        print(f"  Marine readings:       {marine_count:,}")
        print(f"  Port traffic (years):  {traffic_count}")
        print("=" * 60)


if __name__ == "__main__":
    main()
