import os
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from models import db, User, EquipmentMetric, Alert, MemberSchedule, Member, Webhook
import sqlite3
from datetime import datetime
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
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/v1/telemetry', methods=['POST'])
@csrf.exempt # Exempting for machine-to-machine API calls
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

    if 'session_duration' in data:
        # Proper moving average: (old_avg * count + new_val) / (count + 1)
        new_duration = data['session_duration']
        unit.avg_session_duration = ((unit.avg_session_duration * unit.total_sessions) + new_duration) / (unit.total_sessions + 1)
        unit.total_sessions += 1

    # Auto-generate Alert if uptime drops below 95%
    if unit.uptime_percent < 95.0:
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
            # Find franchise_id for this location to send notification
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Simple heuristic: location contains club name which is usually in leads.company
            cursor.execute("SELECT id FROM leads WHERE ? LIKE '%' || company || '%'", (unit.location,))
            lead = cursor.fetchone()
            fid = lead['id'] if lead else None
            send_notification(f"⚠️ [CRITICAL] {alert_msg}", franchise_id=fid)

    db.session.commit()
    return {"status": "success", "unit": unit.equipment_name}, 200

@app.route('/update_lead_status', methods=['POST'])
@login_required
def update_lead_status():
    lead_id = request.form.get('lead_id')
    new_status = request.form.get('status')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE leads SET status = ? WHERE id = ?", (new_status, lead_id))
    conn.commit()
    conn.close()

    flash(f"Status updated for lead {lead_id} to {new_status}")
    return redirect(url_for('dashboard'))

@app.route('/resources/<path:filename>')
@login_required
def serve_resources(filename):
    # Restrict to technical/alignment docs directory for security
    return send_from_directory('technical_docs', filename)

@app.route('/onboard', methods=['GET', 'POST'])
def member_onboarding():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        club_id = request.form.get('club_id')

        # Check if member already exists
        existing = Member.query.filter_by(email=email).first()
        if existing:
            flash("You are already registered for this pilot!")
        else:
            new_member = Member(
                name=name,
                email=email,
                club_id=club_id,
                registration_date=datetime.now().strftime("%Y-%m-%d")
            )
            db.session.add(new_member)
            db.session.commit()
            send_notification(f"🎉 New Pilot Registration: {name} at {club_id}", franchise_id=club_id)
            flash("Successfully registered for the StepManiaX Pilot!")
        return redirect(url_for('member_onboarding'))

    return render_template('onboarding_portal.html')

@app.route('/settings', methods=['GET', 'POST'])
@login_required
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
    else:
        webhooks = Webhook.query.filter_by(franchise_id=current_user.franchise_id).all()

    return render_template('settings.html', webhooks=webhooks)

@app.route('/generate_report/<int:unit_id>')
@login_required
def generate_unit_report(unit_id):
    filepath = generate_report(unit_id)
    if filepath:
        flash(f"Performance report generated successfully: {os.path.basename(filepath)}")
    else:
        flash("Failed to generate performance report.")
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Multi-tenant logic: Filter by franchise_id if user is not an Admin
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. CRM Summary
    if is_admin:
        cursor.execute("SELECT status, count(*) as count FROM leads GROUP BY status")
    else:
        cursor.execute("SELECT status, count(*) as count FROM leads WHERE id = ? GROUP BY status", (franchise_id,))
    crm_stats = cursor.fetchall()

    # 2. Equipment Metrics
    if is_admin:
        metrics = EquipmentMetric.query.all()
    else:
        # We need to link equipment_metric to leads via location or a new FK
        # For now, let's assume location contains the company name
        cursor.execute("SELECT company FROM leads WHERE id = ?", (franchise_id,))
        company = cursor.fetchone()['company']
        metrics = EquipmentMetric.query.filter(EquipmentMetric.location.contains(company)).all()

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
        onboarding_stats = db.session.query(Member.onboarding_status, db.func.count(Member.id)).filter_by(club_id=franchise_id).group_by(Member.onboarding_status).all()

    onboarding_dict = {status: count for status, count in onboarding_stats}

    # 5. Lead List
    if is_admin:
        cursor.execute("SELECT id, company FROM leads ORDER BY company ASC")
    else:
        cursor.execute("SELECT id, company FROM leads WHERE id = ?", (franchise_id,))
    leads_list = cursor.fetchall()

    return render_template('dashboard.html',
                           crm_stats=crm_stats,
                           metrics=metrics,
                           alerts=alerts,
                           schedules=schedules,
                           leads_list=leads_list,
                           onboarding_stats=onboarding_dict,
                           is_admin=is_admin,
                           franchise_name=leads_list[0]['company'] if not is_admin and leads_list else "Global Admin")

# Database Initialization Command
@app.cli.command("init-db")
def init_db():
    db.create_all()
    print(f"Database tables created in {db_path}.")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
