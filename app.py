import os
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from models import db, User, EquipmentMetric, Alert, MemberSchedule, Member
import sqlite3
from datetime import datetime
from report_generator import generate_report

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
        # Simple rolling average for avg_session_duration
        if unit.avg_session_duration == 0:
            unit.avg_session_duration = data['session_duration']
        else:
            unit.avg_session_duration = (unit.avg_session_duration + data['session_duration']) / 2

    # Auto-generate Alert if uptime drops below 95%
    if unit.uptime_percent < 95.0:
        alert_msg = f"Low Uptime detected on {unit.equipment_name} at {unit.location}: {unit.uptime_percent}%"
        existing_alert = Alert.query.filter_by(message=alert_msg, is_resolved=False).first()
        if not existing_alert:
            new_alert = Alert(
                severity="Critical",
                message=alert_msg,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
                is_resolved=False
            )
            db.session.add(new_alert)

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
    return send_from_directory('.', filename)

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
            flash("Successfully registered for the StepManiaX Pilot!")
        return redirect(url_for('member_onboarding'))

    return render_template('onboarding_portal.html')

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
    # 1. Fetch CRM Summary using standard connection for performance
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT status, count(*) as count FROM leads GROUP BY status")
    crm_stats = cursor.fetchall()

    # 2. Fetch Equipment Metrics using SQLAlchemy
    metrics = EquipmentMetric.query.all()

    # 3. Fetch Alerts
    alerts = Alert.query.filter_by(is_resolved=False).order_by(Alert.timestamp.desc()).all()

    # 4. Fetch Schedules
    schedules = MemberSchedule.query.order_by(MemberSchedule.start_time.asc()).all()

    # 6. Fetch Onboarding Stats
    onboarding_stats = db.session.query(Member.onboarding_status, db.func.count(Member.id)).group_by(Member.onboarding_status).all()
    onboarding_dict = {status: count for status, count in onboarding_stats}

    # 5. Fetch Full Lead List for Status Manager
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, company FROM leads ORDER BY company ASC")
    leads_list = cursor.fetchall()

    return render_template('dashboard.html',
                           crm_stats=crm_stats,
                           metrics=metrics,
                           alerts=alerts,
                           schedules=schedules,
                           leads_list=leads_list,
                           onboarding_stats=onboarding_dict)

# Database Initialization Command
@app.cli.command("init-db")
def init_db():
    db.create_all()
    print(f"Database tables created in {db_path}.")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
