from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='Franchisee') # 'Admin', 'Franchisee'
    franchise_id = db.Column(db.String(50), nullable=True) # ID of the Lead they manage

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class EquipmentMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    uptime_percent = db.Column(db.Float, default=100.0)
    total_scans = db.Column(db.Integer, default=0)
    last_service_date = db.Column(db.String(50))
    avg_session_duration = db.Column(db.Float, default=0.0) # In minutes
    total_sessions = db.Column(db.Integer, default=0)

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    severity = db.Column(db.String(20), nullable=False) # 'Critical', 'Warning', 'Info'
    message = db.Column(db.String(250), nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)
    is_resolved = db.Column(db.Boolean, default=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment_metric.id'), nullable=True)

class MemberSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_name = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.String(50), nullable=False)
    duration_minutes = db.Column(db.Integer, default=10)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment_metric.id'))

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    onboarding_status = db.Column(db.String(50), default='Registered') # 'Registered', 'In Progress', 'Completed'
    registration_date = db.Column(db.String(50), nullable=False)
    club_id = db.Column(db.String(100)) # Linked to the Lead/Club location

class Webhook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    franchise_id = db.Column(db.String(50), nullable=True) # None for Global Admin
    url = db.Column(db.String(250), nullable=False)
    service = db.Column(db.String(50), default='Discord') # 'Discord', 'Slack'
