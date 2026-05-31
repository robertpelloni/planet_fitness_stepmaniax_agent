from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from models import db, User, EquipmentMetric, Alert, Member, TelemetryHistory, AutomationHeartbeat, Payment, Lead, MemberSchedule
from blueprints.decorators import role_required
from datetime import datetime
import analytics

staff_bp = Blueprint('staff', __name__)

@staff_bp.route('/dashboard')
@login_required
@role_required(['Admin', 'Staff'])
def staff_dashboard():
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')
    region = request.args.get('region')

    if is_admin:
        query_metrics = EquipmentMetric.query
        if region:
            query_metrics = query_metrics.filter_by(region_cluster=region)
        metrics = query_metrics.all()
        metric_ids = [m.id for m in metrics]

        if region:
            alerts = Alert.query.filter(Alert.equipment_id.in_(metric_ids), Alert.is_resolved == False).order_by(Alert.timestamp.desc()).limit(10).all()
            schedules = MemberSchedule.query.filter(MemberSchedule.equipment_id.in_(metric_ids)).order_by(MemberSchedule.start_time.asc()).all()
        else:
            alerts = Alert.query.filter_by(is_resolved=False).order_by(Alert.timestamp.desc()).limit(10).all()
            schedules = MemberSchedule.query.order_by(MemberSchedule.start_time.asc()).all()
    else:
        metrics = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()
        metric_ids = [m.id for m in metrics]
        alerts = Alert.query.filter(Alert.equipment_id.in_(metric_ids), Alert.is_resolved == False).order_by(Alert.timestamp.desc()).limit(10).all()
        schedules = MemberSchedule.query.filter(MemberSchedule.equipment_id.in_(metric_ids)).order_by(MemberSchedule.start_time.asc()).all()

    for m in metrics:
        m.utilization_score = analytics.calculate_capacity_utilization(m.total_sessions, m.uptime_percent) if hasattr(analytics, 'calculate_capacity_utilization') else 0

    all_regions = [r[0] for r in db.session.query(Lead.region_cluster).distinct().all() if r[0]] if is_admin else []

    return render_template('staff_dashboard.html',
                           metrics=metrics,
                           alerts=alerts,
                           schedules=schedules,
                           franchise_name=current_user.franchise_id or "Global Admin",
                           all_regions=all_regions,
                           current_region=region)

@staff_bp.route('/operations')
@login_required
@role_required(['Admin', 'Staff'])
def facility_operations():
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')
    region = request.args.get('region')

    if is_admin:
        query_metrics = EquipmentMetric.query
        if region:
            query_metrics = query_metrics.filter_by(region_cluster=region)
        metrics = query_metrics.all()
        metric_ids = [m.id for m in metrics]

        today = datetime.now().strftime("%Y-%m-%d")
        if region:
            alerts = Alert.query.filter(Alert.equipment_id.in_(metric_ids), Alert.is_resolved == False).order_by(Alert.timestamp.desc()).limit(20).all()
            schedules = MemberSchedule.query.filter(MemberSchedule.equipment_id.in_(metric_ids), MemberSchedule.start_time.contains(today)).order_by(MemberSchedule.start_time.asc()).all()
        else:
            alerts = Alert.query.filter_by(is_resolved=False).order_by(Alert.timestamp.desc()).limit(20).all()
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

    all_regions = [r[0] for r in db.session.query(Lead.region_cluster).distinct().all() if r[0]] if is_admin else []

    return render_template('facility_ops.html',
                           metrics=metrics,
                           alerts=alerts,
                           schedules=schedules,
                           franchise_name=current_user.franchise_id or "Global Admin",
                           all_regions=all_regions,
                           current_region=region)

@staff_bp.route('/members')
@login_required
@role_required(['Admin', 'Staff'])
def staff_members():
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')
    region = request.args.get('region')

    if is_admin:
        query = Member.query
        if region:
            query = query.filter(Member.franchise_id.in_(
                db.session.query(Lead.id).filter_by(region_cluster=region)
            ))
        members = query.all()
    else:
        members = Member.query.filter_by(franchise_id=franchise_id).all()

    all_regions = [r[0] for r in db.session.query(Lead.region_cluster).distinct().all() if r[0]] if is_admin else []

    return render_template('staff_members.html', members=members, all_regions=all_regions, current_region=region)

@staff_bp.route('/members/update/<int:member_id>', methods=['POST'])
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

@staff_bp.route('/members/assign-plan/<int:member_id>', methods=['POST'])
@login_required
@role_required(['Admin', 'Staff'])
def staff_assign_plan(member_id):
    member = Member.query.get_or_404(member_id)
    if current_user.role != 'Admin' and member.franchise_id != current_user.franchise_id:
        abort(403)

    from models import WorkoutPlan
    plan_name = request.form.get('name')
    target_scans = int(request.form.get('target_scans'))
    target_duration = int(request.form.get('target_duration'))

    # If member already has a plan, update it, otherwise create new
    if member.workout_plan:
        member.workout_plan.name = plan_name
        member.workout_plan.target_scans = target_scans
        member.workout_plan.target_duration = target_duration
    else:
        new_plan = WorkoutPlan(
            member_id=member.id,
            name=plan_name,
            target_scans=target_scans,
            target_duration=target_duration
        )
        db.session.add(new_plan)

    db.session.commit()
    flash(f"Workout plan assigned to {member.name}")
    return redirect(url_for('staff.staff_members'))

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
        m_ids = [m.id for m in Member.query.filter_by(franchise_id=franchise_id).all()]
        recent_payments = Payment.query.filter(Payment.member_id.in_(m_ids)).order_by(Payment.timestamp.desc()).all()

    automation_status = AutomationHeartbeat.query.all()
    franchise_name = Lead.query.get(franchise_id).company if franchise_id else "Global fleet"

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
@role_required(['Admin', 'Staff', 'Franchisee'])
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

@staff_bp.route('/live-ops')
@login_required
@role_required(['Admin', 'Staff', 'Franchisee'])
def live_ops_wallboard():
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')
    region = request.args.get('region')

    if is_admin:
        query = EquipmentMetric.query
        if region:
            query = query.filter_by(region_cluster=region)
        units = query.all()
        all_regions = [r[0] for r in db.session.query(Lead.region_cluster).distinct().all() if r[0]]
    else:
        units = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()
        all_regions = []

    franchise_name = Lead.query.get(franchise_id).company if franchise_id else "Global Fleet"
    if region:
        franchise_name += f" - {region}"

    return render_template('live_ops_wallboard.html',
                           units=units,
                           franchise_name=franchise_name,
                           all_regions=all_regions,
                           current_region=region)

@staff_bp.route('/schedule/create', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Staff'])
def create_schedule():
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        member_name = request.form.get('member_name')
        start_time = request.form.get('start_time')
        duration = int(request.form.get('duration', 10))
        unit_id = request.form.get('equipment_id')

        new_booking = MemberSchedule(
            member_id=member_id if member_id else None,
            member_name=member_name,
            start_time=start_time,
            duration_minutes=duration,
            equipment_id=unit_id,
            status='Scheduled'
        )
        db.session.add(new_booking)
        db.session.commit()
        flash("New session scheduled successfully.")
        return redirect(url_for('staff.staff_dashboard'))

    members = Member.query.all() if current_user.role == 'Admin' else Member.query.filter_by(franchise_id=current_user.franchise_id).all()
    units = EquipmentMetric.query.all() if current_user.role == 'Admin' else EquipmentMetric.query.filter_by(franchise_id=current_user.franchise_id).all()
    return render_template('staff_edit_schedule.html', action="Create", members=members, units=units)

@staff_bp.route('/schedule/edit/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Staff'])
def edit_schedule(schedule_id):
    booking = MemberSchedule.query.get_or_404(schedule_id)
    if request.method == 'POST':
        booking.member_name = request.form.get('member_name')
        booking.start_time = request.form.get('start_time')
        booking.duration_minutes = int(request.form.get('duration', 10))
        booking.equipment_id = request.form.get('equipment_id')
        booking.status = request.form.get('status')
        db.session.commit()
        flash("Schedule updated.")
        return redirect(url_for('staff.staff_dashboard'))

    members = Member.query.all() if current_user.role == 'Admin' else Member.query.filter_by(franchise_id=current_user.franchise_id).all()
    units = EquipmentMetric.query.all() if current_user.role == 'Admin' else EquipmentMetric.query.filter_by(franchise_id=current_user.franchise_id).all()
    return render_template('staff_edit_schedule.html', action="Edit", booking=booking, members=members, units=units)
