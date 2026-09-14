#!/usr/bin/env python3
"""
Train a 24-hour-ahead AQI forecasting model for the Smart Port environmental
dashboard, using the real historical air quality data imported by
datasets/scripts/import_to_database.py (2023-2025, Open-Meteo CAMS reanalysis).

Why this feature, and not something else:
- It's the one place in this project where we have a genuinely rich, reliable,
  continuous historical time series (26,304 real hourly AQI readings, no
  gaps) with an obvious, useful prediction target: "what will air quality be
  tomorrow at this hour", which is directly relevant to environment.html and
  to reports.html.
- Ship schedules, berth occupancy, security incidents, maintenance, and
  billing all have no real historical dataset at all (see the datasets
  audit) -- predicting anything from purely synthetic random data would not
  be a genuine ML feature, just decoration.

Method:
- Features are built only from information available *before* the prediction
  time: lag values (1h, 24h, 168h ago), a trailing 24h rolling mean, calendar
  features (hour/day-of-week/month), and the current pollutant/weather
  co-variates recorded alongside each AQI reading. No feature is derived
  from data at or after the target time, so there is no leakage.
- Train/test split is temporal, not random: train on 2023-01-01..2024-12-31,
  test on 2025-01-01..2025-12-31 (entirely unseen "future" data relative to
  training). A model evaluated only with a random shuffle split would silently
  leak nearby-in-time rows between train and test and overstate accuracy.
- A trivial persistence baseline (predict AQI(t+24h) = AQI(t)) is reported
  alongside the trained model, since a forecasting model that doesn't beat
  "tomorrow will be like today" is not actually adding value.

Run from the backend directory:
    python ml/train_aqi_forecast.py
"""

import os
import sys
import json
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
os.environ.setdefault("FLASK_ENV", "development")

from app import create_app
from app.extensions import db
from app.models import AirQualityReading, WeatherReading

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "aqi_forecast_model.joblib")
METADATA_PATH = os.path.join(MODEL_DIR, "aqi_forecast_metadata.json")

FORECAST_HORIZON_HOURS = 24
TRAIN_END = "2024-12-31 23:00:00"
TEST_START = "2025-01-01 00:00:00"

FEATURE_COLUMNS = [
    "aqi_lag_1h", "aqi_lag_24h", "aqi_lag_168h", "aqi_rolling_mean_24h",
    "pm25", "pm10", "no2", "so2", "co", "o3",
    "temperature", "humidity", "wind_speed", "pressure",
    "hour", "day_of_week", "month",
]


def load_dataframe():
    app = create_app(os.environ.get("FLASK_ENV", "development"))
    with app.app_context():
        aq_rows = AirQualityReading.query.order_by(AirQualityReading.recorded_at).all()
        aq_records = [{
            "recorded_at": r.recorded_at,
            "aqi": r.aqi,
            "pm25": r.pm25, "pm10": r.pm10, "no2": r.no2, "so2": r.so2,
            "co": r.co, "o3": r.o3,
        } for r in aq_rows]

        # The air-quality source API leaves temperature/humidity/wind_speed/
        # pressure entirely empty for every row (verified in the raw CSV) --
        # those columns aren't usable from AirQualityReading. Real weather
        # co-variates for the same timestamps exist in WeatherReading, so
        # join on recorded_at instead of leaving the model without them.
        weather_rows = WeatherReading.query.order_by(WeatherReading.recorded_at).all()
        weather_records = [{
            "recorded_at": r.recorded_at,
            "temperature": r.temperature, "humidity": r.humidity,
            "wind_speed": r.wind_speed, "pressure": r.pressure,
        } for r in weather_rows]

    aq_df = pd.DataFrame.from_records(aq_records)
    if aq_df.empty:
        raise RuntimeError(
            "No AirQualityReading rows found. Run "
            "datasets/scripts/import_to_database.py first."
        )
    weather_df = pd.DataFrame.from_records(weather_records)

    df = aq_df.merge(weather_df, on="recorded_at", how="left")
    df = df.set_index("recorded_at").sort_index()
    # Data was imported at hourly resolution; reindex to a strict hourly grid
    # so lag/rolling features and the forecast target line up on real hours
    # rather than silently shifting across any gap.
    full_index = pd.date_range(df.index.min(), df.index.max(), freq="h")
    df = df.reindex(full_index)
    return df


def build_features(df):
    df = df.copy()
    df["aqi_lag_1h"] = df["aqi"].shift(1)
    df["aqi_lag_24h"] = df["aqi"].shift(24)
    df["aqi_lag_168h"] = df["aqi"].shift(168)
    df["aqi_rolling_mean_24h"] = df["aqi"].shift(1).rolling(24, min_periods=12).mean()
    df["hour"] = df.index.hour
    df["day_of_week"] = df.index.dayofweek
    df["month"] = df.index.month
    df["target"] = df["aqi"].shift(-FORECAST_HORIZON_HOURS)
    return df


def main():
    print("Loading real historical air quality data from the database...")
    df = load_dataframe()
    print(f"  {len(df)} hourly rows, {df.index.min()} .. {df.index.max()}")

    df = build_features(df)
    model_df = df.dropna(subset=FEATURE_COLUMNS + ["target"])
    print(f"  {len(model_df)} rows usable after building lag/target features")

    train_df = model_df[model_df.index <= TRAIN_END]
    test_df = model_df[model_df.index >= TEST_START]
    print(f"  Train: {len(train_df)} rows ({train_df.index.min()} .. {train_df.index.max()})")
    print(f"  Test:  {len(test_df)} rows ({test_df.index.min()} .. {test_df.index.max()})")

    if len(train_df) < 100 or len(test_df) < 100:
        raise RuntimeError(
            "Not enough data for a temporal train/test split. "
            "Re-run the dataset import first."
        )

    X_train, y_train = train_df[FEATURE_COLUMNS], train_df["target"]
    X_test, y_test = test_df[FEATURE_COLUMNS], test_df["target"]

    # Baseline: "tomorrow will look like today" -- the model must beat this
    # to be worth calling a predictive feature.
    baseline_pred = test_df["aqi_lag_1h"]
    baseline_mae = mean_absolute_error(y_test, baseline_pred)
    baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_pred))
    baseline_r2 = r2_score(y_test, baseline_pred)

    model = RandomForestRegressor(
        n_estimators=200, max_depth=12, min_samples_leaf=5,
        random_state=42, n_jobs=-1,
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, pred)
    rmse = np.sqrt(mean_squared_error(y_test, pred))
    r2 = r2_score(y_test, pred)

    importances = dict(zip(FEATURE_COLUMNS, model.feature_importances_.round(4).tolist()))

    print("\n" + "=" * 60)
    print(f"Persistence baseline (AQI(t+{FORECAST_HORIZON_HOURS}h) = AQI(t)):")
    print(f"  MAE={baseline_mae:.2f}  RMSE={baseline_rmse:.2f}  R2={baseline_r2:.3f}")
    print(f"\nRandomForestRegressor:")
    print(f"  MAE={mae:.2f}  RMSE={rmse:.2f}  R2={r2:.3f}")
    print("=" * 60)

    if mae >= baseline_mae:
        print(
            "\nWARNING: the trained model did not beat the naive persistence "
            "baseline on held-out 2025 data. Saving it anyway for inspection, "
            "but the prediction endpoint should not be presented as reliable "
            "until this improves (more/better features, different model, or "
            "a longer training window as more real data accumulates)."
        )

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    metadata = {
        "trained_at": datetime.utcnow().isoformat() + "Z",
        "forecast_horizon_hours": FORECAST_HORIZON_HOURS,
        "feature_columns": FEATURE_COLUMNS,
        "train_range": [str(train_df.index.min()), str(train_df.index.max())],
        "test_range": [str(test_df.index.min()), str(test_df.index.max())],
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "metrics": {
            "model": {"mae": round(mae, 3), "rmse": round(rmse, 3), "r2": round(r2, 3)},
            "persistence_baseline": {
                "mae": round(baseline_mae, 3), "rmse": round(baseline_rmse, 3), "r2": round(baseline_r2, 3)
            },
        },
        "beats_baseline": bool(mae < baseline_mae),
        "feature_importances": importances,
    }
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nModel saved to {MODEL_PATH}")
    print(f"Metadata saved to {METADATA_PATH}")


if __name__ == "__main__":
    main()
