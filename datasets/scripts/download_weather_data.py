#!/usr/bin/env python3
"""
Download Historical Weather Data (2018–present) for V.O. Chidambaranar Port.

Source:  Open-Meteo Historical Weather API (ERA5 reanalysis)
URL:     https://archive-api.open-meteo.com/v1/archive
License:  CC-BY 4.0

Output:  raw/weather/weather_YYYY.csv  (one CSV per year, hourly rows)

Maps to: backend/app/models/environment.py → WeatherReading
"""

import os
import csv
import time
import datetime
import urllib.request
import urllib.parse
import json
import math

LATITUDE = 8.75
LONGITUDE = 78.20
START_YEAR = 2018
END_YEAR = datetime.date.today().year
BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

HOURLY_VARS = [
    "temperature_2m", "apparent_temperature", "relative_humidity_2m",
    "dew_point_2m", "precipitation", "pressure_msl", "surface_pressure",
    "cloud_cover", "wind_speed_10m", "wind_direction_10m",
    "wind_gusts_10m", "shortwave_radiation", "weather_code",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "raw", "weather")


def weather_code_to_condition(code):
    code_map = {
        0: ("Sunny", "Clear skies"),
        1: ("Partly Cloudy", "Mainly clear"),
        2: ("Partly Cloudy", "Partly cloudy"),
        3: ("Cloudy", "Overcast"),
        45: ("Hazy", "Fog"),
        48: ("Hazy", "Depositing rime fog"),
        51: ("Light Rain", "Light drizzle"),
        53: ("Light Rain", "Moderate drizzle"),
        55: ("Light Rain", "Dense drizzle"),
        61: ("Light Rain", "Slight rain"),
        63: ("Light Rain", "Moderate rain"),
        65: ("Thunderstorm", "Heavy rain"),
        66: ("Light Rain", "Freezing rain"),
        67: ("Light Rain", "Heavy freezing rain"),
        71: ("Light Rain", "Slight snow fall"),
        73: ("Light Rain", "Moderate snow fall"),
        75: ("Light Rain", "Heavy snow fall"),
        77: ("Light Rain", "Snow grains"),
        80: ("Light Rain", "Slight rain showers"),
        81: ("Light Rain", "Moderate rain showers"),
        82: ("Thunderstorm", "Violent rain showers"),
        85: ("Light Rain", "Slight snow showers"),
        86: ("Light Rain", "Heavy snow showers"),
        95: ("Thunderstorm", "Thunderstorm"),
        96: ("Thunderstorm", "Thunderstorm with slight hail"),
        99: ("Thunderstorm", "Thunderstorm with heavy hail"),
    }
    return code_map.get(code, ("Unknown", "Unknown"))


def calculate_heat_index(temp_c, humidity):
    """Calculate heat index in Celsius from temperature and humidity."""
    if temp_c is None or humidity is None:
        return None
    temp_f = temp_c * 9/5 + 32
    if temp_f < 80:
        return temp_c
    hi_f = -42.379 + 2.04901523*temp_f + 10.14333127*humidity \
           - 0.22475541*temp_f*humidity - 0.00683783*temp_f**2 \
           - 0.05481717*humidity**2 + 0.00122874*temp_f**2*humidity \
           + 0.00085282*temp_f*humidity**2 - 0.00000199*temp_f**2*humidity**2
    return (hi_f - 32) * 5/9


def calculate_wind_chill(temp_c, wind_speed_kmh):
    """Calculate wind chill in Celsius."""
    if temp_c is None or wind_speed_kmh is None:
        return None
    if temp_c > 10 or wind_speed_kmh < 4.8:
        return temp_c
    wind_kph = wind_speed_kmh
    wc = 13.12 + 0.6215*temp_c - 11.37*(wind_kph**0.16) + 0.3965*temp_c*(wind_kph**0.16)
    return wc


def fetch_year(year):
    start_date = f"{year}-01-01"
    # The archive API 400s if asked for dates beyond what's actually been
    # observed yet -- cap the current (in-progress) year at today instead
    # of Dec 31, so re-running this for the current year to pick up fresh
    # months doesn't fail outright.
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
    output_file = os.path.join(OUTPUT_DIR, f"weather_{year}.csv")

    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "recorded_at", "temperature", "feels_like", "humidity",
            "wind_speed", "wind_direction", "wind_gust", "pressure",
            "precipitation", "visibility", "uv_index", "dew_point",
            "heat_index", "wind_chill", "cloud_cover", "solar_radiation",
            "weather_condition", "weather_description"
        ])

        for i in range(rows):
            temp = hourly.get("temperature_2m", [None] * rows)[i]
            feels = hourly.get("apparent_temperature", [None] * rows)[i]
            hum = hourly.get("relative_humidity_2m", [None] * rows)[i]
            dew = hourly.get("dew_point_2m", [None] * rows)[i]
            precip = hourly.get("precipitation", [None] * rows)[i]
            press = hourly.get("pressure_msl", [None] * rows)[i]
            cloud = hourly.get("cloud_cover", [None] * rows)[i]
            wind_spd = hourly.get("wind_speed_10m", [None] * rows)[i]
            wind_dir = hourly.get("wind_direction_10m", [None] * rows)[i]
            wind_gust = hourly.get("wind_gusts_10m", [None] * rows)[i]
            solar = hourly.get("shortwave_radiation", [None] * rows)[i]
            wcode = hourly.get("weather_code", [None] * rows)[i]

            # Convert wind speed from km/h to m/s
            wind_speed_ms = wind_spd / 3.6 if wind_spd is not None else None
            wind_gust_ms = wind_gust / 3.6 if wind_gust is not None else None

            # Derive visibility from cloud cover and precipitation (rough estimate)
            visibility = None
            if cloud is not None and precip is not None:
                if precip > 0:
                    visibility = max(0.1, 10 - precip * 2)
                elif cloud > 80:
                    visibility = 5
                else:
                    visibility = 10 + (100 - cloud) * 0.05

            # UV index not directly available from historical API
            uv_index = None

            hi = calculate_heat_index(temp, hum)
            wc = calculate_wind_chill(temp, wind_spd)

            condition, desc = weather_code_to_condition(wcode)

            writer.writerow([
                times[i],
                temp,
                feels,
                hum,
                wind_speed_ms,
                wind_dir,
                wind_gust_ms,
                press,
                precip,
                visibility,
                uv_index,
                dew,
                hi,
                wc,
                cloud,
                solar,
                condition,
                desc,
            ])

    print(f"  Saved to {output_file}")
    return True


def main():
    print(f"Downloading Weather data for {START_YEAR}-{END_YEAR}")
    print(f"Location: {LATITUDE}°N, {LONGITUDE}°E (V.O. Chidambaranar Port)")
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    success_count = 0
    for year in range(START_YEAR, END_YEAR + 1):
        if fetch_year(year):
            success_count += 1
        time.sleep(1)

    print(f"\nDone. Successfully downloaded {success_count}/{END_YEAR - START_YEAR + 1} years.")


if __name__ == "__main__":
    main()