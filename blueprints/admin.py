from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, send_from_directory
from flask_login import login_required, current_user
from models import db, User, EquipmentMetric, Alert, Lead, AuditLog, AutomationHeartbeat, Feedback, Member
from datetime import datetime
import subprocess
import analytics
import os
from blueprints.decorators import role_required
from report_generator import generate_report

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/feedback')
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

@admin_bp.route('/admin/optimization')
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

@admin_bp.route('/admin/api/logs')
@login_required
@role_required(['Admin'])
def admin_api_logs():
    """Serves the latest system logs for real-time streaming (v3.9.0)"""
    log_files = ['campaign_launch.log', 'server.log']
    logs = []
    for log_file in log_files:
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()[-5:]
                logs.extend([f"[{log_file}] {line.strip()}" for line in lines])

    return "<br>".join(logs) if logs else "Waiting for system logs..."

@admin_bp.route('/admin/launch-campaign', methods=['POST'])
@login_required
@role_required(['Admin'])
def admin_launch_campaign():
    """Triggers the autonomous sales pipeline (v3.9.0)"""
    try:
        subprocess.Popen(["bash", "launch_campaign.sh"],
                         stdout=open("campaign_launch.log", "a"),
                         stderr=subprocess.STDOUT)

        log_security_event(current_user.id, "Campaign Launch Triggered: Autonomous sales pipeline (launch_campaign.sh) initiated via Command Center.")
        flash("Autonomous Campaign Launch Sequence Initiated! Monitor logs for progress.", "success")
    except Exception as e:
        flash(f"Error launching campaign: {str(e)}", "danger")

    return redirect(url_for('admin.admin_command_center'))

@admin_bp.route('/admin/command-center')
@login_required
@role_required(['Admin'])
def admin_command_center():
    automation_status = AutomationHeartbeat.query.all()
    total_units = EquipmentMetric.query.count()
    active_alerts = Alert.query.filter_by(is_resolved=False).count()
    total_scans = db.session.query(db.func.sum(EquipmentMetric.total_scans)).scalar() or 0
    avg_uptime = db.session.query(db.func.avg(EquipmentMetric.uptime_percent)).scalar() or 0

    from models import TelemetryHistory
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

@admin_bp.route('/update_lead_status', methods=['POST'])
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

@admin_bp.route('/admin/users/unlock/<int:user_id>', methods=['POST'])
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

@admin_bp.route('/admin/users/delete/<int:user_id>', methods=['POST'])
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
    return redirect(url_for('dashboard'))

@admin_bp.route('/prospect/<token>')
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

@admin_bp.route('/resources/<path:filename>')
@login_required
@role_required(['Admin', 'Franchisee'])
def serve_resources(filename):
    # Restrict to technical/alignment docs directory for security
    return send_from_directory('technical_docs', filename)

@admin_bp.route('/admin/system-health')
@login_required
@role_required(['Admin'])
def admin_system_health():
    """System Health & Integrity Dashboard (v4.4.0)"""
    automation_status = AutomationHeartbeat.query.all()

    # Analyze latency
    health_data = []
    now = datetime.now()
    for task in automation_status:
        last_run = datetime.strptime(task.last_run, "%Y-%m-%d %H:%M:%S")
        diff = (now - last_run).total_seconds()

        status_override = task.status
        if diff > 300: # 5 minutes
            status_override = 'Delayed'
        if diff > 3600: # 1 hour
            status_override = 'Critical Gap'

        health_data.append({
            'task_name': task.task_name,
            'last_run': task.last_run,
            'status': status_override,
            'latency_sec': int(diff)
        })

    # Backup History
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

def log_security_event(user_id, action):
    log = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=request.remote_addr,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.session.add(log)
    db.session.commit()
