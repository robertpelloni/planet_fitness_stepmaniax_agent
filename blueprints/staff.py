from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from models import db, EquipmentMetric, Alert, MemberSchedule, Member, TelemetryHistory
from datetime import datetime
import analytics
from blueprints.decorators import role_required

staff_bp = Blueprint('staff', __name__)

@staff_bp.route('/staff/api/metrics')
@login_required
@role_required(['Admin', 'Staff'])
def staff_api_metrics():
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')
    if is_admin:
        metrics = EquipmentMetric.query.all()
    else:
        metrics = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()

    for m in metrics:
        if m.last_heartbeat:
            last_hb = datetime.strptime(m.last_heartbeat, "%Y-%m-%d %H:%M:%S")
            diff = (datetime.now() - last_hb).total_seconds()
            m.is_online = diff < 300
        else:
            m.is_online = False
        # Calculate Utilization (v4.5.0)
        m.utilization_score = analytics.calculate_capacity_utilization(m.total_sessions, m.uptime_percent)

    if request.args.get('view') == 'ops':
        return render_template('partials/facility_metrics.html', metrics=metrics)
    return render_template('partials/staff_metrics.html', metrics=metrics)

@staff_bp.route('/staff/api/maintenance')
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

@staff_bp.route('/staff/api/alerts')
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

@staff_bp.route('/staff/members')
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

@staff_bp.route('/staff/members/update/<int:member_id>', methods=['POST'])
@login_required
@role_required(['Admin', 'Staff'])
def staff_update_member_status(member_id):
    member = Member.query.get_or_404(member_id)
    new_status = request.form.get('status')

    if current_user.role != 'Admin' and member.franchise_id != current_user.franchise_id:
        abort(403)

    member.onboarding_status = new_status
    db.session.commit()
    flash(f"Status updated for member {member.name}")
    return redirect(url_for('staff.staff_members'))

@staff_bp.route('/staff/schedules/create', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Staff'])
def create_schedule():
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')

    if request.method == 'POST':
        new_schedule = MemberSchedule(
            member_name=request.form.get('member_name'),
            start_time=request.form.get('start_time').replace('T', ' '),
            duration_minutes=int(request.form.get('duration_minutes', 15)),
            equipment_id=int(request.form.get('equipment_id')),
            status=request.form.get('status', 'Scheduled')
        )
        db.session.add(new_schedule)
        db.session.commit()
        flash("New session scheduled successfully.")
        return redirect(url_for('staff.staff_dashboard'))

    if is_admin:
        units = EquipmentMetric.query.all()
    else:
        units = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()

    return render_template('staff_edit_schedule.html', units=units, schedule=None)

@staff_bp.route('/staff/schedules/edit/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Staff'])
def edit_schedule(schedule_id):
    schedule = MemberSchedule.query.get_or_404(schedule_id)
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')

    if request.method == 'POST':
        schedule.member_name = request.form.get('member_name')
        schedule.start_time = request.form.get('start_time').replace('T', ' ')
        schedule.duration_minutes = int(request.form.get('duration_minutes'))
        schedule.equipment_id = int(request.form.get('equipment_id'))
        schedule.status = request.form.get('status')
        db.session.commit()
        flash("Schedule updated successfully.")
        return redirect(url_for('staff.staff_dashboard'))

    if is_admin:
        units = EquipmentMetric.query.all()
    else:
        units = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()

    # Format for datetime-local input
    if ' ' in schedule.start_time:
        schedule.start_time = schedule.start_time.replace(' ', 'T')

    return render_template('staff_edit_schedule.html', units=units, schedule=schedule)

@staff_bp.route('/staff/operations')
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

    for m in metrics:
        if m.last_heartbeat:
            last_hb = datetime.strptime(m.last_heartbeat, "%Y-%m-%d %H:%M:%S")
            diff = (datetime.now() - last_hb).total_seconds()
            m.is_online = diff < 300
        else:
            m.is_online = False

    from models import Lead
    franchise_name = "Global Admin"
    if franchise_id:
        lead = Lead.query.get(franchise_id)
        if lead:
            franchise_name = lead.company

    return render_template('facility_ops.html',
                           metrics=metrics,
                           alerts=alerts,
                           schedules=schedules,
                           franchise_name=franchise_name)

@staff_bp.route('/staff/dashboard')
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

    for m in metrics:
        m.utilization_score = analytics.calculate_capacity_utilization(m.total_sessions, m.uptime_percent)

    from models import Lead
    franchise_name = "Global Admin"
    if franchise_id:
        lead = Lead.query.get(franchise_id)
        if lead:
            franchise_name = lead.company

    return render_template('staff_dashboard.html',
                           metrics=metrics,
                           alerts=alerts,
                           schedules=schedules,
                           franchise_name=franchise_name)

@staff_bp.route('/manager/api/activity')
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

@staff_bp.route('/manager/dashboard')
@login_required
@role_required(['Admin', 'Franchisee'])
def manager_dashboard():
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')

    if is_admin:
        units = EquipmentMetric.query.all()
        schedules = MemberSchedule.query.order_by(MemberSchedule.start_time.asc()).limit(20).all()
        activity = db.session.query(TelemetryHistory, Member.name)\
            .outerjoin(Member, TelemetryHistory.member_id == Member.id)\
            .order_by(TelemetryHistory.timestamp.desc()).limit(10).all()
        alerts = Alert.query.filter_by(is_resolved=False).order_by(Alert.timestamp.desc()).limit(5).all()
        from models import AuditLog
        security_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(5).all()
        from models import Payment
        recent_payments = Payment.query.order_by(Payment.timestamp.desc()).limit(10).all()
    else:
        units = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()
        metric_ids = [u.id for u in units]
        schedules = MemberSchedule.query.filter(MemberSchedule.equipment_id.in_(metric_ids)).order_by(MemberSchedule.start_time.asc()).all()
        activity = db.session.query(TelemetryHistory, Member.name)\
            .outerjoin(Member, TelemetryHistory.member_id == Member.id)\
            .filter(TelemetryHistory.equipment_id.in_(metric_ids))\
            .order_by(TelemetryHistory.timestamp.desc()).limit(10).all()
        alerts = Alert.query.filter(Alert.equipment_id.in_(metric_ids), Alert.is_resolved == False).order_by(Alert.timestamp.desc()).all()
        from models import AuditLog
        security_logs = AuditLog.query.filter_by(user_id=current_user.id).order_by(AuditLog.timestamp.desc()).limit(5).all()
        from models import Payment
        m_ids = [m.id for m in Member.query.filter_by(franchise_id=franchise_id).all()]
        recent_payments = Payment.query.filter(Payment.member_id.in_(m_ids)).order_by(Payment.timestamp.desc()).all()

    from models import AutomationHeartbeat
    automation_status = AutomationHeartbeat.query.all()

    from models import Lead
    franchise_name = "Global Fleet"
    if franchise_id:
        lead = Lead.query.get(franchise_id)
        if lead:
            franchise_name = lead.company

    return render_template('manager_dashboard.html',
                           units=units,
                           schedules=schedules,
                           activity=activity,
                           automation_status=automation_status,
                           alerts=alerts,
                           security_logs=security_logs,
                           recent_payments=recent_payments,
                           franchise_name=franchise_name)
