"""
Loads the trained AQI forecasting model (see train_aqi_forecast.py) and
produces a 24-hour-ahead prediction from the most recent real readings in
the database. Returns None (no crash) if the model hasn't been trained yet
or there isn't enough recent history to build the feature vector -- callers
must treat a missing prediction as a legitimate "not available" state, not
an error to paper over with a fabricated number.
"""

import os
import json
import joblib
from datetime import timedelta

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "aqi_forecast_model.joblib")
METADATA_PATH = os.path.join(MODEL_DIR, "aqi_forecast_metadata.json")

_model = None
_metadata = None
_load_attempted = False


def _load():
    global _model, _metadata, _load_attempted
    if _load_attempted:
        return
    _load_attempted = True
    if os.path.exists(MODEL_PATH) and os.path.exists(METADATA_PATH):
        _model = joblib.load(MODEL_PATH)
        with open(METADATA_PATH) as f:
            _metadata = json.load(f)


def preload():
    """Load the model at process startup instead of on a random user's
    first request -- deserializing the joblib file takes several seconds,
    and paying that cost during boot (once per worker) rather than during
    a live request keeps forecast latency consistent for every user."""
    _load()


def aqi_category(aqi):
    if aqi is None:
        return None
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Moderate"
    if aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    if aqi <= 200:
        return "Unhealthy"
    if aqi <= 300:
        return "Very Unhealthy"
    return "Hazardous"


def get_metadata():
    _load()
    return _metadata


def predict_next(AirQualityReading, WeatherReading):
    """Predict AQI `forecast_horizon_hours` ahead of the latest real reading.
    Returns a dict, or None if the model/data isn't available."""
    _load()
    if _model is None:
        return None

    horizon = _metadata["forecast_horizon_hours"]
    latest = AirQualityReading.query.order_by(AirQualityReading.recorded_at.desc()).first()
    if latest is None:
        return None

    def reading_at_or_before(target_time):
        return AirQualityReading.query.filter(
            AirQualityReading.recorded_at <= target_time
        ).order_by(AirQualityReading.recorded_at.desc()).first()

    lag_24h = reading_at_or_before(latest.recorded_at - timedelta(hours=24))
    lag_168h = reading_at_or_before(latest.recorded_at - timedelta(hours=168))
    if lag_24h is None or lag_168h is None:
        return None

    window_start = latest.recorded_at - timedelta(hours=24)
    recent = AirQualityReading.query.filter(
        AirQualityReading.recorded_at > window_start,
        AirQualityReading.recorded_at <= latest.recorded_at
    ).all()
    if len(recent) < 12:
        return None
    rolling_mean_24h = sum(r.aqi for r in recent if r.aqi is not None) / len(recent)

    weather = WeatherReading.query.filter(
        WeatherReading.recorded_at <= latest.recorded_at
    ).order_by(WeatherReading.recorded_at.desc()).first()

    target_time = latest.recorded_at + timedelta(hours=horizon)
    features = {
        "aqi_lag_1h": latest.aqi,
        "aqi_lag_24h": lag_24h.aqi,
        "aqi_lag_168h": lag_168h.aqi,
        "aqi_rolling_mean_24h": rolling_mean_24h,
        "pm25": latest.pm25, "pm10": latest.pm10, "no2": latest.no2,
        "so2": latest.so2, "co": latest.co, "o3": latest.o3,
        "temperature": weather.temperature if weather else None,
        "humidity": weather.humidity if weather else None,
        "wind_speed": weather.wind_speed if weather else None,
        "pressure": weather.pressure if weather else None,
        "hour": target_time.hour,
        "day_of_week": target_time.weekday(),
        "month": target_time.month,
    }
    if any(v is None for v in features.values()):
        return None

    row = [[features[col] for col in _metadata["feature_columns"]]]
    predicted_aqi = float(_model.predict(row)[0])

    return {
        "predicted_aqi": round(predicted_aqi, 1),
        "predicted_category": aqi_category(predicted_aqi),
        "based_on_reading_at": latest.recorded_at.isoformat(),
        "forecast_for": target_time.isoformat(),
        "forecast_horizon_hours": horizon,
        "model_metrics": _metadata["metrics"],
        "is_ml_prediction": True,
    }
