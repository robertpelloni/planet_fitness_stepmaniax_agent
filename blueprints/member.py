from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from models import db, Member, EquipmentMetric, MemberSchedule, TelemetryHistory, Payment, Feedback
from datetime import datetime

member_bp = Blueprint('member', __name__)

@member_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def member_dashboard():
    if current_user.role != 'Member':
        return redirect(url_for('admin.dashboard'))

    member = Member.query.filter_by(user_id=current_user.id).first()
    if not member:
        flash("Member record not found.")
        return redirect(url_for('auth.logout'))

    if request.method == 'POST':
        member.name = request.form.get('name')
        # We don't allow email change for now as it's the username
        db.session.commit()
        flash("Profile updated successfully!")

    # Get available equipment for the member's franchise
    equipment = EquipmentMetric.query.filter_by(franchise_id=member.franchise_id).all()

    # Get member's upcoming sessions
    upcoming_sessions = db.session.query(
        MemberSchedule.start_time,
        MemberSchedule.duration_minutes,
        MemberSchedule.status,
        EquipmentMetric.equipment_name
    ).join(EquipmentMetric, MemberSchedule.equipment_id == EquipmentMetric.id)\
     .filter(MemberSchedule.member_id == member.id)\
     .order_by(MemberSchedule.start_time.asc()).all()

    # Get engagement chart data
    history = TelemetryHistory.query.filter_by(member_id=member.id).order_by(TelemetryHistory.timestamp.asc()).all()
    daily_stats = {}
    for entry in history:
        date = entry.timestamp[:10]
        daily_stats[date] = daily_stats.get(date, 0) + entry.scans_count

    sorted_dates = sorted(daily_stats.keys())
    chart_labels = sorted_dates[-7:] # Last 7 days
    chart_data = [daily_stats[d] for d in chart_labels]

    # Payments (v3.9.2)
    payments = Payment.query.filter_by(member_id=member.id).order_by(Payment.timestamp.desc()).all()

    return render_template('member_dashboard.html',
                           member=member,
                           equipment=equipment,
                           upcoming_sessions=upcoming_sessions,
                           chart_labels=chart_labels,
                           chart_data=chart_data,
                           payments=payments)

@member_bp.route('/submit-feedback', methods=['POST'])
@login_required
def member_submit_feedback():
    """Handles pilot feedback submissions (v3.9.1)"""
    if current_user.role != 'Member':
        abort(403)

    member = Member.query.filter_by(user_id=current_user.id).first()
    rating = request.form.get('rating')
    category = request.form.get('category')
    comment = request.form.get('comment')

    if not rating:
        flash("Please provide a rating.")
        return redirect(url_for('member.member_dashboard'))

    feedback = Feedback(
        member_id=member.id if member else None,
        franchise_id=member.franchise_id if member else None,
        rating=int(rating),
        category=category,
        comment=comment,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.session.add(feedback)
    db.session.commit()

    flash("Thank you for your feedback! It helps us improve the StepManiaX experience.")
    return redirect(url_for('member.member_dashboard'))

@member_bp.route('/book', methods=['POST'])
@login_required
def member_book_session():
    if current_user.role != 'Member':
        abort(403)

    member = Member.query.filter_by(user_id=current_user.id).first()
    equipment_id = request.form.get('equipment_id')
    start_time = request.form.get('start_time')

    if not start_time:
        flash("Please select a valid date and time.")
        return redirect(url_for('member.member_dashboard'))

    # Format datetime for storage
    try:
        dt = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
        formatted_start = dt.strftime('%Y-%m-%d %H:%M')
    except ValueError:
        flash("Invalid date format.")
        return redirect(url_for('member.member_dashboard'))

    new_booking = MemberSchedule(
        member_id=member.id,
        member_name=member.name,
        equipment_id=equipment_id,
        start_time=formatted_start,
        duration_minutes=15, # Default pilot session
        status='Scheduled'
    )
    db.session.add(new_booking)
    db.session.commit()

    flash(f"Session booked for {formatted_start}!")
    return redirect(url_for('member.member_dashboard'))
