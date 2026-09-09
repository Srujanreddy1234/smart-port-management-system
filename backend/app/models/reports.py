from datetime import datetime
from enum import Enum as PyEnum
from app.extensions import db
from sqlalchemy import Enum, Index


class ReportType(PyEnum):
    OPERATIONS = 'Operations'
    FINANCIAL = 'Financial'
    ENVIRONMENTAL = 'Environmental'
    SECURITY = 'Security'
    MAINTENANCE = 'Maintenance'
    VESSEL_TRAFFIC = 'Vessel Traffic'
    CONTAINER_THROUGHPUT = 'Container Throughput'
    TRUCK_OPERATIONS = 'Truck Operations'
    EQUIPMENT_PERFORMANCE = 'Equipment Performance'
    CUSTOM = 'Custom'


class ReportFormat(PyEnum):
    PDF = 'PDF'
    CSV = 'CSV'
    EXCEL = 'Excel'
    JSON = 'JSON'


class ReportStatus(PyEnum):
    PENDING = 'Pending'
    GENERATING = 'Generating'
    READY = 'Ready'
    FAILED = 'Failed'
    EXPIRED = 'Expired'


class ReportSchedule(PyEnum):
    DAILY = 'Daily'
    WEEKLY = 'Weekly'
    MONTHLY = 'Monthly'
    QUARTERLY = 'Quarterly'
    YEARLY = 'Yearly'
    ON_DEMAND = 'On Demand'


class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    report_type = db.Column(Enum(ReportType, values_callable=lambda x: x.value), nullable=False, index=True)
    description = db.Column(db.Text)
    format = db.Column(Enum(ReportFormat, values_callable=lambda x: x.value), nullable=False, default=ReportFormat.PDF, index=True)
    status = db.Column(Enum(ReportStatus, values_callable=lambda x: x.value), default=ReportStatus.PENDING, nullable=False, index=True)
    schedule = db.Column(Enum(ReportSchedule, values_callable=lambda x: x.value), default=ReportSchedule.ON_DEMAND, nullable=False)
    generated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    parameters = db.Column(db.JSON)
    date_from = db.Column(db.DateTime, index=True)
    date_to = db.Column(db.DateTime, index=True)
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    download_count = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    is_scheduled = db.Column(db.Boolean, default=False)
    next_generation_at = db.Column(db.DateTime)
    report_metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    generated_by = db.relationship('User', foreign_keys=[generated_by_id], backref='generated_reports')

    __table_args__ = (
        Index('ix_report_type_status', 'report_type', 'status'),
        Index('ix_report_generated_by_date', 'generated_by_id', 'created_at'),
        Index('ix_report_schedule_next', 'is_scheduled', 'next_generation_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'title': self.title,
            'report_type': self.report_type.value,
            'description': self.description,
            'format': self.format.value,
            'status': self.status.value,
            'schedule': self.schedule.value,
            'generated_by_id': self.generated_by_id,
            'parameters': self.parameters,
            'date_from': self.date_from.isoformat() if self.date_from else None,
            'date_to': self.date_to.isoformat() if self.date_to else None,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'download_count': self.download_count,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_scheduled': self.is_scheduled,
            'next_generation_at': self.next_generation_at.isoformat() if self.next_generation_at else None,
            'metadata': self.report_metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class ReportTemplate(db.Model):
    __tablename__ = 'report_templates'

    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    report_type = db.Column(Enum(ReportType, values_callable=lambda x: x.value), nullable=False, index=True)
    description = db.Column(db.Text)
    template_file = db.Column(db.String(500))
    parameters_schema = db.Column(db.JSON)
    default_format = db.Column(Enum(ReportFormat, values_callable=lambda x: x.value), default=ReportFormat.PDF)
    is_active = db.Column(db.Boolean, default=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_templates')

    def to_dict(self):
        return {
            'id': self.id,
            'template_id': self.template_id,
            'name': self.name,
            'report_type': self.report_type.value,
            'description': self.description,
            'template_file': self.template_file,
            'parameters_schema': self.parameters_schema,
            'default_format': self.default_format.value,
            'is_active': self.is_active,
            'created_by_id': self.created_by_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class DashboardWidget(db.Model):
    __tablename__ = 'dashboard_widgets'

    id = db.Column(db.Integer, primary_key=True)
    widget_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    widget_type = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), index=True)
    description = db.Column(db.Text)
    data_source = db.Column(db.String(255))
    api_endpoint = db.Column(db.String(255))
    refresh_interval = db.Column(db.Integer, default=300)
    default_config = db.Column(db.JSON)
    chart_config = db.Column(db.JSON)
    position = db.Column(db.JSON)
    is_active = db.Column(db.Boolean, default=True)
    required_roles = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('ix_widget_category_active', 'category', 'is_active'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'widget_id': self.widget_id,
            'name': self.name,
            'widget_type': self.widget_type,
            'category': self.category,
            'description': self.description,
            'data_source': self.data_source,
            'api_endpoint': self.api_endpoint,
            'refresh_interval': self.refresh_interval,
            'default_config': self.default_config,
            'chart_config': self.chart_config,
            'position': self.position,
            'is_active': self.is_active,
            'required_roles': self.required_roles,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class UserDashboard(db.Model):
    __tablename__ = 'user_dashboards'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    dashboard_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    layout = db.Column(db.JSON)
    widgets = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship('User', foreign_keys=[user_id], backref='dashboards')

    __table_args__ = (
        Index('ix_dashboard_user_default', 'user_id', 'is_default'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'dashboard_id': self.dashboard_id,
            'name': self.name,
            'is_default': self.is_default,
            'layout': self.layout,
            'widgets': self.widgets,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }