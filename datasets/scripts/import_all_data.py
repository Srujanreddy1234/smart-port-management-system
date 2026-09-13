#!/usr/bin/env python3
"""
Import all downloaded datasets into the Smart Port Management System database.

Loads:
- Weather data -> WeatherReading model
- Air Quality data -> AirQualityReading model
- Marine data -> (for berth operations, stored as metadata)
- Port Traffic data -> (for dashboard KPIs, reports)

Run from backend directory: python ../datasets/scripts/import_all_data.py
"""

import os
import sys
import csv
import glob
from datetime import datetime

# Add backend to path
BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "backend")
sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault("FLASK_ENV", "development")

from app import create_app
from app.extensions import db
from app.models.environment import (
    MonitoringStation, WeatherReading, AirQualityReading,
    WeatherParameter, AirQualityParameter
)
from app.models.ship import Ship, ShipStatus, VesselType
from app.models.container import Container, ContainerStatus, ContainerType


def get_or_create_port_station():
    """Get or create the main port monitoring station."""
    station = MonitoringStation.query.filter_by(station_id="VOC_PORT_MAIN").first()
    if not station:
        station = MonitoringStation(
            station_id="VOC_PORT_MAIN",
            name="V.O. Chidambaranar Port - Main Station",
            station_type="weather_air_quality",
            latitude=8.75,
            longitude=78.20,
            zone="Port Area",
            address="V.O. Chidambaranar Port, Thoothukudi, Tamil Nadu",
            elevation=5.0,
            is_active=True,
            parameters={
                "weather": [p.value for p in WeatherParameter],
                "air_quality": [p.value for p in AirQualityParameter]
            }
        )
        db.session.add(station)
        db.session.commit()
        print(f"  Created station: {station.name} (ID: {station.id})")
    return station


def import_weather_data(station_id):
    """Import weather data from CSV files."""
    weather_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "raw", "weather"
    )
    files = sorted(glob.glob(os.path.join(weather_dir, "weather_*.csv")))

    if not files:
        print("  No weather files found")
        return 0

    total_imported = 0
    for filepath in files:
        year = os.path.basename(filepath).replace("weather_", "").replace(".csv", "")
        print(f"  Importing weather {year}...")

        count = 0
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                try:
                    reading = WeatherReading(
                        station_id=station_id,
                        recorded_at=datetime.fromisoformat(row["recorded_at"]),
                        temperature=float(row["temperature"]) if row["temperature"] else None,
                        feels_like=float(row["feels_like"]) if row["feels_like"] else None,
                        humidity=float(row["humidity"]) if row["humidity"] else None,
                        wind_speed=float(row["wind_speed"]) if row["wind_speed"] else None,
                        wind_direction=float(row["wind_direction"]) if row["wind_direction"] else None,
                        wind_gust=float(row["wind_gust"]) if row["wind_gust"] else None,
                        pressure=float(row["pressure"]) if row["pressure"] else None,
                        precipitation=float(row["precipitation"]) if row["precipitation"] else None,
                        visibility=float(row["visibility"]) if row["visibility"] else None,
                        uv_index=float(row["uv_index"]) if row["uv_index"] else None,
                        dew_point=float(row["dew_point"]) if row["dew_point"] else None,
                        heat_index=float(row["heat_index"]) if row["heat_index"] else None,
                        wind_chill=float(row["wind_chill"]) if row["wind_chill"] else None,
                        cloud_cover=float(row["cloud_cover"]) if row["cloud_cover"] else None,
                        solar_radiation=float(row["solar_radiation"]) if row["solar_radiation"] else None,
                        weather_condition=row["weather_condition"] if row["weather_condition"] else None,
                        weather_description=row["weather_description"] if row["weather_description"] else None,
                    )
                    batch.append(reading)
                    count += 1

                    if len(batch) >= 500:
                        db.session.bulk_save_objects(batch)
                        db.session.commit()
                        batch = []
                except Exception as e:
                    print(f"    Error importing row: {e}")
                    continue

            if batch:
                db.session.bulk_save_objects(batch)
                db.session.commit()

        total_imported += count
        print(f"    Imported {count} records")

    return total_imported


def import_air_quality_data(station_id):
    """Import air quality data from CSV files."""
    aq_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "raw", "air_quality"
    )
    files = sorted(glob.glob(os.path.join(aq_dir, "air_quality_*.csv")))

    if not files:
        print("  No air quality files found")
        return 0

    total_imported = 0
    for filepath in files:
        year = os.path.basename(filepath).replace("air_quality_", "").replace(".csv", "")
        print(f"  Importing air quality {year}...")

        count = 0
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                try:
                    reading = AirQualityReading(
                        station_id=station_id,
                        recorded_at=datetime.fromisoformat(row["recorded_at"]),
                        aqi=int(row["aqi"]) if row["aqi"] else None,
                        aqi_category=row["aqi_category"] if row["aqi_category"] else None,
                        pm25=float(row["pm25"]) if row["pm25"] else None,
                        pm10=float(row["pm10"]) if row["pm10"] else None,
                        no2=float(row["no2"]) if row["no2"] else None,
                        so2=float(row["so2"]) if row["so2"] else None,
                        co=float(row["co"]) if row["co"] else None,
                        o3=float(row["o3"]) if row["o3"] else None,
                        nh3=float(row["nh3"]) if row["nh3"] else None,
                        temperature=float(row["temperature"]) if row["temperature"] else None,
                        humidity=float(row["humidity"]) if row["humidity"] else None,
                        wind_speed=float(row["wind_speed"]) if row["wind_speed"] else None,
                        wind_direction=float(row["wind_direction"]) if row["wind_direction"] else None,
                        pressure=float(row["pressure"]) if row["pressure"] else None,
                    )
                    batch.append(reading)
                    count += 1

                    if len(batch) >= 500:
                        db.session.bulk_save_objects(batch)
                        db.session.commit()
                        batch = []
                except Exception as e:
                    print(f"    Error importing row: {e}")
                    continue

            if batch:
                db.session.bulk_save_objects(batch)
                db.session.commit()

        total_imported += count
        print(f"    Imported {count} records")

    return total_imported


def import_port_traffic_data():
    """Import port traffic statistics."""
    traffic_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "raw", "port_traffic", "port_traffic_statistics.csv"
    )

    if not os.path.exists(traffic_file):
        print("  Port traffic file not found")
        return 0

    print(f"  Importing port traffic statistics...")

    # This data is used for dashboard KPIs and reports
    # We'll store it in a simple way - could be extended to a dedicated model
    count = 0
    with open(traffic_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            count += 1
            # For now, just verify the data loads correctly
            print(f"    FY {row['fiscal_year']}: {row['total_cargo_mmt']} MMT, {row['container_teu']} TEU, {row['vessel_calls']} vessels")

    return count


def create_sample_ships_and_containers():
    """Create sample ships and containers for demonstration."""
    # Check if already exists
    if Ship.query.first():
        print("  Ships already exist, skipping creation")
        return 0, 0

    print("  Creating sample ships and containers...")

    # Sample ships based on port traffic data
    vessels = [
        {"name": "MSC ANNA", "imo": "9708699", "vessel_type": VesselType.CONTAINER, "status": ShipStatus.AT_BERTH, "length": 366, "beam": 51, "draft": 15.5, "deadweight": 150000, "flag": "Panama", "berth_id": "B1"},
        {"name": "CMA CGM MARCO POLO", "imo": "9702150", "vessel_type": VesselType.CONTAINER, "status": ShipStatus.ANCHORED, "length": 396, "beam": 54, "draft": 16.0, "deadweight": 180000, "flag": "France", "berth_id": None},
        {"name": "MT OCEAN GLORY", "imo": "9812345", "vessel_type": VesselType.TANKER, "status": ShipStatus.AT_BERTH, "length": 250, "beam": 44, "draft": 12.5, "deadweight": 110000, "flag": "Singapore", "berth_id": "B3"},
        {"name": "MV BULK CARRIER 1", "imo": "9876543", "vessel_type": VesselType.BULK_CARRIER, "status": ShipStatus.EXPECTED, "length": 229, "beam": 32, "draft": 14.0, "deadweight": 80000, "flag": "India", "berth_id": None},
        {"name": "GENERAL CARGO EXPRESS", "imo": "9765432", "vessel_type": VesselType.GENERAL_CARGO, "status": ShipStatus.AT_BERTH, "length": 180, "beam": 28, "draft": 10.0, "deadweight": 45000, "flag": "India", "berth_id": "B5"},
    ]

    ships_created = 0
    containers_created = 0

    for v in vessels:
        ship = Ship(**v)
        db.session.add(ship)
        db.session.flush()
        ships_created += 1

        # Create some containers for container ships
        if v["vessel_type"] == VesselType.CONTAINER:
            for i in range(10):
                container = Container(
                    container_number=f"{v['name'][:4].upper()}{1000+i}",
                    container_type=ContainerType.STANDARD_20 if i % 2 == 0 else ContainerType.STANDARD_40,
                    status=ContainerStatus.ON_VESSEL,
                    vessel_id=ship.id,
                    weight=18000 if i % 2 == 0 else 26000,
                    cargo_description="General cargo",
                    is_refrigerated=i % 5 == 0,
                    is_hazardous=False,
                )
                db.session.add(container)
                containers_created += 1

    db.session.commit()
    print(f"    Created {ships_created} ships and {containers_created} containers")
    return ships_created, containers_created


def main():
    print("="*60)
    print("📥 Smart Port Management System - Data Importer")
    print("   Importing 6-7 years of historical data into database")
    print("="*60)

    app = create_app("development")

    with app.app_context():
        print("\n1. Creating/verifying port monitoring station...")
        station = get_or_create_port_station()

        print("\n2. Importing weather data (2018-2025)...")
        weather_count = import_weather_data(station.id)
        print(f"   Total weather records imported: {weather_count}")

        print("\n3. Importing air quality data (2018-2025)...")
        aq_count = import_air_quality_data(station.id)
        print(f"   Total air quality records imported: {aq_count}")

        print("\n4. Importing port traffic statistics...")
        traffic_count = import_port_traffic_data()
        print(f"   Total traffic records: {traffic_count}")

        print("\n5. Creating sample ships and containers...")
        ships, containers = create_sample_ships_and_containers()

        print("\n" + "="*60)
        print("✅ DATA IMPORT COMPLETE")
        print("="*60)
        print(f"  Weather readings: {weather_count:,}")
        print(f"  Air quality readings: {aq_count:,}")
        print(f"  Port traffic records: {traffic_count}")
        print(f"  Ships: {ships}")
        print(f"  Containers: {containers}")
        print(f"\n  Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print("="*60)


if __name__ == "__main__":
    main()