import os
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from flask_wtf.csrf import CSRFProtect
from models import db, User, EquipmentMetric, Alert, MemberSchedule, Member, Webhook, Lead, OutreachLog, TelemetryHistory
from datetime import datetime
import config
from report_generator import generate_report
from notifications import send_notification

app = Flask(__name__)
# Secret key should be loaded from environment for production
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')
# Use absolute path to project root DB for consistency
project_root = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(project_root, 'crm.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if api_key and api_key == config.API_KEY:
            return f(*args, **kwargs)
        return {"error": "Unauthorized access"}, 401
    return decorated_function

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if current_user.role not in roles:
                if current_user.role == 'Member':
                    flash("Access restricted to management only.")
                    return redirect(url_for('member_dashboard'))
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Routes
@app.route('/')
@login_required
def index():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            if user.role == 'Member':
                return redirect(url_for('member_dashboard'))
            if user.role == 'Staff':
                return redirect(url_for('staff_dashboard'))
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/staff/api/metrics')
@login_required
@role_required(['Admin', 'Staff'])
def staff_api_metrics():
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')
    if is_admin:
        metrics = EquipmentMetric.query.all()
    else:
        metrics = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()
    return render_template('partials/staff_metrics.html', metrics=metrics)

@app.route('/staff/api/maintenance')
@login_required
@role_required(['Admin', 'Staff'])
def staff_api_maintenance():
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')
    if is_admin:
        metrics = EquipmentMetric.query.all()
    else:
        metrics = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()
    return render_template('partials/staff_maintenance.html', metrics=metrics)

@app.route('/staff/api/alerts')
@login_required
@role_required(['Admin', 'Staff'])
def staff_api_alerts():
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')
    if is_admin:
        alerts = Alert.query.filter_by(is_resolved=False).order_by(Alert.timestamp.desc()).limit(10).all()
    else:
        metrics = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()
        metric_ids = [m.id for m in metrics]
        alerts = Alert.query.filter(Alert.equipment_id.in_(metric_ids), Alert.is_resolved == False).order_by(Alert.timestamp.desc()).limit(10).all()
    return render_template('partials/staff_alerts.html', alerts=alerts)

@app.route('/staff/dashboard')
@login_required
@role_required(['Admin', 'Staff'])
def staff_dashboard():
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')

    if is_admin:
        metrics = EquipmentMetric.query.all()
        alerts = Alert.query.filter_by(is_resolved=False).order_by(Alert.timestamp.desc()).limit(10).all()
        schedules = MemberSchedule.query.order_by(MemberSchedule.start_time.asc()).all()
    else:
        metrics = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()
        metric_ids = [m.id for m in metrics]
        alerts = Alert.query.filter(Alert.equipment_id.in_(metric_ids), Alert.is_resolved == False).order_by(Alert.timestamp.desc()).limit(10).all()
        schedules = MemberSchedule.query.filter(MemberSchedule.equipment_id.in_(metric_ids)).order_by(MemberSchedule.start_time.asc()).all()

    return render_template('staff_dashboard.html',
                           metrics=metrics,
                           alerts=alerts,
                           schedules=schedules,
                           franchise_name=current_user.franchise_id or "Global Admin")

@app.route('/member/dashboard', methods=['GET', 'POST'])
@login_required
def member_dashboard():
    if current_user.role != 'Member':
        return redirect(url_for('dashboard'))

    member = Member.query.filter_by(user_id=current_user.id).first()
    if not member:
        flash("Member record not found.")
        return redirect(url_for('logout'))

    if request.method == 'POST':
        member.name = request.form.get('name')
        # We don't allow email change for now as it's the username
        db.session.commit()
        flash("Profile updated successfully!")

    return render_template('member_dashboard.html', member=member)

@app.route('/api/v1/telemetry', methods=['POST'])
@csrf.exempt # Exempting for machine-to-machine API calls
@require_api_key
def telemetry():
    """
    Endpoint for StepManiaX units to POST telemetry data.
    Expected JSON: { "equipment_id": int, "uptime_percent": float, "scans_increment": int, "session_duration": float }
    """
    data = request.get_json()
    if not data or 'equipment_id' not in data:
        return {"error": "Invalid telemetry packet"}, 400

    unit = EquipmentMetric.query.get(data['equipment_id'])
    if not unit:
        return {"error": "Unit not found"}, 404

    # Update Metrics
    if 'uptime_percent' in data:
        unit.uptime_percent = data['uptime_percent']

    if 'scans_increment' in data:
        unit.total_scans += data['scans_increment']
        # Log to history
        history = TelemetryHistory(
            equipment_id=unit.id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            scans_count=data['scans_increment']
        )
        db.session.add(history)

    if 'session_duration' in data:
        # Proper moving average: (old_avg * count + new_val) / (count + 1)
        new_duration = data['session_duration']
        unit.avg_session_duration = ((unit.avg_session_duration * unit.total_sessions) + new_duration) / (unit.total_sessions + 1)
        unit.total_sessions += 1

    # Auto-generate Alert if uptime drops below threshold
    if unit.uptime_percent < config.UPTIME_THRESHOLD:
        alert_msg = f"Low Uptime detected on {unit.equipment_name} at {unit.location}: {unit.uptime_percent}%"
        existing_alert = Alert.query.filter_by(message=alert_msg, is_resolved=False).first()
        if not existing_alert:
            new_alert = Alert(
                severity="Critical",
                message=alert_msg,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
                is_resolved=False,
                equipment_id=unit.id
            )
            db.session.add(new_alert)
            # Update maintenance status
            unit.maintenance_status = 'Needs Maintenance'
            send_notification(f"⚠️ [CRITICAL] {alert_msg}", franchise_id=unit.franchise_id)

    db.session.commit()
    return {"status": "success", "unit": unit.equipment_name}, 200

@app.route('/update_lead_status', methods=['POST'])
@login_required
@role_required(['Admin', 'Franchisee'])
def update_lead_status():
    lead_id = request.form.get('lead_id')
    new_status = request.form.get('status')

    lead = Lead.query.get(lead_id)
    if lead:
        lead.status = new_status
        db.session.commit()
        flash(f"Status updated for lead {lead_id} to {new_status}")
    else:
        flash(f"Error: Lead {lead_id} not found.")

    return redirect(url_for('dashboard'))

@app.route('/resources/<path:filename>')
@login_required
@role_required(['Admin', 'Franchisee'])
def serve_resources(filename):
    # Restrict to technical/alignment docs directory for security
    return send_from_directory('technical_docs', filename)

@app.route('/onboard', methods=['GET', 'POST'])
def member_onboarding():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        franchise_id = request.form.get('franchise_id')

        # Check if member already exists
        existing = Member.query.filter_by(email=email).first()
        if existing:
            flash("You are already registered for this pilot!")
        else:
            # Create User first
            new_user = User(username=email, role='Member')
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.flush() # Get ID

            new_member = Member(
                name=name,
                email=email,
                franchise_id=franchise_id,
                registration_date=datetime.now().strftime("%Y-%m-%d"),
                user_id=new_user.id
            )
            db.session.add(new_member)
            db.session.commit()
            send_notification(f"🎉 New Pilot Registration: {name}", franchise_id=franchise_id)
            flash("Successfully registered! You can now log in to your dashboard.")
            return redirect(url_for('login'))
        return redirect(url_for('member_onboarding'))

    # Get available franchise locations for the dropdown
    leads = Lead.query.filter(Lead.status.contains('Pilot')).all()
    return render_template('onboarding_portal.html', leads=leads)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Franchisee'])
def settings():
    if request.method == 'POST':
        url = request.form.get('url')
        service = request.form.get('service')

        new_hook = Webhook(
            url=url,
            service=service,
            franchise_id=current_user.franchise_id if current_user.role != 'Admin' else None
        )
        db.session.add(new_hook)
        db.session.commit()
        flash(f"Webhook added successfully for {service}")
        return redirect(url_for('settings'))

    if current_user.role == 'Admin':
        webhooks = Webhook.query.all()
        users = User.query.all()
    else:
        webhooks = Webhook.query.filter_by(franchise_id=current_user.franchise_id).all()
        users = []

    return render_template('settings.html', webhooks=webhooks, users=users)

@app.route('/api/v1/analytics/usage', methods=['GET'])
@login_required
@role_required(['Admin', 'Franchisee'])
def api_usage_analytics():
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')

    if is_admin:
        metrics = EquipmentMetric.query.all()
    else:
        metrics = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()

    metric_ids = [m.id for m in metrics]

    # Simple aggregation by date from TelemetryHistory
    # In a real app we'd use a group_by on substr(timestamp, 1, 10)
    history = TelemetryHistory.query.filter(TelemetryHistory.equipment_id.in_(metric_ids)).all()

    daily_stats = {}
    for entry in history:
        date = entry.timestamp[:10]
        daily_stats[date] = daily_stats.get(date, 0) + entry.scans_count

    # Sort by date
    sorted_dates = sorted(daily_stats.keys())

    return {
        "labels": sorted_dates,
        "data": [daily_stats[d] for d in sorted_dates]
    }, 200

@app.route('/api/v1/members', methods=['GET'])
@csrf.exempt
@require_api_key
def api_list_members():
    franchise_id = request.args.get('franchise_id')
    if not franchise_id:
        members = Member.query.all()
    else:
        members = Member.query.filter_by(franchise_id=franchise_id).all()

    return {
        "members": [
            {
                "id": m.id,
                "name": m.name,
                "email": m.email,
                "onboarding_status": m.onboarding_status,
                "registration_date": m.registration_date,
                "franchise_id": m.franchise_id
            } for m in members
        ]
    }, 200

@app.route('/api/v1/members', methods=['POST'])
@csrf.exempt
@require_api_key
def api_create_member():
    data = request.get_json()
    if not data or 'email' not in data or 'name' not in data or 'password' not in data:
        return {"error": "Missing required fields"}, 400

    # Check if exists
    if User.query.filter_by(username=data['email']).first():
        return {"error": "User already exists"}, 409

    # Logic similar to /onboard but for API
    new_user = User(
        username=data['email'],
        role='Member',
        franchise_id=data.get('franchise_id', current_user.franchise_id)
    )
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.flush()

    new_member = Member(
        name=data['name'],
        email=data['email'],
        user_id=new_user.id,
        franchise_id=new_user.franchise_id,
        registration_date=datetime.now().strftime("%Y-%m-%d"),
        onboarding_status=data.get('onboarding_status', 'Registered')
    )
    db.session.add(new_member)
    db.session.commit()

    return {"status": "success", "member_id": new_member.id}, 201

@app.route('/api/v1/members/<int:member_id>', methods=['GET', 'PUT', 'DELETE'])
@csrf.exempt
@require_api_key
def api_member_detail(member_id):
    member = Member.query.get_or_404(member_id)

    if request.method == 'GET':
        return {
            "id": member.id,
            "name": member.name,
            "email": member.email,
            "onboarding_status": member.onboarding_status,
            "registration_date": member.registration_date,
            "franchise_id": member.franchise_id
        }

    if request.method == 'PUT':
        data = request.get_json()
        if 'name' in data:
            member.name = data['name']
        if 'onboarding_status' in data:
            member.onboarding_status = data['onboarding_status']
        db.session.commit()
        return {"status": "updated"}

    if request.method == 'DELETE':
        # Remove User account too
        user = User.query.get(member.user_id)
        if user:
            db.session.delete(user)
        db.session.delete(member)
        db.session.commit()
        return {"status": "deleted"}

@app.route('/generate_report/<int:unit_id>')
@login_required
@role_required(['Admin', 'Franchisee'])
def generate_unit_report(unit_id):
    filepath = generate_report(unit_id)
    if filepath:
        flash(f"Performance report generated successfully: {os.path.basename(filepath)}")
    else:
        flash("Failed to generate performance report.")
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
@role_required(['Admin', 'Franchisee'])
def dashboard():
    # Multi-tenant logic: Filter by franchise_id if user is not an Admin
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')

    # 1. CRM Summary
    if is_admin:
        crm_stats = db.session.query(Lead.status, db.func.count(Lead.id).label('count')).group_by(Lead.status).all()
    else:
        crm_stats = db.session.query(Lead.status, db.func.count(Lead.id).label('count')).filter_by(id=franchise_id).group_by(Lead.status).all()

    # 2. Equipment Metrics
    if is_admin:
        metrics = EquipmentMetric.query.all()
    else:
        metrics = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()

    metric_ids = [m.id for m in metrics]

    # 3. Alerts
    if is_admin:
        alerts = Alert.query.filter_by(is_resolved=False).order_by(Alert.timestamp.desc()).all()
    else:
        alerts = Alert.query.filter(Alert.equipment_id.in_(metric_ids), Alert.is_resolved == False).order_by(Alert.timestamp.desc()).all()

    # 4. Schedules
    if is_admin:
        schedules = MemberSchedule.query.order_by(MemberSchedule.start_time.asc()).all()
    else:
        schedules = MemberSchedule.query.filter(MemberSchedule.equipment_id.in_(metric_ids)).order_by(MemberSchedule.start_time.asc()).all()

    # 6. Onboarding Stats
    if is_admin:
        onboarding_stats = db.session.query(Member.onboarding_status, db.func.count(Member.id)).group_by(Member.onboarding_status).all()
    else:
        onboarding_stats = db.session.query(Member.onboarding_status, db.func.count(Member.id)).filter_by(franchise_id=franchise_id).group_by(Member.onboarding_status).all()

    onboarding_dict = {status: count for status, count in onboarding_stats}

    # 5. Lead List
    if is_admin:
        leads_list = Lead.query.order_by(Lead.company.asc()).all()
    else:
        leads_list = Lead.query.filter_by(id=franchise_id).all()

    return render_template('dashboard.html',
                           crm_stats=crm_stats,
                           metrics=metrics,
                           alerts=alerts,
                           schedules=schedules,
                           leads_list=leads_list,
                           onboarding_stats=onboarding_dict,
                           is_admin=is_admin,
                           franchise_name=leads_list[0].company if not is_admin and leads_list else "Global Admin")

# Database Initialization Command
@app.cli.command("init-db")
def init_db():
    db.create_all()
    print(f"Database tables created in {db_path}.")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
