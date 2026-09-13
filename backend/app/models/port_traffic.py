from datetime import datetime
from app.extensions import db
from sqlalchemy import Index


class PortTrafficAnnual(db.Model):
    """Annual port-authority traffic statistics (public record, one row per fiscal year).
    Deliberately coarse-grained -- this is reference/historical context only,
    not a source for daily/hourly operational figures."""
    __tablename__ = 'port_traffic_annual'

    id = db.Column(db.Integer, primary_key=True)
    fiscal_year = db.Column(db.String(10), unique=True, nullable=False, index=True)
    total_cargo_mmt = db.Column(db.Float)
    container_teu = db.Column(db.Integer)
    vessel_calls = db.Column(db.Integer)
    container_vessels = db.Column(db.Integer)
    bulk_carrier_vessels = db.Column(db.Integer)
    tanker_vessels = db.Column(db.Integer)
    general_cargo_vessels = db.Column(db.Integer)
    avg_berth_occupancy_pct = db.Column(db.Float)
    avg_pre_berthing_delay_hrs = db.Column(db.Float)
    avg_turnaround_time_hrs = db.Column(db.Float)
    avg_output_per_ship_berth_day_t = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('ix_port_traffic_fiscal_year', 'fiscal_year'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'fiscal_year': self.fiscal_year,
            'total_cargo_mmt': self.total_cargo_mmt,
            'container_teu': self.container_teu,
            'vessel_calls': self.vessel_calls,
            'container_vessels': self.container_vessels,
            'bulk_carrier_vessels': self.bulk_carrier_vessels,
            'tanker_vessels': self.tanker_vessels,
            'general_cargo_vessels': self.general_cargo_vessels,
            'avg_berth_occupancy_pct': self.avg_berth_occupancy_pct,
            'avg_pre_berthing_delay_hrs': self.avg_pre_berthing_delay_hrs,
            'avg_turnaround_time_hrs': self.avg_turnaround_time_hrs,
            'avg_output_per_ship_berth_day_t': self.avg_output_per_ship_berth_day_t,
            'created_at': self.created_at.isoformat()
        }
