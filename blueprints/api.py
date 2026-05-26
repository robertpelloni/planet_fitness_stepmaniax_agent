from flask import Blueprint, request, abort
from flask_login import login_required, current_user
from models import db, User, Member, EquipmentMetric, TelemetryHistory, Payment, Alert
from blueprints.decorators import require_api_or_role, require_api_key, role_required
from datetime import datetime
import os
import config
from gateways import get_payment_gateway
from notifications import send_notification

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

        from blueprints.auth import log_security_event
        log_security_event(None, f"Payment Processed: {result['transaction_id']} for Member {member.id}")
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

@api_bp.route('/v1/analytics/hourly', methods=['GET'])
@require_api_or_role(['Admin', 'Staff', 'Franchisee'])
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

@api_bp.route('/v1/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@login_required
@role_required(['Admin', 'Staff'])
def api_acknowledge_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    alert.acknowledged_by = current_user.username
    db.session.commit()
    return {"status": "acknowledged", "user": current_user.username}, 200

@api_bp.route('/v1/alerts/<int:alert_id>/resolve', methods=['POST'])
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

@api_bp.route('/v1/analytics/usage', methods=['GET'])
@require_api_or_role(['Admin', 'Staff', 'Franchisee'])
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

@api_bp.route('/v1/members', methods=['GET'])
@require_api_or_role(['Admin', 'Staff', 'Franchisee'])
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

@api_bp.route('/v1/members', methods=['POST'])
@require_api_or_role(['Admin', 'Staff'])
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

@api_bp.route('/v1/members/<int:member_id>', methods=['GET', 'PUT', 'DELETE'])
@require_api_or_role(['Admin', 'Staff', 'Franchisee'])
def api_member_detail(member_id):
    member = Member.query.get_or_404(member_id)

    # Multi-tenant isolation for session-based users
    if current_user.is_authenticated:
        if current_user.role != 'Admin' and member.franchise_id != current_user.franchise_id:
            from blueprints.auth import log_security_event
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
