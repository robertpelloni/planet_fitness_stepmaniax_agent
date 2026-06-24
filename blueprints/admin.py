from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, send_from_directory
from flask_login import login_required, current_user
from models import db, User, EquipmentMetric, Alert, Lead, AuditLog, OutreachLog, AutomationHeartbeat, Feedback, Member, Payment, TelemetryHistory, MemberSchedule, ServiceDispatch
from sqlalchemy import func
from datetime import datetime
import subprocess
import analytics
import os
import secrets
from blueprints.decorators import role_required, permission_required
from report_generator import generate_report, generate_commercial_proposal, PROPOSALS_DIR
from extensions import log_security_event, csrf

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@role_required(['Admin', 'Franchisee'])
def dashboard():
    # Multi-tenant logic: Filter by franchise_id if user is not an Admin
    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')
    region = request.args.get('region')

    if is_admin:
        query_leads = Lead.query
        query_metrics = EquipmentMetric.query
        query_members = Member.query

        if region:
            query_leads = query_leads.filter_by(region_cluster=region)
            query_metrics = query_metrics.filter_by(region_cluster=region)
            query_members = query_members.filter(Member.franchise_id.in_(
                db.session.query(Lead.id).filter_by(region_cluster=region)
            ))

        crm_stats = db.session.query(Lead.status, db.func.count(Lead.id).label('count'))
        if region: crm_stats = crm_stats.filter_by(region_cluster=region)
        crm_stats = crm_stats.group_by(Lead.status).all()

        metrics = query_metrics.all()

        onboarding_stats = db.session.query(Member.onboarding_status, db.func.count(Member.id))
        if region:
            onboarding_stats = onboarding_stats.filter(Member.franchise_id.in_(
                db.session.query(Lead.id).filter_by(region_cluster=region)
            ))
        onboarding_stats = onboarding_stats.group_by(Member.onboarding_status).all()

        leads_list = query_leads.all()
    else:
        crm_stats = db.session.query(Lead.status, db.func.count(Lead.id).label('count')).filter_by(id=franchise_id).group_by(Lead.status).all()
        metrics = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()
        onboarding_stats = db.session.query(Member.onboarding_status, db.func.count(Member.id)).filter_by(franchise_id=franchise_id).group_by(Member.onboarding_status).all()
        leads_list = Lead.query.filter_by(id=franchise_id).all()

    metric_ids = [m.id for m in metrics]

    if is_admin:
        if region:
            metric_ids = [m.id for m in metrics]
            alerts = Alert.query.filter(Alert.equipment_id.in_(metric_ids), Alert.is_resolved == False).order_by(Alert.timestamp.desc()).all()
            schedules = MemberSchedule.query.filter(MemberSchedule.equipment_id.in_(metric_ids)).order_by(MemberSchedule.start_time.asc()).all()
        else:
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
            'avg_feedback_rating': avg_feedback,
            'notes': lead.notes
        }
        lead.propensity_score = analytics.calculate_propensity_score(lead_dict)

    if updated:
        db.session.commit()

    if is_admin:
        leads_list.sort(key=lambda x: x.propensity_score, reverse=True)

    franchise_name = "Global Admin"
    if region:
        franchise_name = f"Global Admin - {region}"
    if not is_admin and leads_list:
        franchise_name = leads_list[0].company

    all_regions = [r[0] for r in db.session.query(Lead.region_cluster).distinct().all() if r[0]]

    return render_template('dashboard.html',
                           crm_stats=crm_stats,
                           metrics=metrics,
                           alerts=alerts,
                           schedules=schedules,
                           leads_list=leads_list,
                           onboarding_stats=onboarding_dict,
                           is_admin=is_admin,
                           franchise_name=franchise_name,
                           all_regions=all_regions,
                           current_region=region)

@admin_bp.route('/feedback')
@login_required
@role_required(['Admin'])
def admin_feedback():
    """Feedback Analytics Dashboard (v3.9.1)"""
    region = request.args.get('region')

    query = db.session.query(Feedback, Member.name, Lead.company)\
        .outerjoin(Member, Feedback.member_id == Member.id)\
        .outerjoin(Lead, Feedback.franchise_id == Lead.id)

    if region:
        query = query.filter(Lead.region_cluster == region)

    feedback_raw = query.order_by(Feedback.timestamp.desc()).all()

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

    avg_query = db.session.query(db.func.avg(Feedback.rating))
    cat_query = db.session.query(Feedback.category, db.func.count(Feedback.id))
    trend_query = db.session.query(db.func.substr(Feedback.timestamp, 1, 10), db.func.avg(Feedback.rating))

    if region:
        avg_query = avg_query.join(Lead, Feedback.franchise_id == Lead.id).filter(Lead.region_cluster == region)
        cat_query = cat_query.join(Lead, Feedback.franchise_id == Lead.id).filter(Lead.region_cluster == region)
        trend_query = trend_query.join(Lead, Feedback.franchise_id == Lead.id).filter(Lead.region_cluster == region)

    avg_rating = avg_query.scalar() or 0
    cat_counts = cat_query.group_by(Feedback.category).all()
    categories = [c[0] for c in cat_counts]
    category_counts = [c[1] for c in cat_counts]

    trend_raw = trend_query.group_by(db.func.substr(Feedback.timestamp, 1, 10))\
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
    region = request.args.get('region')

    member_query = Member.query
    onboarding_query = db.session.query(Member.onboarding_status, db.func.count(Member.id))
    engagement_query = db.session.query(db.func.avg(Member.engagement_score))
    units_query = EquipmentMetric.query

    if region:
        member_query = member_query.filter(Member.franchise_id.in_(
            db.session.query(Lead.id).filter_by(region_cluster=region)
        ))
        onboarding_query = onboarding_query.filter(Member.franchise_id.in_(
            db.session.query(Lead.id).filter_by(region_cluster=region)
        ))
        engagement_query = engagement_query.filter(Member.franchise_id.in_(
            db.session.query(Lead.id).filter_by(region_cluster=region)
        ))
        units_query = units_query.filter_by(region_cluster=region)

    total_members = member_query.count()
    onboarding_funnel = onboarding_query.group_by(Member.onboarding_status).all()
    onboarding_dict = {status: count for status, count in onboarding_funnel}
    avg_engagement = engagement_query.scalar() or 0
    units = units_query.all()
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

    all_regions = [r[0] for r in db.session.query(Lead.region_cluster).distinct().all() if r[0]]

    return render_template('admin_optimization.html',
                           total_members=total_members,
                           onboarding_stats=onboarding_dict,
                           avg_engagement=round(avg_engagement * 100, 1),
                           recommendations=recommendations,
                           units=units,
                           all_regions=all_regions,
                           current_region=region)

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
                    from markupsafe import escape
                    logs.append(f"<div class='mb-2'><span class='text-blue-200 font-bold'>[{log_file}]</span>")
                    for line in lines:
                        logs.append(f"<div class='pl-2 opacity-80'>{escape(line.strip())}</div>")
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
    all_regions = [r[0] for r in db.session.query(Lead.region_cluster).distinct().all() if r[0]]
    automation_status = AutomationHeartbeat.query.all()
    dispatches = ServiceDispatch.query.order_by(ServiceDispatch.created_at.desc()).limit(10).all()

    # Outreach Metrics (v6.8.0)
    outreach_query = OutreachLog.query
    if region:
        outreach_query = outreach_query.filter(OutreachLog.lead_id.in_(
            db.session.query(Lead.id).filter_by(region_cluster=region)
        ))

    total_outreach = outreach_query.count()
    outreach_by_tier = db.session.query(OutreachLog.notes, func.count(OutreachLog.id))\
        .group_by(OutreachLog.notes).all()

    # Simplify notes to tiers
    tier_counts = {"Initial": 0, "Day 3": 0, "Day 7": 0, "Day 14": 0}
    for note, count in outreach_by_tier:
        if "Tier 0" in note: tier_counts["Initial"] += count
        elif "Tier 1" in note: tier_counts["Day 3"] += count
        elif "Tier 2" in note: tier_counts["Day 7"] += count
        elif "Tier 3" in note: tier_counts["Day 14"] += count

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

    if region:
        metric_ids = [m.id for m in metrics]
        alerts = Alert.query.filter(Alert.equipment_id.in_(metric_ids), Alert.is_resolved == False).order_by(Alert.timestamp.desc()).all()
    else:
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
                           recent_security=recent_security,
                           all_regions=all_regions,
                           current_region=region,
                           dispatches=dispatches,
                           total_outreach=total_outreach,
                           tier_counts=tier_counts)

@admin_bp.route('/pipeline')
@login_required
@role_required(['Admin'])
def admin_pipeline():
    """Kanban-style Sales Pipeline Visualization (v6.7.0)"""
    region = request.args.get('region')
    query = Lead.query
    if region:
        query = query.filter_by(region_cluster=region)
    leads = query.all()

    stages = [
        "Researching",
        "Ready for Outreach",
        "Outreach Active",
        "Discovery Call Scheduled",
        "Pilot MOU Signed",
        "Pilot Operational",
        "Corporate Vendor Approval"
    ]

    pipeline_data = {stage: [] for stage in stages}
    pipeline_data["Other"] = []

    for lead in leads:
        if lead.status in pipeline_data:
            pipeline_data[lead.status].append(lead)
        else:
            pipeline_data["Other"].append(lead)

    all_regions = [r[0] for r in db.session.query(Lead.region_cluster).distinct().all() if r[0]]
    return render_template('admin_pipeline.html', pipeline_data=pipeline_data, stages=stages, all_regions=all_regions, current_region=region)

@admin_bp.route('/leads')
@login_required
@role_required(['Admin'])
def admin_leads():
    region = request.args.get('region')
    query = Lead.query
    if region:
        query = query.filter_by(region_cluster=region)
    leads = query.all()
    all_regions = [r[0] for r in db.session.query(Lead.region_cluster).distinct().all() if r[0]]
    return render_template('admin_leads.html', leads=leads, all_regions=all_regions, current_region=region)

@admin_bp.route('/leads/create', methods=['GET', 'POST'])
@login_required
@role_required(['Admin'])
def admin_lead_create():
    if request.method == 'POST':
        company = request.form.get('company')
        lead_id = company[:3].upper() + "-" + secrets.token_hex(2).upper()

        new_lead = Lead(
            id=lead_id,
            company=company,
            contact_name=request.form.get('contact_name'),
            title=request.form.get('title'),
            email=request.form.get('email'),
            region=request.form.get('region'),
            status=request.form.get('status', 'New'),
            priority=request.form.get('priority', 'Medium'),
            num_clubs=int(request.form.get('num_clubs', 0)),
            notes=request.form.get('notes'),
            public_token=secrets.token_urlsafe(16)
        )
        db.session.add(new_lead)
        db.session.commit()
        log_security_event(current_user.id, f"Created new lead: {company}")
        flash(f"Lead {company} created successfully.")
        return redirect(url_for('admin.admin_leads'))
    return render_template('admin_lead_form.html', action="Create")

@admin_bp.route('/leads/edit/<lead_id>', methods=['GET', 'POST'])
@login_required
@role_required(['Admin'])
def admin_lead_edit(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    if request.method == 'POST':
        lead.company = request.form.get('company')
        lead.contact_name = request.form.get('contact_name')
        lead.title = request.form.get('title')
        lead.email = request.form.get('email')
        lead.region = request.form.get('region')
        lead.status = request.form.get('status')
        lead.priority = request.form.get('priority')
        lead.num_clubs = int(request.form.get('num_clubs', 0))
        lead.notes = request.form.get('notes')

        db.session.commit()
        log_security_event(current_user.id, f"Edited lead: {lead.company}")
        flash(f"Lead {lead.company} updated.")
        return redirect(url_for('admin.admin_leads'))
    return render_template('admin_lead_form.html', action="Edit", lead=lead)

@admin_bp.route('/leads/toggle-cadence/<lead_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def admin_toggle_cadence(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    lead.cadence_paused = not lead.cadence_paused
    db.session.commit()
    return render_template('partials/lead_row.html', lead=lead)

@admin_bp.route('/leads/reset-cadence/<lead_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def admin_reset_cadence(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    lead.follow_up_count = 0
    lead.status = 'Ready for Outreach'
    lead.last_contact_date = None
    lead.cadence_paused = False
    db.session.commit()
    return render_template('partials/lead_row.html', lead=lead)

@admin_bp.route('/leads/update-status/<lead_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def admin_update_lead_status(lead_id):
    """Updates lead status and logs the transition (v6.6.0)"""
    new_status = request.form.get('status')
    lead = Lead.query.get_or_404(lead_id)
    old_status = lead.status
    lead.status = new_status
    db.session.commit()
    log_security_event(current_user.id, f"Lead {lead_id} Status Transition: {old_status} -> {new_status}")
    return render_template('partials/lead_row.html', lead=lead)

@admin_bp.route('/leads/dispatch-outreach/<lead_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def admin_dispatch_outreach(lead_id):
    """Manually triggers the next outreach tier for a specific lead (v6.6.0)"""
    from launch_outreach import launch_outreach
    try:
        launch_outreach(force_lead_id=lead_id)
        log_security_event(current_user.id, f"Manual Outreach Dispatched: Lead {lead_id}")
    except Exception as e:
        print(f"Error in manual dispatch: {e}")

    lead = Lead.query.get_or_404(lead_id)
    return render_template('partials/lead_row.html', lead=lead)

@admin_bp.route('/leads/delete/<lead_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def admin_lead_delete(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    company = lead.company
    db.session.delete(lead)
    db.session.commit()
    log_security_event(current_user.id, f"Deleted lead: {company}")
    flash(f"Lead {company} deleted.")
    return redirect(url_for('admin.admin_leads'))

@admin_bp.route('/leads/convert/<lead_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def convert_lead_to_partner(lead_id):
    """Converts a successful lead into a 'Franchisee' user account (v6.7.0)"""
    lead = Lead.query.get_or_404(lead_id)

    existing_user = User.query.filter_by(franchise_id=lead.id).first()
    if existing_user:
        flash(f"Partner account already exists for {lead.company} ({existing_user.username}).", "warning")
        return redirect(url_for('admin.admin_leads'))

    # Generate Partner Account
    username = lead.email if lead.email else f"partner_{lead.id.lower()}"
    password = secrets.token_hex(8)

    new_user = User(
        username=username,
        role='Franchisee',
        franchise_id=lead.id,
        region_cluster=lead.region_cluster or 'US-EAST-1',
        perm_crm_view=True,
        perm_crm_edit=False,
        perm_ops_view=True,
        perm_revenue_view=True
    )
    new_user.set_password(password)

    # Auto-promote status if not already advanced
    if lead.status not in ['Contract Finalized', 'Pilot Operational']:
        lead.status = 'Contract Finalized'

    db.session.add(new_user)
    db.session.commit()

    log_security_event(current_user.id, f"CONVERSION: Lead {lead.company} converted to Partner. User: {username}")
    flash(f"SUCCESS: {lead.company} has been converted to a Partner! Login: {username} | Temp Password: {password}", "success")

    return redirect(url_for('admin.admin_leads'))

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
        flash(f"Status updated for lead {lead.company} to {new_status}")
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

@admin_bp.route('/leads/download-proposal/<lead_id>')
@login_required
@role_required(['Admin'])
def download_proposal(lead_id):
    """Generates and downloads a commercial expansion proposal (v6.7.0)"""
    filepath = generate_commercial_proposal(lead_id)
    if filepath:
        return send_from_directory(PROPOSALS_DIR, os.path.basename(filepath), as_attachment=True)
    flash("Error generating proposal.")
    return redirect(url_for('admin.admin_leads'))

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

@admin_bp.route('/prospect/track-interaction/<token>', methods=['POST'])
@csrf.exempt
def track_prospect_interaction(token):
    """Logs high-intent interaction from the ROI simulator (v6.5.0)"""
    lead = Lead.query.filter_by(public_token=token).first_or_404()

    # Increment engagement signal
    if lead.notes is None: lead.notes = ""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lead.notes = f"[{timestamp}] HIGH INTENT: Prospect interacted with ROI Simulator.\n" + lead.notes

    # Also increment portal views as a proxy for engagement
    lead.portal_views += 1

    db.session.commit()
    log_security_event(None, f"High-Intent Signal: {lead.company} interacted with ROI Simulator.")
    return "", 204

@admin_bp.route('/prospect/request-demo/<token>', methods=['POST'])
@csrf.exempt
def request_prospect_demo(token):
    """Handles demo requests from the prospect portal (v6.8.0)"""
    lead = Lead.query.filter_by(public_token=token).first_or_404()

    name = request.form.get('name')
    email = request.form.get('email')
    preferred_time = request.form.get('preferred_time')

    # Update Lead
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lead.status = 'Discovery Call Scheduled'
    if lead.notes is None: lead.notes = ""
    lead.notes = f"[{timestamp}] DEMO REQUESTED: {name} ({email}) requested a demo for {preferred_time}.\n" + lead.notes

    db.session.commit()
    log_security_event(None, f"DEMO REQUEST: {lead.company} requested a priority discovery call.")

    return f"""
        <div class="bg-green-900/20 border border-green-500/50 rounded-2xl p-8 text-center animate-pulse">
            <i class="fa-solid fa-circle-check text-4xl text-green-500 mb-4"></i>
            <h3 class="text-xl font-black text-white italic uppercase tracking-tight">Request Received</h3>
            <p class="text-green-400 text-sm mt-2 font-medium">Thank you, {name}. Our regional director will contact you shortly to confirm your slot.</p>
        </div>
    """

@admin_bp.route('/pilot-success')
@login_required
@role_required(['Admin'])
def admin_pilot_success():
    """Pilot Success Dashboard: ROI Tracking (v6.3.0)"""
    region = request.args.get('region')

    query = Lead.query.filter(Lead.status.contains('Pilot'))
    if region:
        query = query.filter_by(region_cluster=region)

    pilot_leads = query.all()
    pilot_stats = []

    for lead in pilot_leads:
        # Calculate actual revenue from payments
        actual_revenue = db.session.query(func.sum(Payment.amount))\
            .join(Member, Payment.member_id == Member.id)\
            .filter(Member.franchise_id == lead.id, Payment.status == 'Completed').scalar() or 0.0

        # Success Score: (Actual / Projected) * 100
        target = lead.projected_annual_profit / 52 if lead.projected_annual_profit else 1000 # Weekly target approx
        # Since payments might be sparse in test data, we use a simulation factor if actuals are 0
        success_score = min(100.0, (actual_revenue / target * 100)) if target > 0 else 0

        pilot_stats.append({
            "company": lead.company,
            "region": lead.region,
            "target": round(target, 2),
            "actual": round(actual_revenue, 2),
            "score": round(success_score, 1),
            "status": lead.status
        })

    all_regions = [r[0] for r in db.session.query(Lead.region_cluster).distinct().all() if r[0]]
    return render_template('admin_pilot_success.html', pilot_stats=pilot_stats, all_regions=all_regions, current_region=region)
