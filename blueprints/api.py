from flask import Blueprint, request, abort, current_app
from flask_login import current_user
from models import db, Member, EquipmentMetric, TelemetryHistory, Alert, Payment, User, Feedback, MemberSchedule, Lead
from datetime import datetime
import os
import config
import secrets
from notifications import send_notification
from gateways import get_payment_gateway
from blueprints.decorators import require_api_key, require_api_or_role

api_bp = Blueprint('api', __name__)

@api_bp.route('/v1/payments', methods=['POST'])
@require_api_or_role(['Admin', 'Member'])
def api_process_payment():
    """Processes membership payments via configured gateway (v3.9.2)"""
    data = request.get_json()
    if not data or 'member_id' not in data or 'amount' not in data:
        return {"error": "Invalid payment data"}, 400

    member = Member.query.get(data['member_id'])
    if not member:
        return {"error": "Member not found"}, 404

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

        return {"status": "success", "transaction_id": result['transaction_id']}, 201
    else:
        return {"error": "Payment failed", "details": result.get('error')}, 400

@api_bp.route('/v1/telemetry', methods=['POST'])
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

    unit.last_heartbeat = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    member_id = data.get('member_id')
    member = None
    if member_id:
        member = Member.query.get(member_id)

    if 'uptime_percent' in data:
        unit.uptime_percent = data['uptime_percent']

    if 'scans_increment' in data:
        unit.total_scans += data['scans_increment']
        history = TelemetryHistory(
            equipment_id=unit.id,
            member_id=member_id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            scans_count=data['scans_increment'],
            duration_minutes=data.get('session_duration', 0.0)
        )
        db.session.add(history)

        if member:
            member.points += data['scans_increment']
            reg_date = datetime.strptime(member.registration_date, "%Y-%m-%d")
            days_active = (datetime.now() - reg_date).days + 1
            member.engagement_score = min(1.0, member.points / (days_active * 100))

    if 'session_duration' in data:
        new_duration = data['session_duration']
        unit.avg_session_duration = ((unit.avg_session_duration * unit.total_sessions) + new_duration) / (unit.total_sessions + 1)
        unit.total_sessions += 1

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
            unit.maintenance_status = 'Needs Maintenance'
            send_notification(f"⚠️ [CRITICAL] {alert_msg}", franchise_id=unit.franchise_id)

    db.session.commit()
    return {"status": "success", "unit": unit.equipment_name}, 200

@api_bp.route('/v1/analytics/hourly', methods=['GET'])
@require_api_or_role(['Admin', 'Staff', 'Franchisee'])
def api_hourly_analytics():
    """Returns scan distribution by hour of day (0-23)."""
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
        try:
            hour = int(entry.timestamp[11:13])
            hourly_distribution[hour] += entry.scans_count
        except (ValueError, IndexError):
            continue

    return {
        "labels": [f"{h:02d}:00" for h in range(24)],
        "data": [hourly_distribution[h] for h in range(24)]
    }, 200

@api_bp.route('/v1/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@require_api_or_role(['Admin', 'Staff'])
def api_acknowledge_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    alert.acknowledged_by = current_user.username if current_user.is_authenticated else "API-USER"
    db.session.commit()
    return {"status": "acknowledged", "user": alert.acknowledged_by}, 200

@api_bp.route('/v1/alerts/<int:alert_id>/resolve', methods=['POST'])
@require_api_or_role(['Admin', 'Staff'])
def api_resolve_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    alert.is_resolved = True
    alert.resolved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alert.resolved_by = current_user.username if current_user.is_authenticated else "API-USER"

    unit = EquipmentMetric.query.get(alert.equipment_id)
    if unit:
        remaining = Alert.query.filter_by(equipment_id=unit.id, is_resolved=False).count()
        if remaining <= 1:
            unit.maintenance_status = 'Operational'

    db.session.commit()
    return {"status": "resolved", "user": alert.resolved_by}, 200

@api_bp.route('/v1/analytics/usage', methods=['GET'])
@require_api_or_role(['Admin', 'Staff', 'Franchisee'])
def api_usage_analytics():
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

    daily_stats = {}
    for entry in history:
        date = entry.timestamp[:10]
        daily_stats[date] = daily_stats.get(date, 0) + entry.scans_count

    sorted_dates = sorted(daily_stats.keys())

    return {
        "labels": sorted_dates,
        "data": [daily_stats[d] for d in sorted_dates]
    }, 200

@api_bp.route('/v1/members', methods=['GET'])
@require_api_or_role(['Admin', 'Staff', 'Franchisee'])
def api_list_members():
    is_admin = not current_user.is_authenticated or current_user.role == 'Admin'

    if is_admin:
        franchise_id = request.args.get('franchise_id')
        if not franchise_id:
            members = Member.query.all()
        else:
            members = Member.query.filter_by(franchise_id=franchise_id).all()
    else:
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

@api_bp.route('/v1/members', methods=['POST'])
@require_api_or_role(['Admin', 'Staff'])
def api_create_member():
    data = request.get_json()
    if not data or 'email' not in data or 'name' not in data or 'password' not in data:
        return {"error": "Missing required fields"}, 400

    if User.query.filter_by(username=data['email']).first():
        return {"error": "User already exists"}, 409

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

@api_bp.route('/v1/members/<int:member_id>', methods=['GET', 'PUT', 'DELETE'])
@require_api_or_role(['Admin', 'Staff', 'Franchisee'])
def api_member_detail(member_id):
    member = Member.query.get_or_404(member_id)

    if current_user.is_authenticated:
        if current_user.role != 'Admin' and member.franchise_id != current_user.franchise_id:
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
        user = User.query.get(member.user_id)
        if user:
            db.session.delete(user)
        db.session.delete(member)
        db.session.commit()
        return {"status": "deleted"}

@api_bp.route('/v1/feedback', methods=['POST'])
@require_api_or_role(['Admin', 'Member'])
def api_submit_feedback():
    data = request.get_json()
    if not data or 'rating' not in data:
        return {"error": "Rating is required"}, 400

    member_id = data.get('member_id')
    if not member_id and current_user.is_authenticated and current_user.role == 'Member':
        member = Member.query.filter_by(user_id=current_user.id).first()
        member_id = member.id if member else None

    feedback = Feedback(
        member_id=member_id,
        franchise_id=data.get('franchise_id'),
        rating=int(data['rating']),
        category=data.get('category', 'General'),
        comment=data.get('comment'),
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.session.add(feedback)
    db.session.commit()
    return {"status": "success", "feedback_id": feedback.id}, 201

@api_bp.route('/v1/members/sync', methods=['POST'])
@require_api_key
def api_sync_members():
    """Secure bulk sync for member statuses."""
    data = request.get_json()
    if not data or not isinstance(data, list):
        return {"error": "Invalid data format, expected list"}, 400

    results = {"updated": 0, "errors": []}
    for item in data:
        email = item.get('email')
        status = item.get('status')
        if not email or not status:
            results['errors'].append({"email": email, "error": "Missing email or status"})
            continue

        member = Member.query.filter_by(email=email).first()
        if member:
            member.onboarding_status = status
            results['updated'] += 1
        else:
            results['errors'].append({"email": email, "error": "Member not found"})

    db.session.commit()
    return results, 200

@api_bp.route('/v1/telemetry/check-in', methods=['POST'])
@require_api_key
def api_hardware_checkin():
    """Hardware Check-in Integration (v5.2.0)"""
    data = request.get_json()
    if not data:
        return {"error": "Invalid check-in packet"}, 400

    nfc_uid = data.get('nfc_uid')
    biometric_token = data.get('biometric_token')
    equipment_id = data.get('equipment_id')

    if not equipment_id:
        return {"error": "Equipment ID required"}, 400

    member = None
    if nfc_uid:
        member = Member.query.filter_by(nfc_uid=nfc_uid).first()
    elif biometric_token:
        member = Member.query.filter_by(biometric_token=biometric_token).first()

    if not member:
        return {"error": "Member not identified"}, 404

    history = TelemetryHistory(
        equipment_id=equipment_id,
        member_id=member.id,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        scans_count=1
    )
    db.session.add(history)
    member.points += 1
    db.session.commit()

    return {
        "status": "success",
        "member_name": member.name,
        "points_total": member.points
    }, 200

@api_bp.route('/v1/auth/member-login', methods=['POST'])
@require_api_key
def api_member_login():
    """Secure Member Auth (v5.3.0)"""
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return {"error": "Email and password required"}, 400

    user = User.query.filter_by(username=data['email'], role='Member').first()
    if user and user.check_password(data['password']):
        if user.is_locked:
            return {"error": "Account is locked"}, 403

        member = Member.query.filter_by(user_id=user.id).first()
        return {
            "status": "authenticated",
            "member_id": member.id if member else None,
            "name": member.name if member else user.username,
            "session_token": secrets.token_urlsafe(32)
        }, 200

    return {"error": "Invalid credentials"}, 401

@api_bp.route('/v1/schedules/book', methods=['POST'])
@require_api_key
def api_book_session():
    """Stateless Scheduling (v5.3.0)"""
    data = request.get_json()
    if not data or not all(k in data for k in ['member_id', 'equipment_id', 'start_time']):
        return {"error": "Missing booking details"}, 400

    existing = MemberSchedule.query.filter_by(
        equipment_id=data['equipment_id'],
        start_time=data['start_time'].replace('T', ' ')
    ).first()

    if existing:
        return {"error": "Slot already occupied"}, 409

    new_booking = MemberSchedule(
        member_id=data['member_id'],
        member_name=data.get('member_name', 'External Booking'),
        equipment_id=data['equipment_id'],
        start_time=data['start_time'].replace('T', ' '),
        duration_minutes=int(data.get('duration_minutes', 15)),
        status='Scheduled'
    )
    db.session.add(new_booking)
    db.session.commit()

    return {
        "status": "confirmed",
        "booking_id": new_booking.id
    }, 201

@api_bp.route('/v1/enterprise/export', methods=['GET'])
@require_api_or_role(['Admin'])
def api_enterprise_export():
    """Enterprise Data Exchange (v4.8.0)"""
    units = EquipmentMetric.query.all()
    telemetry_data = [{
        "unit_id": u.id,
        "name": u.equipment_name,
        "location": u.location,
        "uptime": u.uptime_percent,
        "scans": u.total_scans,
        "health_score": u.predictive_health_score,
        "status": u.maintenance_status
    } for u in units]

    members = Member.query.all()
    engagement_data = [{
        "member_id": m.id,
        "status": m.onboarding_status,
        "points": m.points,
        "engagement_score": m.engagement_score,
        "franchise_id": m.franchise_id
    } for m in members]

    feedback = Feedback.query.all()
    sentiment_data = [{
        "rating": f.rating,
        "category": f.category,
        "timestamp": f.timestamp,
        "franchise_id": f.franchise_id
    } for f in feedback]

    return {
        "version": "4.8.0",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "telemetry": telemetry_data,
        "engagement": engagement_data,
        "sentiment": sentiment_data
    }, 200

@api_bp.route('/v1/enterprise/leads', methods=['GET'])
@require_api_or_role(['Admin'])
def api_enterprise_leads():
    """Enterprise Lead Sync (v4.8.0)"""
    leads = Lead.query.all()
    lead_data = [{
        "id": l.id,
        "company": l.company,
        "region": l.region,
        "status": l.status,
        "priority": l.priority,
        "propensity_score": l.propensity_score if hasattr(l, 'propensity_score') else 0,
        "portal_views": l.portal_views
    } for l in leads]

    return {
        "count": len(lead_data),
        "leads": lead_data
    }, 200

@api_bp.route('/v1/analytics/live-occupancy', methods=['GET'])
@require_api_or_role(['Admin', 'Staff', 'Franchisee'])
def api_live_occupancy():
    """Live Occupancy Analytics (v5.0.0)"""
    if current_user.is_authenticated:
        franchise_id = current_user.franchise_id
        is_admin = (current_user.role == 'Admin')
    else:
        franchise_id = request.args.get('franchise_id')
        is_admin = not franchise_id

    if is_admin:
        units = EquipmentMetric.query.all()
    else:
        units = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()

    unit_intensity = []
    total_active_scans = 0

    for u in units:
        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
        recent_scans = db.session.query(db.func.sum(TelemetryHistory.scans_count)).filter(
            TelemetryHistory.equipment_id == u.id,
            TelemetryHistory.timestamp >= cutoff
        ).scalar() or 0

        intensity = min(1.0, recent_scans / 10.0)
        unit_intensity.append({
            "unit_id": u.id,
            "name": u.equipment_name,
            "intensity": intensity,
            "scans": recent_scans
        })
        total_active_scans += recent_scans

    active_shifts = MemberSchedule.query.filter(
        MemberSchedule.status == 'Scheduled',
        MemberSchedule.start_time.contains(datetime.now().strftime("%Y-%m-%d"))
    ).count()

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_active_scans": total_active_scans,
        "active_staff": active_shifts,
        "units": unit_intensity
    }, 200
