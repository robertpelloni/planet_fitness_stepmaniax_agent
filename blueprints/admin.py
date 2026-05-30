from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, send_from_directory
from flask_login import login_required, current_user
from models import db, User, EquipmentMetric, Alert, Lead, AuditLog, AutomationHeartbeat, Feedback, Member, Payment, TelemetryHistory, MemberSchedule
from datetime import datetime
import subprocess
import analytics
import os
import secrets
from blueprints.decorators import role_required, permission_required
from report_generator import generate_report

admin_bp = Blueprint('admin', __name__)

def log_security_event(user_id, action):
    log = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=request.remote_addr,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.session.add(log)
    db.session.commit()

@admin_bp.route('/dashboard')
@login_required
@role_required(['Admin', 'Franchisee'])
def dashboard():
    # Multi-tenant logic: Filter by franchise_id if user is not an Admin
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')

    if is_admin:
        crm_stats = db.session.query(Lead.status, db.func.count(Lead.id).label('count')).group_by(Lead.status).all()
        metrics = EquipmentMetric.query.all()
        onboarding_stats = db.session.query(Member.onboarding_status, db.func.count(Member.id)).group_by(Member.onboarding_status).all()
        leads_list = Lead.query.all()
    else:
        crm_stats = db.session.query(Lead.status, db.func.count(Lead.id).label('count')).filter_by(id=franchise_id).group_by(Lead.status).all()
        metrics = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()
        onboarding_stats = db.session.query(Member.onboarding_status, db.func.count(Member.id)).filter_by(franchise_id=franchise_id).group_by(Member.onboarding_status).all()
        leads_list = Lead.query.filter_by(id=franchise_id).all()

    metric_ids = [m.id for m in metrics]

    if is_admin:
        alerts = Alert.query.filter_by(is_resolved=False).order_by(Alert.timestamp.desc()).all()
        schedules = MemberSchedule.query.order_by(MemberSchedule.start_time.asc()).all()
    else:
        alerts = Alert.query.filter(Alert.equipment_id.in_(metric_ids), Alert.is_resolved == False).order_by(Alert.timestamp.desc()).all()
        schedules = MemberSchedule.query.filter(MemberSchedule.equipment_id.in_(metric_ids)).order_by(MemberSchedule.start_time.asc()).all()

    onboarding_dict = {status: count for status, count in onboarding_stats}

    updated = False
    for lead in leads_list:
        if not lead.public_token:
            lead.public_token = secrets.token_urlsafe(16)
            updated = True

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

    if is_admin:
        leads_list.sort(key=lambda x: x.propensity_score, reverse=True)

    franchise_name = "Global Admin"
    if not is_admin and leads_list:
        franchise_name = leads_list[0].company

    return render_template('dashboard.html',
                           crm_stats=crm_stats,
                           metrics=metrics,
                           alerts=alerts,
                           schedules=schedules,
                           leads_list=leads_list,
                           onboarding_stats=onboarding_dict,
                           is_admin=is_admin,
                           franchise_name=franchise_name)

@admin_bp.route('/feedback')
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
    cat_counts = db.session.query(Feedback.category, db.func.count(Feedback.id)).group_by(Feedback.category).all()
    categories = [c[0] for c in cat_counts]
    category_counts = [c[1] for c in cat_counts]

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

@admin_bp.route('/optimization')
@login_required
@role_required(['Admin'])
def admin_optimization():
    total_members = Member.query.count()
    onboarding_funnel = db.session.query(Member.onboarding_status, db.func.count(Member.id)).group_by(Member.onboarding_status).all()
    onboarding_dict = {status: count for status, count in onboarding_funnel}
    avg_engagement = db.session.query(db.func.avg(Member.engagement_score)).scalar() or 0
    units = EquipmentMetric.query.all()
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

@admin_bp.route('/api/logs')
@login_required
@role_required(['Admin'])
def admin_api_logs():
    """Serves the latest system logs for real-time streaming (v4.5.0)"""
    log_files = ['campaign_launch.log', 'server.log', 'health_monitor.log']
    logs = []
    for log_file in log_files:
        path = os.path.join('logs', log_file)
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    lines = f.readlines()[-8:]
                    logs.append(f"<div class='mb-2'><span class='text-blue-200 font-bold'>[{log_file}]</span>")
                    for line in lines:
                        logs.append(f"<div class='pl-2 opacity-80'>{line.strip()}</div>")
                    logs.append("</div>")
            except Exception as e:
                logs.append(f"Error reading {log_file}: {str(e)}")

    return "".join(logs) if logs else "Waiting for system logs..."

@admin_bp.route('/launch-campaign', methods=['POST'])
@login_required
@role_required(['Admin'])
def admin_launch_campaign():
    """Triggers the autonomous sales pipeline (v3.9.0)"""
    try:
        log_path = os.path.join('logs', 'campaign_launch.log')
        subprocess.Popen(["bash", "launch_campaign.sh"],
                         stdout=open(log_path, "a"),
                         stderr=subprocess.STDOUT)

        log_security_event(current_user.id, "Campaign Launch Triggered: Autonomous sales pipeline (launch_campaign.sh) initiated.")
        flash("Autonomous Campaign Launch Sequence Initiated! Monitor logs for progress.", "success")
    except Exception as e:
        flash(f"Error launching campaign: {str(e)}", "danger")

    return redirect(url_for('admin.admin_command_center'))

@admin_bp.route('/command-center')
@login_required
@role_required(['Admin'])
def admin_command_center():
    region = request.args.get('region')
    automation_status = AutomationHeartbeat.query.all()

    query_metrics = EquipmentMetric.query
    if region:
        query_metrics = query_metrics.filter_by(region_cluster=region)

    metrics = query_metrics.all()
    total_units = len(metrics)

    active_alerts_query = Alert.query.filter_by(is_resolved=False)
    if region:
        metric_ids = [m.id for m in metrics]
        active_alerts_query = active_alerts_query.filter(Alert.equipment_id.in_(metric_ids))
    active_alerts = active_alerts_query.count()

    total_scans = sum(m.total_scans for m in metrics)
    avg_uptime = sum(m.uptime_percent for m in metrics) / total_units if total_units > 0 else 0

    live_sessions_query = db.session.query(TelemetryHistory.member_id).distinct()
    if region:
        metric_ids = [m.id for m in metrics]
        live_sessions_query = live_sessions_query.filter(TelemetryHistory.equipment_id.in_(metric_ids))
    live_sessions = live_sessions_query.limit(10).count()
    alerts = Alert.query.filter_by(is_resolved=False).order_by(Alert.timestamp.desc()).all()

    recent_security = db.session.query(AuditLog, User.username)\
        .outerjoin(User, AuditLog.user_id == User.id)\
        .order_by(AuditLog.timestamp.desc()).limit(10).all()

    return render_template('admin_command_center.html',
                           total_units=total_units,
                           active_alerts=active_alerts,
                           total_scans=total_scans,
                           avg_uptime=round(avg_uptime, 1),
                           live_sessions=live_sessions,
                           metrics=metrics,
                           alerts=alerts,
                           automation_status=automation_status,
                           recent_security=recent_security)

@admin_bp.route('/update_lead_status', methods=['POST'])
@login_required
@permission_required('perm_crm_edit')
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

    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/users/unlock/<int:user_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def admin_unlock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_locked = False
    user.failed_login_attempts = 0
    db.session.commit()
    log_security_event(current_user.id, f"Unlocked user account: {user.username}")
    flash(f"Account for {user.username} has been unlocked.")
    return redirect(url_for('auth.settings'))

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def admin_delete_user(user_id):
    if user_id == current_user.id:
        flash("Cannot delete your own account.")
        return redirect(url_for('auth.settings'))

    user = User.query.get_or_404(user_id)
    username = user.username
    member = Member.query.filter_by(user_id=user.id).first()
    if member:
        db.session.delete(member)

    db.session.delete(user)
    db.session.commit()
    log_security_event(current_user.id, f"Deleted user account: {username}")
    flash(f"Account for {username} and associated member data deleted.")
    return redirect(url_for('auth.settings'))

@admin_bp.route('/generate_report/<int:unit_id>')
@login_required
@role_required(['Admin', 'Franchisee'])
def generate_unit_report(unit_id):
    filepath = generate_report(unit_id)
    if filepath:
        flash(f"Performance report generated successfully: {os.path.basename(filepath)}")
    else:
        flash("Failed to generate performance report.")
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/prospect/<token>')
def prospect_portal(token):
    lead = Lead.query.filter_by(public_token=token).first_or_404()
    if lead.portal_views is None: lead.portal_views = 0
    lead.portal_views += 1
    db.session.commit()
    log_security_event(None, f"Prospect Portal Viewed: {lead.company} (Token: {token})")
    metrics = analytics.calculate_detailed_metrics(
        num_clubs=lead.num_clubs,
        retention_lift_percent=lead.retention_lift,
        avg_monthly_fee=lead.avg_monthly_fee
    )
    return render_template('prospect_portal.html', lead=lead, metrics=metrics)

@admin_bp.route('/resources/<path:filename>')
@login_required
@role_required(['Admin', 'Franchisee'])
def serve_resources(filename):
    return send_from_directory('technical_docs', filename)

@admin_bp.route('/system-health')
@login_required
@role_required(['Admin'])
def admin_system_health():
    """System Health & Integrity Dashboard (v4.4.0)"""
    automation_status = AutomationHeartbeat.query.all()
    health_data = []
    now = datetime.now()
    for task in automation_status:
        last_run = datetime.strptime(task.last_run, "%Y-%m-%d %H:%M:%S")
        diff = (now - last_run).total_seconds()
        status_override = task.status
        if diff > 300: status_override = 'Delayed'
        if diff > 3600: status_override = 'Critical Gap'
        health_data.append({
            'task_name': task.task_name,
            'last_run': task.last_run,
            'status': status_override,
            'latency_sec': int(diff)
        })

    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
    backups = []
    if os.path.exists(backup_dir):
        for f in os.listdir(backup_dir):
            if f.endswith('.db'):
                path = os.path.join(backup_dir, f)
                backups.append({
                    'filename': f,
                    'size_kb': round(os.path.getsize(path) / 1024, 1),
                    'created_at': datetime.fromtimestamp(os.path.getctime(path)).strftime("%Y-%m-%d %H:%M:%S")
                })
    backups.sort(key=lambda x: x['filename'], reverse=True)
    return render_template('admin_system_health.html', health_data=health_data, backups=backups)
