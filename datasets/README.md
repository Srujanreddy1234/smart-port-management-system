# Datasets for Smart Port Management System

This directory contains real-world datasets for V.O. Chidambaranar Port,
Thoothukudi, downloaded from free public APIs. They are imported into the
application database and used by `environment.html`, the `/dashboard` and
`/environment` and `/reports` APIs -- they are not sitting here unused.

## What's included, and what's actually imported

Only years with genuinely complete data are imported. See
`processed/import_manifest.json` for the exact record counts and exclusion
reasons from the most recent import run, and `DATASETS_CATALOG.md` for the
full model mapping.

| # | Dataset               | Source            | Downloaded | **Imported** | Why |
|---|-----------------------|-------------------|------------|--------------|-----|
| 1 | Historical Weather    | Open-Meteo ERA5   | 2018-2025  | **2020-2025** (6 yrs) | Fully populated for every year; 6-year window used |
| 2 | Air Quality           | Open-Meteo CAMS   | 2018-2025  | **2023-2025** (3 yrs) | 2018-2021 have 0% coverage, 2022 ~41% -- excluded rather than imported as if complete |
| 3 | Marine/Oceanographic  | Open-Meteo Marine | 2022-2025  | **2022-2025** (4 yrs) | Wave data populated throughout; sea-temp/sea-level partially null in 2022-23, imported as NULL |
| 4 | Port Traffic Stats    | IPA / VOC Port    | FY2018-19 to FY2023-24 | **all 6 fiscal years** | Annual aggregate only -- deliberately never used for daily/hourly figures |

## Quick start

Re-download the source data (idempotent, overwrites the CSVs with the latest
available years):

```bash
pip3 install requests
cd datasets
python3 scripts/download_all_datasets.py
```

Import into the application database (also idempotent -- clears and
re-imports rather than appending duplicates):

```bash
cd backend
python ../datasets/scripts/import_to_database.py
```

See `DATASETS_CATALOG.md` for the complete mapping of each dataset to the
project's data models.
