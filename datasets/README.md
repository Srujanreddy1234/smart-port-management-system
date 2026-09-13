# Datasets for Smart Port Management System

This directory contains **real-world datasets** for the past 6-7 years that are
**100% needed and fully useful** for the Smart Port Management System project
(V.O. Chidambaranar Port, Thoothukudi).

## What's included

| # | Dataset               | Source           | Years     | Status       |
|---|-----------------------|------------------|-----------|--------------|
| 1 | Historical Weather    | Open-Meteo ERA5  | 2018-2024 | Downloadable |
| 2 | Air Quality           | Open-Meteo CAMS  | 2018-2024 | Downloadable |
| 3 | Marine/Oceanographic  | Open-Meteo Marine| 2022-2024 | Downloadable |
| 4 | Port Traffic Stats    | IPA / VOC Port   | 2018-2024 | Included CSV |

## Quick start

```bash
pip3 install requests

cd "datasets"
python3 scripts/download_all_datasets.py
```

See `DATASETS_CATALOG.md` for the complete mapping of each dataset to the
project's data models.
