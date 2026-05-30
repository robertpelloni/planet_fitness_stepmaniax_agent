from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='Franchisee') # 'Admin', 'Franchisee', 'Member', 'Staff'
    franchise_id = db.Column(db.String(50), db.ForeignKey('leads.id'), nullable=True)
    last_login = db.Column(db.String(50))
    failed_login_attempts = db.Column(db.Integer, default=0)
    is_locked = db.Column(db.Boolean, default=False)

    # Security Enhancements (v4.9.0)
    mfa_secret = db.Column(db.String(32))
    mfa_enabled = db.Column(db.Boolean, default=False)
    api_key = db.Column(db.String(64), unique=True)
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiry = db.Column(db.String(50))

    # Granular Permissions (v4.0.0)
    perm_crm_view = db.Column(db.Boolean, default=True)
    perm_crm_edit = db.Column(db.Boolean, default=False)
    perm_ops_view = db.Column(db.Boolean, default=True)
    perm_revenue_view = db.Column(db.Boolean, default=False)
    perm_admin_access = db.Column(db.Boolean, default=False)

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
    last_heartbeat = db.Column(db.String(50))
    predictive_health_score = db.Column(db.Float, default=100.0)
    region_cluster = db.Column(db.String(50), default='US-EAST-1')

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    severity = db.Column(db.String(20), nullable=False) # 'Critical', 'Warning', 'Info'
    message = db.Column(db.String(250), nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)
    is_resolved = db.Column(db.Boolean, default=False)
    acknowledged_by = db.Column(db.String(100))
    resolved_at = db.Column(db.String(50))
    resolved_by = db.Column(db.String(100))
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
    biometric_token = db.Column(db.String(100), unique=True)
    nfc_uid = db.Column(db.String(50), unique=True)

    # Relationship to WorkoutPlan
    workout_plan = db.relationship('WorkoutPlan', backref='member', uselist=False)

class WorkoutPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    target_scans = db.Column(db.Integer, default=1000)
    target_duration = db.Column(db.Integer, default=300) # In minutes
    created_at = db.Column(db.String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

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
    portal_views = db.Column(db.Integer, default=0)
    region_cluster = db.Column(db.String(50), default='US-EAST-1')

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
    duration_minutes = db.Column(db.Float, default=0.0)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(250), nullable=False)
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.String(50), nullable=False)

class AutomationHeartbeat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(100), unique=True, nullable=False)
    last_run = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='Healthy')

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=True)
    franchise_id = db.Column(db.String(50), db.ForeignKey('leads.id'), nullable=True)
    rating = db.Column(db.Integer, nullable=False) # 1-5 scale
    comment = db.Column(db.Text)
    category = db.Column(db.String(50), default='General') # 'Equipment', 'Support', 'Experience'
    timestamp = db.Column(db.String(50), nullable=False)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='USD')
    status = db.Column(db.String(20), default='Pending') # 'Pending', 'Completed', 'Failed'
    transaction_id = db.Column(db.String(100), unique=True)
    timestamp = db.Column(db.String(50), nullable=False)
