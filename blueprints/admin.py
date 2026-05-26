from flask import Blueprint, render_template, redirect, url_for, request, flash, send_from_directory
from flask_login import login_required, current_user
from models import db, EquipmentMetric, Alert, Member, MemberSchedule, Lead, Feedback, AutomationHeartbeat, User
from blueprints.decorators import role_required, permission_required
from report_generator import generate_report
import analytics
import secrets
import subprocess
import os

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@permission_required('perm_crm_view')
def dashboard():
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')
    if is_admin:
        crm_stats = db.session.query(Lead.status, db.func.count(Lead.id).label('count')).group_by(Lead.status).all()
        metrics = EquipmentMetric.query.all()
    else:
        crm_stats = db.session.query(Lead.status, db.func.count(Lead.id).label('count')).filter_by(id=franchise_id).group_by(Lead.status).all()
        metrics = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()

    metric_ids = [m.id for m in metrics]
    if is_admin:
        alerts = Alert.query.filter_by(is_resolved=False).order_by(Alert.timestamp.desc()).all()
        schedules = MemberSchedule.query.order_by(MemberSchedule.start_time.asc()).all()
        onboarding_stats = db.session.query(Member.onboarding_status, db.func.count(Member.id)).group_by(Member.onboarding_status).all()
        leads_list = Lead.query.all()
    else:
        alerts = Alert.query.filter(Alert.equipment_id.in_(metric_ids), Alert.is_resolved == False).order_by(Alert.timestamp.desc()).all()
        schedules = MemberSchedule.query.filter(MemberSchedule.equipment_id.in_(metric_ids)).order_by(MemberSchedule.start_time.asc()).all()
        onboarding_stats = db.session.query(Member.onboarding_status, db.func.count(Member.id)).filter_by(franchise_id=franchise_id).group_by(Member.onboarding_status).all()
        leads_list = Lead.query.filter_by(id=franchise_id).all()

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
            'pilot_engagement': {'member_count': member_count, 'total_points': total_points},
            'portal_views': lead.portal_views,
            'avg_feedback_rating': avg_feedback
        }
        lead.propensity_score = analytics.calculate_propensity_score(lead_dict)
    if updated: db.session.commit()
    if is_admin: leads_list.sort(key=lambda x: x.propensity_score, reverse=True)

    return render_template('dashboard.html',
                           crm_stats=crm_stats,
                           metrics=metrics,
                           alerts=alerts,
                           schedules=schedules,
                           leads_list=leads_list,
                           onboarding_stats=onboarding_dict,
                           is_admin=is_admin,
                           franchise_name=leads_list[0].company if not is_admin and leads_list else "Global Admin")

@admin_bp.route('/command-center')
@login_required
@role_required(['Admin'])
def admin_command_center():
    automation_status = AutomationHeartbeat.query.all()
    total_units = EquipmentMetric.query.count()
    active_alerts = Alert.query.filter_by(is_resolved=False).count()
    total_scans = db.session.query(db.func.sum(EquipmentMetric.total_scans)).scalar() or 0
    avg_uptime = db.session.query(db.func.avg(EquipmentMetric.uptime_percent)).scalar() or 0
    metrics = EquipmentMetric.query.all()
    alerts = Alert.query.filter_by(is_resolved=False).order_by(Alert.timestamp.desc()).all()
    return render_template('admin_command_center.html', total_units=total_units, active_alerts=active_alerts, total_scans=total_scans, avg_uptime=round(avg_uptime, 1), metrics=metrics, alerts=alerts, automation_status=automation_status)

@admin_bp.route('/feedback')
@login_required
@role_required(['Admin'])
def admin_feedback():
    feedback_raw = db.session.query(Feedback, Member.name, Lead.company).outerjoin(Member, Feedback.member_id == Member.id).outerjoin(Lead, Feedback.franchise_id == Lead.id).all()
    feedback_list = [{"timestamp": f.timestamp, "member_name": m_name, "company": company, "category": f.category, "rating": f.rating, "comment": f.comment} for f, m_name, company in feedback_raw]
    avg_rating = db.session.query(db.func.avg(Feedback.rating)).scalar() or 0
    return render_template('admin_feedback.html', feedback_list=feedback_list, avg_rating=avg_rating)

@admin_bp.route('/optimization')
@login_required
@role_required(['Admin'])
def admin_optimization():
    units = EquipmentMetric.query.all()
    recommendations = analytics.generate_optimization_recommendations([{"equipment_name": u.equipment_name, "location": u.location, "uptime_percent": u.uptime_percent, "total_sessions": u.total_sessions} for u in units])
    return render_template('admin_optimization.html', recommendations=recommendations, units=units)

@admin_bp.route('/update_lead_status', methods=['POST'])
@login_required
@permission_required('perm_crm_edit')
def update_lead_status():
    lead_id, new_status = request.form.get('lead_id'), request.form.get('status')
    lead = Lead.query.get_or_404(lead_id)
    lead.status = new_status
    db.session.commit()
    flash(f"Status for {lead.company} updated to {new_status}.")
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/generate_report/<int:unit_id>')
@login_required
def generate_unit_report(unit_id):
    filepath = generate_report(unit_id)
    if filepath: flash(f"Performance report generated successfully: {os.path.basename(filepath)}")
    else: flash("Failed to generate performance report.")
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/launch-campaign', methods=['POST'])
@login_required
@role_required(['Admin'])
def admin_launch_campaign():
    subprocess.Popen(["bash", "launch_campaign.sh"], stdout=open("campaign_launch.log", "a"), stderr=subprocess.STDOUT)
    flash("Campaign launched!")
    return redirect(url_for('admin.admin_command_center'))

@admin_bp.route('/users/unlock/<int:user_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def admin_unlock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_locked = False
    db.session.commit()
    flash(f"User {user.username} unlocked.")
    return redirect(url_for('auth.settings'))

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f"User deleted.")
    return redirect(url_for('auth.settings'))

@admin_bp.route('/users/update-permissions/<int:user_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def admin_update_permissions(user_id):
    user = User.query.get_or_404(user_id)
    user.perm_crm_view = bool(request.form.get('perm_crm_view'))
    user.perm_crm_edit = bool(request.form.get('perm_crm_edit'))
    user.perm_ops_view = bool(request.form.get('perm_ops_view'))
    user.perm_revenue_view = bool(request.form.get('perm_revenue_view'))
    db.session.commit()
    flash(f"Permissions updated for {user.username}.")
    return redirect(url_for('auth.settings'))

@admin_bp.route('/api/logs')
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

@admin_bp.route('/security')
@login_required
@role_required(['Admin'])
def admin_security():
    """Security Intelligence Dashboard (v4.2.0)"""
    from models import AuditLog

    # Audit log distribution by action
    logs_raw = db.session.query(AuditLog.action, db.func.count(AuditLog.id))\
        .group_by(AuditLog.action).all()
    actions = [l[0][:30] + "..." if len(l[0]) > 30 else l[0] for l in logs_raw]
    action_counts = [l[1] for l in logs_raw]

    # Failed login attempts trend
    failed_logins = AuditLog.query.filter(AuditLog.action.contains("Failed login attempt")).all()
    failed_trend = {}
    for log in failed_logins:
        date = log.timestamp[:10]
        failed_trend[date] = failed_trend.get(date, 0) + 1

    trend_labels = sorted(failed_trend.keys())
    trend_data = [failed_trend[d] for d in trend_labels]

    # Recent high-severity events (locked accounts, unauthorized access)
    security_events = AuditLog.query.filter(
        db.or_(
            AuditLog.action.contains("locked"),
            AuditLog.action.contains("Unauthorized"),
            AuditLog.action.contains("Deleted")
        )
    ).order_by(AuditLog.timestamp.desc()).limit(20).all()

    return render_template('admin_security.html',
                           actions=actions,
                           action_counts=action_counts,
                           trend_labels=trend_labels,
                           trend_data=trend_data,
                           security_events=security_events)

@admin_bp.route('/resources/<path:filename>')
@login_required
def serve_resources(filename):
    return send_from_directory('outreach/generated', filename)
