from flask import Blueprint, render_template, redirect, url_for, request, flash, send_from_directory
from flask_login import login_required, current_user
from models import db, User, EquipmentMetric, Alert, Member, Lead, TelemetryHistory, AutomationHeartbeat, Feedback
from blueprints.decorators import role_required, permission_required
from report_generator import generate_report
import analytics
import secrets
import subprocess
import os

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
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
    from models import MemberSchedule
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

@admin_bp.route('/optimization')
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

@admin_bp.route('/launch-campaign', methods=['POST'])
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
        from blueprints.auth import log_security_event
        log_security_event(current_user.id, "Campaign Launch Triggered: Autonomous sales pipeline (launch_campaign.sh) initiated via Command Center.")

        flash("Autonomous Campaign Launch Sequence Initiated! Monitor logs for progress.", "success")
    except Exception as e:
        flash(f"Error launching campaign: {str(e)}", "danger")

    return redirect(url_for('admin.admin_command_center'))

@admin_bp.route('/command-center')
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

    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/users/unlock/<int:user_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def admin_unlock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_locked = False
    user.failed_login_attempts = 0
    db.session.commit()
    from blueprints.auth import log_security_event
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

    # Also find associated member record if any
    member = Member.query.filter_by(user_id=user.id).first()
    if member:
        db.session.delete(member)

    db.session.delete(user)
    db.session.commit()
    from blueprints.auth import log_security_event
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
