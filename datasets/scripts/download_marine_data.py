#!/usr/bin/env python3
"""
Download Marine/Oceanographic Data (2022-present) for V.O. Chidambaranar Port.

Source:  Open-Meteo Marine Weather API
URL:     https://marine-api.open-meteo.com/v1/marine
License:  CC-BY 4.0

Output:  raw/marine/marine_YYYY.csv  (one CSV per year, hourly rows)

Used by: berth operations, vessel approach monitoring, berth.can_accommodate()
Note: Only available from ~2022; older years return null.
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
START_YEAR = 2022
END_YEAR = datetime.date.today().year
BASE_URL = "https://marine-api.open-meteo.com/v1/marine"

HOURLY_VARS = [
    "wave_height",
    "wave_direction",
    "wave_period",
    "sea_surface_temperature",
    "sea_level_height_msl",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "raw", "marine")


def fetch_year(year):
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(HOURLY_VARS),
        "timezone": "Asia/Kolkata",
    }

    url = BASE_URL + "?" + urllib.parse.urlencode(params)
    print(f"Fetching marine data for {year}: {url}")

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
    output_file = os.path.join(OUTPUT_DIR, f"marine_{year}.csv")

    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "recorded_at", "wave_height_m", "wave_direction_deg",
            "wave_period_s", "sea_surface_temp_c", "sea_level_height_msl_m"
        ])

        for i in range(rows):
            writer.writerow([
                times[i],
                hourly.get("wave_height", [None] * rows)[i],
                hourly.get("wave_direction", [None] * rows)[i],
                hourly.get("wave_period", [None] * rows)[i],
                hourly.get("sea_surface_temperature", [None] * rows)[i],
                hourly.get("sea_level_height_msl", [None] * rows)[i],
            ])

    print(f"  Saved to {output_file}")
    return True


def main():
    print(f"Downloading Marine data for {START_YEAR}-{END_YEAR}")
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