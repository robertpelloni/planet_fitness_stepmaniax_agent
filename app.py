import os
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from flask_wtf.csrf import CSRFProtect
from models import db, User, EquipmentMetric, Alert, MemberSchedule, Member, Webhook, Lead, OutreachLog, TelemetryHistory, AuditLog, AutomationHeartbeat, Feedback, Payment
from datetime import datetime
import subprocess
import config
import analytics
import secrets
from report_generator import generate_report
from notifications import send_notification
from gateways import get_payment_gateway

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

def log_security_event(user_id, action):
    log = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=request.remote_addr,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.session.add(log)
    db.session.commit()

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Support both X-API-KEY header and standard session auth (v3.9.0)
        api_key = request.headers.get('X-API-KEY') or request.args.get('api_key')
        if (api_key and api_key == config.API_KEY) or (current_user and current_user.is_authenticated):
            return f(*args, **kwargs)
        return {"error": "Unauthorized access. API-KEY or Session required."}, 401
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

        if user:
            if user.is_locked:
                log_security_event(user.id, f"Login attempt on locked account: {username}")
                flash('Account is locked due to too many failed attempts. Please contact an administrator.')
                return render_template('login.html')

            if user.check_password(password):
                user.failed_login_attempts = 0
                user.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db.session.commit()
                login_user(user)
                log_security_event(user.id, f"Successful login: {username}")

                if user.role == 'Member':
                    return redirect(url_for('member_dashboard'))
                if user.role == 'Staff':
                    return redirect(url_for('staff_dashboard'))
                return redirect(url_for('dashboard'))
            else:
                if user.failed_login_attempts is None:
                    user.failed_login_attempts = 0
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.is_locked = True
                    log_security_event(user.id, f"Account locked after 5 failures: {username}")
                else:
                    log_security_event(user.id, f"Failed login attempt: {username} (Attempt {user.failed_login_attempts})")
                db.session.commit()

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

    # Determine online status
    for m in metrics:
        if m.last_heartbeat:
            last_hb = datetime.strptime(m.last_heartbeat, "%Y-%m-%d %H:%M:%S")
            diff = (datetime.now() - last_hb).total_seconds()
            m.is_online = diff < 300
        else:
            m.is_online = False

    if request.args.get('view') == 'ops':
        return render_template('partials/facility_metrics.html', metrics=metrics)
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

@app.route('/manager/api/activity')
@login_required
@role_required(['Admin', 'Franchisee'])
def manager_api_activity():
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')

    if is_admin:
        units = EquipmentMetric.query.all()
    else:
        units = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()

    metric_ids = [u.id for u in units]

    activity = db.session.query(TelemetryHistory, Member.name)\
        .outerjoin(Member, TelemetryHistory.member_id == Member.id)\
        .filter(TelemetryHistory.equipment_id.in_(metric_ids))\
        .order_by(TelemetryHistory.timestamp.desc()).limit(10).all()

    return render_template('partials/manager_activity.html', activity=activity)

@app.route('/staff/api/alerts')
@login_required
@role_required(['Admin', 'Staff', 'Franchisee'])
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

@app.route('/staff/members')
@login_required
@role_required(['Admin', 'Staff'])
def staff_members():
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')

    if is_admin:
        members = Member.query.all()
    else:
        members = Member.query.filter_by(franchise_id=franchise_id).all()

    return render_template('staff_members.html', members=members)

@app.route('/staff/members/update/<int:member_id>', methods=['POST'])
@login_required
@role_required(['Admin', 'Staff'])
def staff_update_member_status(member_id):
    member = Member.query.get_or_404(member_id)
    new_status = request.form.get('status')

    # Check multi-tenant permission
    if current_user.role != 'Admin' and member.franchise_id != current_user.franchise_id:
        abort(403)

    member.onboarding_status = new_status
    db.session.commit()
    flash(f"Status updated for member {member.name}")
    return redirect(url_for('staff_members'))

@app.route('/staff/operations')
@login_required
@role_required(['Admin', 'Staff'])
def facility_operations():
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')

    if is_admin:
        metrics = EquipmentMetric.query.all()
        alerts = Alert.query.filter_by(is_resolved=False).order_by(Alert.timestamp.desc()).limit(20).all()
        today = datetime.now().strftime("%Y-%m-%d")
        schedules = MemberSchedule.query.filter(MemberSchedule.start_time.contains(today)).order_by(MemberSchedule.start_time.asc()).all()
    else:
        metrics = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()
        metric_ids = [m.id for m in metrics]
        alerts = Alert.query.filter(Alert.equipment_id.in_(metric_ids), Alert.is_resolved == False).order_by(Alert.timestamp.desc()).limit(20).all()
        today = datetime.now().strftime("%Y-%m-%d")
        schedules = MemberSchedule.query.filter(MemberSchedule.equipment_id.in_(metric_ids), MemberSchedule.start_time.contains(today)).order_by(MemberSchedule.start_time.asc()).all()

    # Determine online status (heartbeat within last 5 minutes)
    for m in metrics:
        if m.last_heartbeat:
            last_hb = datetime.strptime(m.last_heartbeat, "%Y-%m-%d %H:%M:%S")
            diff = (datetime.now() - last_hb).total_seconds()
            m.is_online = diff < 300 # 5 minutes
        else:
            m.is_online = False

    return render_template('facility_ops.html',
                           metrics=metrics,
                           alerts=alerts,
                           schedules=schedules,
                           franchise_name=current_user.franchise_id or "Global Admin")

@app.route('/manager/dashboard')
@login_required
@role_required(['Admin', 'Franchisee'])
def manager_dashboard():
    """Manager-specific intelligence dashboard (v3.9.0)"""
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')

    # 1. Equipment Stability & Health
    if is_admin:
        units = EquipmentMetric.query.all()
    else:
        units = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()

    # 2. Staff Schedule & Reservations
    if is_admin:
        schedules = MemberSchedule.query.order_by(MemberSchedule.start_time.asc()).limit(20).all()
    else:
        metric_ids = [u.id for u in units]
        schedules = MemberSchedule.query.filter(MemberSchedule.equipment_id.in_(metric_ids)).order_by(MemberSchedule.start_time.asc()).all()

    # 3. Live Activity Feed (Recent Scans)
    if is_admin:
        activity = db.session.query(TelemetryHistory, Member.name)\
            .outerjoin(Member, TelemetryHistory.member_id == Member.id)\
            .order_by(TelemetryHistory.timestamp.desc()).limit(10).all()
    else:
        metric_ids = [u.id for u in units]
        activity = db.session.query(TelemetryHistory, Member.name)\
            .outerjoin(Member, TelemetryHistory.member_id == Member.id)\
            .filter(TelemetryHistory.equipment_id.in_(metric_ids))\
            .order_by(TelemetryHistory.timestamp.desc()).limit(10).all()

    # 4. Automation Efficiency
    automation_status = AutomationHeartbeat.query.all()

    # 5. Critical Alerts
    if is_admin:
        alerts = Alert.query.filter_by(is_resolved=False).order_by(Alert.timestamp.desc()).limit(5).all()
    else:
        metric_ids = [u.id for u in units]
        alerts = Alert.query.filter(Alert.equipment_id.in_(metric_ids), Alert.is_resolved == False).order_by(Alert.timestamp.desc()).all()

    # 6. Revenue & Payments (v3.9.2)
    if is_admin:
        recent_payments = Payment.query.order_by(Payment.timestamp.desc()).limit(10).all()
    else:
        # Get all members in this franchise
        m_ids = [m.id for m in Member.query.filter_by(franchise_id=franchise_id).all()]
        recent_payments = Payment.query.filter(Payment.member_id.in_(m_ids)).order_by(Payment.timestamp.desc()).all()

    # 7. Security & Access Audit
    if is_admin:
        security_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(5).all()
    else:
        security_logs = AuditLog.query.filter_by(user_id=current_user.id).order_by(AuditLog.timestamp.desc()).limit(5).all()

    franchise_name = Lead.query.get(franchise_id).company if franchise_id else "Global Fleet"

    return render_template('manager_dashboard.html',
                           units=units,
                           schedules=schedules,
                           activity=activity,
                           automation_status=automation_status,
                           alerts=alerts,
                           security_logs=security_logs,
                           recent_payments=recent_payments,
                           franchise_name=franchise_name)

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

    # Get available equipment for the member's franchise
    equipment = EquipmentMetric.query.filter_by(franchise_id=member.franchise_id).all()

    # Get member's upcoming sessions
    upcoming_sessions = db.session.query(
        MemberSchedule.start_time,
        MemberSchedule.duration_minutes,
        MemberSchedule.status,
        EquipmentMetric.equipment_name
    ).join(EquipmentMetric, MemberSchedule.equipment_id == EquipmentMetric.id)\
     .filter(MemberSchedule.member_id == member.id)\
     .order_by(MemberSchedule.start_time.asc()).all()

    # Get engagement chart data
    history = TelemetryHistory.query.filter_by(member_id=member.id).order_by(TelemetryHistory.timestamp.asc()).all()
    daily_stats = {}
    for entry in history:
        date = entry.timestamp[:10]
        daily_stats[date] = daily_stats.get(date, 0) + entry.scans_count

    sorted_dates = sorted(daily_stats.keys())
    chart_labels = sorted_dates[-7:] # Last 7 days
    chart_data = [daily_stats[d] for d in chart_labels]

    # Payments (v3.9.2)
    payments = Payment.query.filter_by(member_id=member.id).order_by(Payment.timestamp.desc()).all()

    return render_template('member_dashboard.html',
                           member=member,
                           equipment=equipment,
                           upcoming_sessions=upcoming_sessions,
                           chart_labels=chart_labels,
                           chart_data=chart_data,
                           payments=payments)

@app.route('/member/submit-feedback', methods=['POST'])
@login_required
def member_submit_feedback():
    """Handles pilot feedback submissions (v3.9.1)"""
    if current_user.role != 'Member':
        abort(403)

    member = Member.query.filter_by(user_id=current_user.id).first()
    rating = request.form.get('rating')
    category = request.form.get('category')
    comment = request.form.get('comment')

    if not rating:
        flash("Please provide a rating.")
        return redirect(url_for('member_dashboard'))

    feedback = Feedback(
        member_id=member.id if member else None,
        franchise_id=member.franchise_id if member else None,
        rating=int(rating),
        category=category,
        comment=comment,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.session.add(feedback)
    db.session.commit()

    flash("Thank you for your feedback! It helps us improve the StepManiaX experience.")
    return redirect(url_for('member_dashboard'))

@app.route('/member/book', methods=['POST'])
@login_required
def member_book_session():
    if current_user.role != 'Member':
        abort(403)

    member = Member.query.filter_by(user_id=current_user.id).first()
    equipment_id = request.form.get('equipment_id')
    start_time = request.form.get('start_time')

    if not start_time:
        flash("Please select a valid date and time.")
        return redirect(url_for('member_dashboard'))

    # Format datetime for storage
    try:
        dt = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
        formatted_start = dt.strftime('%Y-%m-%d %H:%M')
    except ValueError:
        flash("Invalid date format.")
        return redirect(url_for('member_dashboard'))

    new_booking = MemberSchedule(
        member_id=member.id,
        member_name=member.name,
        equipment_id=equipment_id,
        start_time=formatted_start,
        duration_minutes=15, # Default pilot session
        status='Scheduled'
    )
    db.session.add(new_booking)
    db.session.commit()

    flash(f"Session booked for {formatted_start}!")
    return redirect(url_for('member_dashboard'))

@app.route('/api/v1/payments', methods=['POST'])
@csrf.exempt
@require_api_key
def api_process_payment():
    """Processes membership payments via configured gateway (v3.9.2)"""
    data = request.get_json()
    if not data or 'member_id' not in data or 'amount' not in data:
        return {"error": "Invalid payment data"}, 400

    member = Member.query.get(data['member_id'])
    if not member:
        return {"error": "Member not found"}, 404

    # Utilize Gateway Adapter
    gateway = get_payment_gateway(provider_type=os.environ.get('PAYMENT_PROVIDER', 'mock'))
    result = gateway.process_charge(
        amount=float(data['amount']),
        currency=data.get('currency', 'USD'),
        description=f"Membership Fee - Member {member.id}"
    )

    if result['status'] == 'success':
        payment = Payment(
            member_id=member.id,
            amount=result['amount'],
            currency=result['currency'],
            status='Completed',
            transaction_id=result['transaction_id'],
            timestamp=result['timestamp']
        )
        db.session.add(payment)
        db.session.commit()

        log_security_event(None, f"Payment Processed: {result['transaction_id']} for Member {member.id}")
        return {"status": "success", "transaction_id": result['transaction_id']}, 201
    else:
        return {"error": "Payment failed", "details": result.get('error')}, 400

@app.route('/api/v1/telemetry', methods=['POST'])
@csrf.exempt # Exempting for machine-to-machine API calls
@require_api_key
def telemetry():
    """
    Endpoint for StepManiaX units to POST telemetry data.
    Expected JSON: { "equipment_id": int, "uptime_percent": float, "scans_increment": int, "session_duration": float, "member_id": int }
    """
    data = request.get_json()
    if not data or 'equipment_id' not in data:
        return {"error": "Invalid telemetry packet"}, 400

    unit = EquipmentMetric.query.get(data['equipment_id'])
    if not unit:
        return {"error": "Unit not found"}, 404

    # Update heartbeat
    unit.last_heartbeat = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    member_id = data.get('member_id')
    member = None
    if member_id:
        member = Member.query.get(member_id)

    # Update Metrics
    if 'uptime_percent' in data:
        unit.uptime_percent = data['uptime_percent']

    if 'scans_increment' in data:
        unit.total_scans += data['scans_increment']
        # Log to history
        history = TelemetryHistory(
            equipment_id=unit.id,
            member_id=member_id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            scans_count=data['scans_increment']
        )
        db.session.add(history)

        # Update member points and engagement
        if member:
            member.points += data['scans_increment']
            # Simple engagement score: points / days since registration
            reg_date = datetime.strptime(member.registration_date, "%Y-%m-%d")
            days_active = (datetime.now() - reg_date).days + 1
            member.engagement_score = min(1.0, member.points / (days_active * 100)) # Target 100 scans/day

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
@role_required(['Admin', 'Franchisee', 'Staff'])
def settings():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'change_password':
            current_pw = request.form.get('current_password')
            new_pw = request.form.get('new_password')
            confirm_pw = request.form.get('confirm_password')

            if not current_user.check_password(current_pw):
                flash("Current password incorrect.")
            elif new_pw != confirm_pw:
                flash("New passwords do not match.")
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                log_security_event(current_user.id, "Password changed successfully")
                flash("Password updated successfully!")
            return redirect(url_for('settings'))

        if action == 'add_webhook':
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

        elif action == 'create_user' and current_user.role == 'Admin':
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')
            franchise_id = request.form.get('franchise_id')

            if User.query.filter_by(username=username).first():
                flash("User already exists.")
            else:
                new_user = User(username=username, role=role, franchise_id=franchise_id if franchise_id else None)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                flash(f"User {username} created successfully as {role}.")

        return redirect(url_for('settings'))

    # Filtering for audit logs (v3.9.0)
    search_query = request.args.get('q', '')

    if current_user.role == 'Admin':
        webhooks = Webhook.query.all()
        users = User.query.all()
        audit_base = AuditLog.query
        if search_query:
            audit_base = audit_base.filter(AuditLog.action.contains(search_query))
        audit_logs = audit_base.order_by(AuditLog.timestamp.desc()).limit(50).all()
    else:
        webhooks = Webhook.query.filter_by(franchise_id=current_user.franchise_id).all()
        users = []
        audit_logs = AuditLog.query.filter_by(user_id=current_user.id).order_by(AuditLog.timestamp.desc()).limit(10).all()

    return render_template('settings.html', webhooks=webhooks, users=users, audit_logs=audit_logs)

@app.route('/api/v1/analytics/hourly', methods=['GET'])
@csrf.exempt
@require_api_key
def api_hourly_analytics():
    """
    Returns scan distribution by hour of day (0-23).
    """
    if current_user.is_authenticated:
        franchise_id = current_user.franchise_id
        is_admin = (current_user.role == 'Admin')
    else:
        franchise_id = request.args.get('franchise_id')
        is_admin = not franchise_id

    if is_admin:
        metrics = EquipmentMetric.query.all()
    else:
        metrics = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()

    metric_ids = [m.id for m in metrics]
    history = TelemetryHistory.query.filter(TelemetryHistory.equipment_id.in_(metric_ids)).all()

    hourly_distribution = {i: 0 for i in range(24)}
    for entry in history:
        # Expected format: "YYYY-MM-DD HH:MM:S"
        try:
            hour = int(entry.timestamp[11:13])
            hourly_distribution[hour] += entry.scans_count
        except (ValueError, IndexError):
            continue

    return {
        "labels": [f"{h:02d}:00" for h in range(24)],
        "data": [hourly_distribution[h] for h in range(24)]
    }, 200

@app.route('/api/v1/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@login_required
@role_required(['Admin', 'Staff'])
def api_acknowledge_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    alert.acknowledged_by = current_user.username
    db.session.commit()
    return {"status": "acknowledged", "user": current_user.username}, 200

@app.route('/api/v1/alerts/<int:alert_id>/resolve', methods=['POST'])
@login_required
@role_required(['Admin', 'Staff'])
def api_resolve_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    alert.is_resolved = True
    alert.resolved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alert.resolved_by = current_user.username

    # Also update equipment status if all alerts for it are resolved
    unit = EquipmentMetric.query.get(alert.equipment_id)
    if unit:
        remaining = Alert.query.filter_by(equipment_id=unit.id, is_resolved=False).count()
        if remaining <= 1: # This one is about to be resolved
            unit.maintenance_status = 'Operational'

    db.session.commit()
    return {"status": "resolved", "user": current_user.username}, 200

@app.route('/api/v1/analytics/usage', methods=['GET'])
@csrf.exempt
@require_api_key
def api_usage_analytics():
    # If authenticated via session (e.g. from dashboard), use session context
    # Otherwise, require franchise_id as a parameter if not global
    if current_user.is_authenticated:
        franchise_id = current_user.franchise_id
        is_admin = (current_user.role == 'Admin')
    else:
        franchise_id = request.args.get('franchise_id')
        is_admin = not franchise_id

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
    # If authenticated via API Key, we assume Global Admin scope for now as the key is in config.py
    # If authenticated via Session, we check roles.
    is_admin = not current_user.is_authenticated or current_user.role == 'Admin'

    if is_admin:
        franchise_id = request.args.get('franchise_id')
        if not franchise_id:
            members = Member.query.all()
        else:
            members = Member.query.filter_by(franchise_id=franchise_id).all()
    else:
        # Force filter by current user's franchise if not admin
        members = Member.query.filter_by(franchise_id=current_user.franchise_id).all()

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
        franchise_id=data.get('franchise_id', getattr(current_user, 'franchise_id', None))
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

    # Multi-tenant isolation for session-based users
    if current_user.is_authenticated:
        if current_user.role != 'Admin' and member.franchise_id != current_user.franchise_id:
            log_security_event(current_user.id, f"Unauthorized member access attempt: Member {member_id}")
            abort(403)

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

@app.route('/prospect/<token>')
def prospect_portal(token):
    """
    Public but secure landing page for prospective franchise partners.
    """
    lead = Lead.query.filter_by(public_token=token).first_or_404()

    # Increment view counter
    if lead.portal_views is None: lead.portal_views = 0
    lead.portal_views += 1
    db.session.commit()

    # Log engagement
    log_security_event(None, f"Prospect Portal Viewed: {lead.company} (Token: {token})")

    # Calculate personalized metrics
    metrics = analytics.calculate_detailed_metrics(
        num_clubs=lead.num_clubs,
        retention_lift_percent=lead.retention_lift,
        avg_monthly_fee=lead.avg_monthly_fee
    )

    return render_template('prospect_portal.html', lead=lead, metrics=metrics)

@app.route('/admin/feedback')
@login_required
@role_required(['Admin'])
def admin_feedback():
    """Feedback Analytics Dashboard (v3.9.1)"""
    feedback_raw = db.session.query(Feedback, Member.name, Lead.company)\
        .outerjoin(Member, Feedback.member_id == Member.id)\
        .outerjoin(Lead, Feedback.franchise_id == Lead.id)\
        .order_by(Feedback.timestamp.desc()).all()

    feedback_list = []
    for f, m_name, company in feedback_raw:
        feedback_list.append({
            "timestamp": f.timestamp,
            "member_name": m_name or "Anonymous",
            "company": company or "Global",
            "category": f.category,
            "rating": f.rating,
            "comment": f.comment
        })

    avg_rating = db.session.query(db.func.avg(Feedback.rating)).scalar() or 0

    # Category distribution
    cat_counts = db.session.query(Feedback.category, db.func.count(Feedback.id))\
        .group_by(Feedback.category).all()
    categories = [c[0] for c in cat_counts]
    category_counts = [c[1] for c in cat_counts]

    # Simple rating trend (by day)
    trend_raw = db.session.query(db.func.substr(Feedback.timestamp, 1, 10), db.func.avg(Feedback.rating))\
        .group_by(db.func.substr(Feedback.timestamp, 1, 10))\
        .order_by(db.func.substr(Feedback.timestamp, 1, 10)).all()
    trend_labels = [t[0] for t in trend_raw]
    trend_data = [round(t[1], 1) for t in trend_raw]

    return render_template('admin_feedback.html',
                           feedback_list=feedback_list,
                           avg_rating=avg_rating,
                           categories=categories,
                           category_counts=category_counts,
                           trend_labels=trend_labels,
                           trend_data=trend_data)

@app.route('/admin/optimization')
@login_required
@role_required(['Admin'])
def admin_optimization():
    # Optimization & Performance Metrics
    total_members = Member.query.count()
    onboarding_funnel = db.session.query(Member.onboarding_status, db.func.count(Member.id)).group_by(Member.onboarding_status).all()
    onboarding_dict = {status: count for status, count in onboarding_funnel}

    # Avg Engagement Score across fleet
    avg_engagement = db.session.query(db.func.avg(Member.engagement_score)).scalar() or 0

    # Optimization recommendations
    units = EquipmentMetric.query.all()
    # Convert SQLAlchemy objects to dicts for the analytics function
    metrics_list = [
        {
            "equipment_name": u.equipment_name,
            "location": u.location,
            "uptime_percent": u.uptime_percent,
            "total_sessions": u.total_sessions,
            "avg_session_duration": u.avg_session_duration
        } for u in units
    ]
    recommendations = analytics.generate_optimization_recommendations(metrics_list)

    return render_template('admin_optimization.html',
                           total_members=total_members,
                           onboarding_stats=onboarding_dict,
                           avg_engagement=round(avg_engagement * 100, 1),
                           recommendations=recommendations,
                           units=units)

@app.route('/admin/api/logs')
@login_required
@role_required(['Admin'])
def admin_api_logs():
    """Serves the latest system logs for real-time streaming (v3.9.0)"""
    log_files = ['campaign_launch.log', 'server.log']
    logs = []
    for log_file in log_files:
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                # Get last 5 lines from each
                lines = f.readlines()[-5:]
                logs.extend([f"[{log_file}] {line.strip()}" for line in lines])

    return "<br>".join(logs) if logs else "Waiting for system logs..."

@app.route('/admin/launch-campaign', methods=['POST'])
@login_required
@role_required(['Admin'])
def admin_launch_campaign():
    """Triggers the autonomous sales pipeline (v3.9.0)"""
    try:
        # Run launch_campaign.sh in the background
        subprocess.Popen(["bash", "launch_campaign.sh"],
                         stdout=open("campaign_launch.log", "a"),
                         stderr=subprocess.STDOUT)

        # Log the event
        audit = AuditLog(
            user_id=current_user.id,
            action="Campaign Launch Triggered: Autonomous sales pipeline (launch_campaign.sh) initiated via Command Center.",
            ip_address=request.remote_addr,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.session.add(audit)
        db.session.commit()

        flash("Autonomous Campaign Launch Sequence Initiated! Monitor logs for progress.", "success")
    except Exception as e:
        flash(f"Error launching campaign: {str(e)}", "danger")

    return redirect(url_for('admin_command_center'))

@app.route('/admin/command-center')
@login_required
@role_required(['Admin'])
def admin_command_center():
    # Automation Status (v3.9.0)
    automation_status = AutomationHeartbeat.query.all()

    # Global Fleet Stats
    total_units = EquipmentMetric.query.count()
    active_alerts = Alert.query.filter_by(is_resolved=False).count()
    total_scans = db.session.query(db.func.sum(EquipmentMetric.total_scans)).scalar() or 0
    avg_uptime = db.session.query(db.func.avg(EquipmentMetric.uptime_percent)).scalar() or 0

    # Active Sessions (Mocking for now as we don't have a 'session' table yet,
    # but we can count unique member_ids in TelemetryHistory from last hour)
    one_hour_ago = datetime.now().timestamp() - 3600
    # Actually our timestamp is a string, so we'd need to convert.
    # For now let's just count distinct member_ids from the last 10 telemetry entries as 'live'
    live_sessions = db.session.query(TelemetryHistory.member_id).distinct().limit(10).count()

    metrics = EquipmentMetric.query.all()
    alerts = Alert.query.filter_by(is_resolved=False).order_by(Alert.timestamp.desc()).all()

    return render_template('admin_command_center.html',
                           total_units=total_units,
                           active_alerts=active_alerts,
                           total_scans=total_scans,
                           avg_uptime=round(avg_uptime, 1),
                           live_sessions=live_sessions,
                           metrics=metrics,
                           alerts=alerts,
                           automation_status=automation_status)

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

    # 5. Lead List with Propensity Scores
    if is_admin:
        leads_list = Lead.query.all()
    else:
        leads_list = Lead.query.filter_by(id=franchise_id).all()

    # Dynamic scoring and token generation
    updated = False
    for lead in leads_list:
        if not lead.public_token:
            lead.public_token = secrets.token_urlsafe(16)
            updated = True

        # Calculate real-time pilot engagement
        member_count = Member.query.filter_by(franchise_id=lead.id).count()
        total_points = db.session.query(db.func.sum(Member.points)).filter_by(franchise_id=lead.id).scalar() or 0
        avg_feedback = db.session.query(db.func.avg(Feedback.rating)).filter_by(franchise_id=lead.id).scalar() or 5.0

        lead_dict = {
            'num_clubs': lead.num_clubs,
            'region': lead.region,
            'status': lead.status,
            'priority': lead.priority,
            'pilot_engagement': {
                'member_count': member_count,
                'total_points': total_points
            },
            'portal_views': lead.portal_views,
            'avg_feedback_rating': avg_feedback
        }
        lead.propensity_score = analytics.calculate_propensity_score(lead_dict)

    if updated:
        db.session.commit()

    # Sort by propensity score descending for Admin
    if is_admin:
        leads_list.sort(key=lambda x: x.propensity_score, reverse=True)

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
    # Default to production-safe settings; use environment for debug
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, port=5000)
