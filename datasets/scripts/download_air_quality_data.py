#!/usr/bin/env python3
"""
Download Air Quality Data (2018-present) for V.O. Chidambaranar Port.

Source:  Open-Meteo Air Quality API (CAMS European air quality reanalysis)
URL:     https://air-quality-api.open-meteo.com/v1/air-quality
License:  CC-BY 4.0 (free with attribution to CAMS)

Output:  raw/air_quality/air_quality_YYYY.csv  (one CSV per year, hourly rows)

Maps to: backend/app/models/environment.py -> AirQualityReading
"""

import os
import csv
import time
import datetime
import urllib.request
import urllib.parse
import json

LATITUDE = 8.75
LONGITUDE = 78.20
START_YEAR = 2018
END_YEAR = datetime.date.today().year
BASE_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

HOURLY_VARS = [
    "us_aqi",
    "pm2_5",
    "pm10",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "carbon_monoxide",
    "ozone",
    "ammonia",
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "wind_direction_10m",
    "pressure_msl",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "raw", "air_quality")

# AQI category mapping (US EPA standard)
def aqi_to_category(aqi):
    if aqi is None:
        return "Unknown"
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"


def fetch_year(year):
    start_date = f"{year}-01-01"
    # See download_weather_data.py's fetch_year() for why the current year
    # is capped at today instead of Dec 31.
    today = datetime.date.today()
    end_date = today.isoformat() if year == today.year else f"{year}-12-31"

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(HOURLY_VARS),
        "timezone": "Asia/Kolkata",
    }

    url = BASE_URL + "?" + urllib.parse.urlencode(params)
    print(f"Fetching {year}: {url}")

    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        print(f"  Error fetching {year}: {e}")
        return False

    hourly = data.get("hourly", {})
    if not hourly or "time" not in hourly:
        print(f"  No data for {year}")
        return False

    times = hourly["time"]
    rows = len(times)
    print(f"  Got {rows} hourly records")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_file = os.path.join(OUTPUT_DIR, f"air_quality_{year}.csv")

    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "recorded_at", "aqi", "aqi_category", "pm25", "pm10",
            "no2", "so2", "co", "o3", "nh3",
            "temperature", "humidity", "wind_speed", "wind_direction", "pressure"
        ])

        for i in range(rows):
            aqi = hourly.get("us_aqi", [None] * rows)[i]
            writer.writerow([
                times[i],
                aqi,
                aqi_to_category(aqi),
                hourly.get("pm2_5", [None] * rows)[i],
                hourly.get("pm10", [None] * rows)[i],
                hourly.get("nitrogen_dioxide", [None] * rows)[i],
                hourly.get("sulphur_dioxide", [None] * rows)[i],
                hourly.get("carbon_monoxide", [None] * rows)[i],
                hourly.get("ozone", [None] * rows)[i],
                hourly.get("ammonia", [None] * rows)[i],
                hourly.get("temperature_2m", [None] * rows)[i],
                hourly.get("relative_humidity_2m", [None] * rows)[i],
                hourly.get("wind_speed_10m", [None] * rows)[i],
                hourly.get("wind_direction_10m", [None] * rows)[i],
                hourly.get("pressure_msl", [None] * rows)[i],
            ])

    print(f"  Saved to {output_file}")
    return True


def main():
    print(f"Downloading Air Quality data for {START_YEAR}-{END_YEAR}")
    print(f"Location: {LATITUDE}°N, {LONGITUDE}°E (V.O. Chidambaranar Port)")
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    success_count = 0
    for year in range(START_YEAR, END_YEAR + 1):
        if fetch_year(year):
            success_count += 1
        time.sleep(1)  # Be nice to the API

    print(f"\nDone. Successfully downloaded {success_count}/{END_YEAR - START_YEAR + 1} years.")


if __name__ == "__main__":
    main()