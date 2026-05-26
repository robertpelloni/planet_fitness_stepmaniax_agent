from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from models import db, User, EquipmentMetric, Alert, MemberSchedule, Member, TelemetryHistory, AutomationHeartbeat, Payment, Lead
from blueprints.decorators import role_required
from datetime import datetime

staff_bp = Blueprint('staff', __name__)

@staff_bp.route('/dashboard')
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

@staff_bp.route('/operations')
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

@staff_bp.route('/members')
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

@staff_bp.route('/members/update/<int:member_id>', methods=['POST'])
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
    return redirect(url_for('staff.staff_members'))

@staff_bp.route('/manager/dashboard')
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
    from models import AuditLog
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

@staff_bp.route('/api/metrics')
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

@staff_bp.route('/api/maintenance')
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

@staff_bp.route('/api/activity')
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

@staff_bp.route('/api/alerts')
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
