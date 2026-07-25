from datetime import datetime
from enum import Enum as PyEnum
from app.extensions import db
from sqlalchemy import Enum, Index


class WaterQualityParameter(PyEnum):
    PH = 'pH'
    DISSOLVED_OXYGEN = 'Dissolved Oxygen'
    BOD = 'Biochemical Oxygen Demand'
    COD = 'Chemical Oxygen Demand'
    TSS = 'Total Suspended Solids'
    TDS = 'Total Dissolved Solids'
    OIL_GREASE = 'Oil and Grease'
    AMMONIA = 'Ammonia'
    NITRATE = 'Nitrate'
    PHOSPHATE = 'Phosphate'
    TEMPERATURE = 'Temperature'
    TURBIDITY = 'Turbidity'
    CONDUCTIVITY = 'Conductivity'
    SALINITY = 'Salinity'
    FECAL_COLIFORM = 'Fecal Coliform'
    TOTAL_COLIFORM = 'Total Coliform'
    HEAVY_METALS = 'Heavy Metals'
    PHENOLS = 'Phenols'
    CYANIDE = 'Cyanide'
    SULFIDE = 'Sulfide'


class AirQualityParameter(PyEnum):
    AQI = 'Air Quality Index'
    PM25 = 'PM2.5'
    PM10 = 'PM10'
    NO2 = 'NO2'
    SO2 = 'SO2'
    CO = 'CO'
    O3 = 'O3'
    NH3 = 'NH3'
    LEAD = 'Pb'
    BENZENE = 'Benzene'
    BAP = 'Benzo(a)pyrene'
    ARSENIC = 'Arsenic'
    NICKEL = 'Nickel'


class NoiseParameter(PyEnum):
    LEQ = 'Leq'
    LMAX = 'Lmax'
    LMIN = 'Lmin'
    L10 = 'L10'
    L50 = 'L50'
    L90 = 'L90'
    LDN = 'Ldn'
    CNEL = 'CNEL'


class WeatherParameter(PyEnum):
    TEMPERATURE = 'Temperature'
    HUMIDITY = 'Humidity'
    WIND_SPEED = 'Wind Speed'
    WIND_DIRECTION = 'Wind Direction'
    PRESSURE = 'Atmospheric Pressure'
    PRECIPITATION = 'Precipitation'
    VISIBILITY = 'Visibility'
    UV_INDEX = 'UV Index'
    DEW_POINT = 'Dew Point'
    HEAT_INDEX = 'Heat Index'
    WIND_CHILL = 'Wind Chill'
    CLOUD_COVER = 'Cloud Cover'
    SOLAR_RADIATION = 'Solar Radiation'


class MonitoringStation(db.Model):
    __tablename__ = 'monitoring_stations'

    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    station_type = db.Column(db.String(50), nullable=False, index=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    zone = db.Column(db.String(100), index=True)
    address = db.Column(db.String(500))
    elevation = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    parameters = db.Column(db.JSON)
    metadata = db.Column(db.JSON)
    last_reading_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('ix_station_type_active', 'station_type', 'is_active'),
        Index('ix_station_zone_active', 'zone', 'is_active'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'station_id': self.station_id,
            'name': self.name,
            'station_type': self.station_type,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'zone': self.zone,
            'address': self.address,
            'elevation': self.elevation,
            'is_active': self.is_active,
            'parameters': self.parameters,
            'metadata': self.metadata,
            'last_reading_at': self.last_reading_at.isoformat() if self.last_reading_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class AirQualityReading(db.Model):
    __tablename__ = 'air_quality_readings'

    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('monitoring_stations.id'), nullable=False, index=True)
    aqi = db.Column(db.Integer, index=True)
    aqi_category = db.Column(db.String(50))
    pm25 = db.Column(db.Float)
    pm10 = db.Column(db.Float)
    no2 = db.Column(db.Float)
    so2 = db.Column(db.Float)
    co = db.Column(db.Float)
    o3 = db.Column(db.Float)
    nh3 = db.Column(db.Float)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    wind_direction = db.Column(db.Float)
    pressure = db.Column(db.Float)
    metadata = db.Column(db.JSON)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    station = db.relationship('MonitoringStation', backref='air_quality_readings')

    __table_args__ = (
        Index('ix_aq_station_recorded', 'station_id', 'recorded_at'),
        Index('ix_aq_aqi_recorded', 'aqi', 'recorded_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'station_id': self.station_id,
            'aqi': self.aqi,
            'aqi_category': self.aqi_category,
            'pm25': self.pm25,
            'pm10': self.pm10,
            'no2': self.no2,
            'so2': self.so2,
            'co': self.co,
            'o3': self.o3,
            'nh3': self.nh3,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction,
            'pressure': self.pressure,
            'metadata': self.metadata,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'created_at': self.created_at.isoformat()
        }


class WaterQualityReading(db.Model):
    __tablename__ = 'water_quality_readings'

    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('monitoring_stations.id'), nullable=False, index=True)
    ph = db.Column(db.Float)
    dissolved_oxygen = db.Column(db.Float)
    bod = db.Column(db.Float)
    cod = db.Column(db.Float)
    tss = db.Column(db.Float)
    tds = db.Column(db.Float)
    oil_grease = db.Column(db.Float)
    ammonia = db.Column(db.Float)
    nitrate = db.Column(db.Float)
    phosphate = db.Column(db.Float)
    temperature = db.Column(db.Float)
    turbidity = db.Column(db.Float)
    conductivity = db.Column(db.Float)
    salinity = db.Column(db.Float)
    fecal_coliform = db.Column(db.Float)
    total_coliform = db.Column(db.Float)
    heavy_metals = db.Column(db.JSON)
    phenols = db.Column(db.Float)
    cyanide = db.Column(db.Float)
    sulfide = db.Column(db.Float)
    metadata = db.Column(db.JSON)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    station = db.relationship('MonitoringStation', backref='water_quality_readings')

    __table_args__ = (
        Index('ix_wq_station_recorded', 'station_id', 'recorded_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'station_id': self.station_id,
            'ph': self.ph,
            'dissolved_oxygen': self.dissolved_oxygen,
            'bod': self.bod,
            'cod': self.cod,
            'tss': self.tss,
            'tds': self.tds,
            'oil_grease': self.oil_grease,
            'ammonia': self.ammonia,
            'nitrate': self.nitrate,
            'phosphate': self.phosphate,
            'temperature': self.temperature,
            'turbidity': self.turbidity,
            'conductivity': self.conductivity,
            'salinity': self.salinity,
            'fecal_coliform': self.fecal_coliform,
            'total_coliform': self.total_coliform,
            'heavy_metals': self.heavy_metals,
            'phenols': self.phenols,
            'cyanide': self.cyanide,
            'sulfide': self.sulfide,
            'metadata': self.metadata,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'created_at': self.created_at.isoformat()
        }


class NoiseReading(db.Model):
    __tablename__ = 'noise_readings'

    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('monitoring_stations.id'), nullable=False, index=True)
    leq = db.Column(db.Float, index=True)
    lmax = db.Column(db.Float)
    lmin = db.Column(db.Float)
    l10 = db.Column(db.Float)
    l50 = db.Column(db.Float)
    l90 = db.Column(db.Float)
    ldn = db.Column(db.Float)
    cnel = db.Column(db.Float)
    frequency_data = db.Column(db.JSON)
    metadata = db.Column(db.JSON)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    station = db.relationship('MonitoringStation', backref='noise_readings')

    __table_args__ = (
        Index('ix_noise_station_recorded', 'station_id', 'recorded_at'),
        Index('ix_noise_leq_recorded', 'leq', 'recorded_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'station_id': self.station_id,
            'leq': self.leq,
            'lmax': self.lmax,
            'lmin': self.lmin,
            'l10': self.l10,
            'l50': self.l50,
            'l90': self.l90,
            'ldn': self.ldn,
            'cnel': self.cnel,
            'frequency_data': self.frequency_data,
            'metadata': self.metadata,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'created_at': self.created_at.isoformat()
        }


class WeatherReading(db.Model):
    __tablename__ = 'weather_readings'

    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('monitoring_stations.id'), nullable=False, index=True)
    temperature = db.Column(db.Float)
    feels_like = db.Column(db.Float)
    humidity = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    wind_direction = db.Column(db.Float)
    wind_gust = db.Column(db.Float)
    pressure = db.Column(db.Float)
    precipitation = db.Column(db.Float)
    visibility = db.Column(db.Float)
    uv_index = db.Column(db.Float)
    dew_point = db.Column(db.Float)
    heat_index = db.Column(db.Float)
    wind_chill = db.Column(db.Float)
    cloud_cover = db.Column(db.Float)
    solar_radiation = db.Column(db.Float)
    weather_condition = db.Column(db.String(100))
    weather_description = db.Column(db.String(255))
    metadata = db.Column(db.JSON)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    station = db.relationship('MonitoringStation', backref='weather_readings')

    __table_args__ = (
        Index('ix_weather_station_recorded', 'station_id', 'recorded_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'station_id': self.station_id,
            'temperature': self.temperature,
            'feels_like': self.feels_like,
            'humidity': self.humidity,
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction,
            'wind_gust': self.wind_gust,
            'pressure': self.pressure,
            'precipitation': self.precipitation,
            'visibility': self.visibility,
            'uv_index': self.uv_index,
            'dew_point': self.dew_point,
            'heat_index': self.heat_index,
            'wind_chill': self.wind_chill,
            'cloud_cover': self.cloud_cover,
            'solar_radiation': self.solar_radiation,
            'weather_condition': self.weather_condition,
            'weather_description': self.weather_description,
            'metadata': self.metadata,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'created_at': self.created_at.isoformat()
        }


class EmissionReading(db.Model):
    __tablename__ = 'emission_readings'

    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('monitoring_stations.id'), nullable=False, index=True)
    source_type = db.Column(db.String(100), index=True)
    source_id = db.Column(db.String(100), index=True)
    co2 = db.Column(db.Float)
    ch4 = db.Column(db.Float)
    n2o = db.Column(db.Float)
    co2e = db.Column(db.Float, index=True)
    sox = db.Column(db.Float)
    nox = db.Column(db.Float)
    pm = db.Column(db.Float)
    voc = db.Column(db.Float)
    fuel_consumed = db.Column(db.Float)
    fuel_type = db.Column(db.String(50))
    operating_hours = db.Column(db.Float)
    metadata = db.Column(db.JSON)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    station = db.relationship('MonitoringStation', backref='emission_readings')

    __table_args__ = (
        Index('ix_emission_station_recorded', 'station_id', 'recorded_at'),
        Index('ix_emission_source_recorded', 'source_type', 'source_id', 'recorded_at'),
        Index('ix_emission_co2e_recorded', 'co2e', 'recorded_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'station_id': self.station_id,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'co2': self.co2,
            'ch4': self.ch4,
            'n2o': self.n2o,
            'co2e': self.co2e,
            'sox': self.sox,
            'nox': self.nox,
            'pm': self.pm,
            'voc': self.voc,
            'fuel_consumed': self.fuel_consumed,
            'fuel_type': self.fuel_type,
            'operating_hours': self.operating_hours,
            'metadata': self.metadata,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'created_at': self.created_at.isoformat()
        }


class EnvironmentalAlert(db.Model):
    __tablename__ = 'environmental_alerts'

    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    station_id = db.Column(db.Integer, db.ForeignKey('monitoring_stations.id'), index=True)
    parameter = db.Column(db.String(100), index=True)
    parameter_type = db.Column(db.String(50), index=True)
    threshold_type = db.Column(db.String(20))
    threshold_value = db.Column(db.Float)
    actual_value = db.Column(db.Float)
    severity = db.Column(db.String(20), index=True)
    status = db.Column(db.String(20), default='Active', index=True)
    message = db.Column(db.Text)
    acknowledged_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    acknowledged_at = db.Column(db.DateTime)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolved_at = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)
    metadata = db.Column(db.JSON)
    triggered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    station = db.relationship('MonitoringStation', backref='environmental_alerts')
    acknowledged_by = db.relationship('User', foreign_keys=[acknowledged_by_id], backref='acknowledged_env_alerts')
    resolved_by = db.relationship('User', foreign_keys=[resolved_by_id], backref='resolved_env_alerts')

    __table_args__ = (
        Index('ix_env_alert_station_status', 'station_id', 'status'),
        Index('ix_env_alert_parameter_status', 'parameter', 'status'),
        Index('ix_env_alert_severity_triggered', 'severity', 'triggered_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'station_id': self.station_id,
            'parameter': self.parameter,
            'parameter_type': self.parameter_type,
            'threshold_type': self.threshold_type,
            'threshold_value': self.threshold_value,
            'actual_value': self.actual_value,
            'severity': self.severity,
            'status': self.status,
            'message': self.message,
            'acknowledged_by_id': self.acknowledged_by_id,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_by_id': self.resolved_by_id,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_notes': self.resolution_notes,
            'metadata': self.metadata,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'created_at': self.created_at.isoformat()
        }


class ComplianceThreshold(db.Model):
    __tablename__ = 'compliance_thresholds'

    id = db.Column(db.Integer, primary_key=True)
    parameter = db.Column(db.String(100), nullable=False, index=True)
    parameter_type = db.Column(db.String(50), nullable=False, index=True)
    station_type = db.Column(db.String(50))
    zone = db.Column(db.String(100))
    min_value = db.Column(db.Float)
    max_value = db.Column(db.Float)
    warning_min = db.Column(db.Float)
    warning_max = db.Column(db.Float)
    critical_min = db.Column(db.Float)
    critical_max = db.Column(db.Float)
    unit = db.Column(db.String(50))
    regulation = db.Column(db.String(255))
    regulation_reference = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    effective_from = db.Column(db.DateTime)
    effective_to = db.Column(db.DateTime)
    metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('ix_threshold_param_type', 'parameter', 'parameter_type'),
        Index('ix_threshold_station_zone', 'station_type', 'zone'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'parameter': self.parameter,
            'parameter_type': self.parameter_type,
            'station_type': self.station_type,
            'zone': self.zone,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'warning_min': self.warning_min,
            'warning_max': self.warning_max,
            'critical_min': self.critical_min,
            'critical_max': self.critical_max,
            'unit': self.unit,
            'regulation': self.regulation,
            'regulation_reference': self.regulation_reference,
            'is_active': self.is_active,
            'effective_from': self.effective_from.isoformat() if self.effective_from else None,
            'effective_to': self.effective_to.isoformat() if self.effective_to else None,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }