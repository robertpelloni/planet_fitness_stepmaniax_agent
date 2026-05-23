from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='Franchisee') # 'Admin', 'Franchisee', 'Member', 'Staff'
    franchise_id = db.Column(db.String(50), db.ForeignKey('leads.id'), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class EquipmentMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    franchise_id = db.Column(db.String(50), db.ForeignKey('leads.id'), nullable=True)
    uptime_percent = db.Column(db.Float, default=100.0)
    total_scans = db.Column(db.Integer, default=0)
    last_service_date = db.Column(db.String(50))
    avg_session_duration = db.Column(db.Float, default=0.0) # In minutes
    total_sessions = db.Column(db.Integer, default=0)
    maintenance_status = db.Column(db.String(50), default='Operational') # 'Operational', 'Needs Maintenance'

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    severity = db.Column(db.String(20), nullable=False) # 'Critical', 'Warning', 'Info'
    message = db.Column(db.String(250), nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)
    is_resolved = db.Column(db.Boolean, default=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment_metric.id'), nullable=True)

class MemberSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=True)
    member_name = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.String(50), nullable=False)
    duration_minutes = db.Column(db.Integer, default=10)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment_metric.id'))
    status = db.Column(db.String(20), default='Scheduled') # 'Scheduled', 'Completed', 'No-show'

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    onboarding_status = db.Column(db.String(50), default='Registered') # 'Registered', 'In Progress', 'Completed'
    registration_date = db.Column(db.String(50), nullable=False)
    franchise_id = db.Column(db.String(50), db.ForeignKey('leads.id'), nullable=True)
    points = db.Column(db.Integer, default=0)
    engagement_score = db.Column(db.Float, default=0.0)

class Lead(db.Model):
    __tablename__ = 'leads'
    id = db.Column(db.String(50), primary_key=True)
    company = db.Column(db.String(100), nullable=False)
    contact_name = db.Column(db.String(100))
    title = db.Column(db.String(100))
    email = db.Column(db.String(100))
    region = db.Column(db.String(50))
    status = db.Column(db.String(50), default='Identified')
    priority = db.Column(db.String(20), default='Medium')
    notes = db.Column(db.Text)
    num_clubs = db.Column(db.Integer)
    retention_lift = db.Column(db.Float, default=0.03)
    avg_monthly_fee = db.Column(db.Float, default=15.0)
    projected_annual_profit = db.Column(db.Float)
    follow_up_count = db.Column(db.Integer, default=0)
    last_contact_date = db.Column(db.String(50))
    public_token = db.Column(db.String(100), unique=True)

class OutreachLog(db.Model):
    __tablename__ = 'outreach_logs'
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.String(50), db.ForeignKey('leads.id'), nullable=False)
    date_sent = db.Column(db.String(50), nullable=False)
    channel = db.Column(db.String(50))
    notes = db.Column(db.Text)

class Webhook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    franchise_id = db.Column(db.String(50), nullable=True) # None for Global Admin
    url = db.Column(db.String(250), nullable=False)
    service = db.Column(db.String(50), default='Discord') # 'Discord', 'Slack'

class TelemetryHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment_metric.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=True)
    timestamp = db.Column(db.String(50), nullable=False)
    scans_count = db.Column(db.Integer, default=0)
