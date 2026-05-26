from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Lead, Member, AuditLog
from datetime import datetime
import secrets

auth_bp = Blueprint('auth', __name__)

def log_security_event(user_id, action):
    from flask import request
    log = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=request.remote_addr,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.session.add(log)
    db.session.commit()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user:
            if user.is_locked:
                log_security_event(user.id, f"Login attempt on locked account: {username}")
                flash('Account is locked due to too many failed attempts. Please contact an administrator.')
                return render_template('login.html')

            if user.check_password(password):
                remember = True if request.form.get('remember') else False
                user.failed_login_attempts = 0
                user.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db.session.commit()
                login_user(user, remember=remember)
                log_security_event(user.id, f"Successful login: {username}")

                if user.role == 'Member':
                    return redirect(url_for('member.member_dashboard'))
                if user.role == 'Staff':
                    return redirect(url_for('staff.staff_dashboard'))
                return redirect(url_for('dashboard'))
            else:
                if user.failed_login_attempts is None:
                    user.failed_login_attempts = 0
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.is_locked = True
                    log_security_event(user.id, f"Account locked after 5 failures: {username}")
                else:
                    log_security_event(user.id, f"Failed login attempt: {username} (Attempt {user.failed_login_attempts})")
                db.session.commit()

        flash('Invalid username or password')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/onboard', methods=['GET', 'POST'])
def member_onboarding():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        franchise_id = request.form.get('franchise_id')

        if not all([name, email, password, franchise_id]):
            flash("All fields are required.")
            return redirect(url_for('auth.member_onboarding'))

        if User.query.filter_by(username=email).first():
            flash("An account with this email already exists.")
            return redirect(url_for('auth.member_onboarding'))

        # 1. Create User
        new_user = User(username=email, role='Member', franchise_id=franchise_id)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()

        # 2. Create Member Record
        new_member = Member(
            name=name,
            email=email,
            user_id=new_user.id,
            franchise_id=franchise_id,
            registration_date=datetime.now().strftime("%Y-%m-%d"),
            onboarding_status='Registered'
        )
        db.session.add(new_member)
        db.session.commit()

        flash("Registration successful! Please login to your pilot portal.")
        return redirect(url_for('auth.login'))

    # Get available franchise locations for the dropdown
    leads = Lead.query.filter(Lead.status.contains('Pilot')).all()
    return render_template('onboarding_portal.html', leads=leads)
