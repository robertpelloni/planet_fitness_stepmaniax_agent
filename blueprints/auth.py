from flask import Blueprint, render_template, redirect, url_for, request, flash, session, send_file
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Lead, Member, AuditLog, Webhook
from datetime import datetime, timedelta
from blueprints.decorators import role_required
import secrets
import pyotp
import qrcode
import io
import re
from extensions import limiter

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

def is_password_complex(password):
    """
    Validates password complexity:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, ""

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
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
                if user.mfa_enabled:
                    # Partial login, require TOTP
                    session['mfa_user_id'] = user.id
                    session['mfa_remember'] = True if request.form.get('remember') else False
                    return redirect(url_for('auth.login_2fa'))

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
    username = current_user.username
    user_id = current_user.id
    logout_user()
    log_security_event(user_id, f"User logged out: {username}")
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(username=email).first()
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
            db.session.commit()
            # In a production app, we would send an email here.
            # For the pilot, we flash the reset URL for the simulator.
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            log_security_event(user.id, f"Password reset requested: {email}")
            flash(f"Reset link generated (Pilot Simulation): {reset_url}")
        else:
            # Prevent user enumeration
            flash("If an account exists for that email, a reset link has been sent.")
        return redirect(url_for('auth.login'))
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user:
        flash("Invalid or expired reset token.")
        return redirect(url_for('auth.login'))

    expiry = datetime.strptime(user.reset_token_expiry, "%Y-%m-%d %H:%M:%S")
    if datetime.now() > expiry:
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        flash("Reset token has expired.")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        new_pw = request.form.get('password')
        confirm_pw = request.form.get('confirm_password')

        if new_pw != confirm_pw:
            flash("Passwords do not match.")
            return render_template('reset_password.html', token=token)

        is_valid, msg = is_password_complex(new_pw)
        if not is_valid:
            flash(msg)
            return render_template('reset_password.html', token=token)

        user.set_password(new_pw)
        user.reset_token = None
        user.reset_token_expiry = None
        user.failed_login_attempts = 0
        user.is_locked = False
        db.session.commit()
        log_security_event(user.id, "Password reset successfully via token")
        flash("Password reset successful! Please login.")
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', token=token)

@auth_bp.route('/onboard', methods=['GET', 'POST'])
def member_onboarding():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        franchise_id = request.form.get('franchise_id')

        if not all([name, email, password, franchise_id]):
            log_security_event(None, f"Incomplete onboarding attempt for email: {email}")
            flash("All fields are required.")
            return redirect(url_for('auth.member_onboarding'))

        if User.query.filter_by(username=email).first():
            log_security_event(None, f"Onboarding attempt with existing email: {email}")
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

@auth_bp.route('/login/2fa', methods=['GET', 'POST'])
def login_2fa():
    if 'mfa_user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        token = request.form.get('token')
        user = User.query.get(session['mfa_user_id'])

        if user and pyotp.TOTP(user.mfa_secret).verify(token):
            remember = session.pop('mfa_remember', False)
            session.pop('mfa_user_id')

            user.failed_login_attempts = 0
            user.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db.session.commit()

            login_user(user, remember=remember)
            log_security_event(user.id, f"Successful 2FA login: {user.username}")

            if user.role == 'Member':
                return redirect(url_for('member.member_dashboard'))
            if user.role == 'Staff':
                return redirect(url_for('staff.staff_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid 2FA token.")

    return render_template('login_2fa.html')

@auth_bp.route('/mfa/setup')
@login_required
def mfa_setup():
    if not current_user.mfa_secret:
        current_user.mfa_secret = pyotp.random_base32()
        db.session.commit()

    # Generate provisioning URI for QR code
    totp = pyotp.TOTP(current_user.mfa_secret)
    provisioning_uri = totp.provisioning_uri(name=current_user.username, issuer_name="StepManiaX B2B")

    return render_template('mfa_setup.html', secret=current_user.mfa_secret, uri=provisioning_uri)

@auth_bp.route('/mfa/qr')
@login_required
def mfa_qr():
    if not current_user.mfa_secret:
        abort(404)

    totp = pyotp.TOTP(current_user.mfa_secret)
    uri = totp.provisioning_uri(name=current_user.username, issuer_name="StepManiaX B2B")

    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@auth_bp.route('/mfa/verify', methods=['POST'])
@login_required
def mfa_verify():
    token = request.form.get('token')
    totp = pyotp.TOTP(current_user.mfa_secret)

    if totp.verify(token):
        current_user.mfa_enabled = True
        db.session.commit()
        log_security_event(current_user.id, "MFA enabled successfully")
        flash("Multi-Factor Authentication enabled!")
    else:
        flash("Invalid token. MFA setup failed.")

    return redirect(url_for('auth.settings'))

@auth_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Franchisee', 'Staff', 'Member'])
def settings():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'change_password':
            current_pw = request.form.get('current_password')
            new_pw = request.form.get('new_password')
            confirm_pw = request.form.get('confirm_password')

            if not current_user.check_password(current_pw):
                flash("Current password incorrect.")
            elif new_pw != confirm_pw:
                flash("New passwords do not match.")
            else:
                is_valid, msg = is_password_complex(new_pw)
                if not is_valid:
                    flash(msg)
                else:
                    current_user.set_password(new_pw)
                    db.session.commit()
                    log_security_event(current_user.id, "Password changed successfully")
                    flash("Password updated successfully!")
            return redirect(url_for('auth.settings'))

        if action == 'add_webhook':
            url = request.form.get('url')
            service = request.form.get('service')
            new_hook = Webhook(
                url=url,
                service=service,
                franchise_id=current_user.franchise_id if current_user.role != 'Admin' else None
            )
            db.session.add(new_hook)
            db.session.commit()
            flash(f"Webhook added successfully for {service}")

        elif action == 'create_user' and current_user.role == 'Admin':
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')
            franchise_id = request.form.get('franchise_id')

            if User.query.filter_by(username=username).first():
                flash("User already exists.")
            else:
                new_user = User(username=username, role=role, franchise_id=franchise_id if franchise_id else None)
                new_user.set_password(password)
                new_user.api_key = secrets.token_urlsafe(32)
                db.session.add(new_user)
                db.session.commit()
                flash(f"User {username} created successfully as {role}.")

        elif action == 'rotate_api_key':
            current_user.api_key = secrets.token_urlsafe(32)
            db.session.commit()
            log_security_event(current_user.id, "API key rotated")
            flash("New API Key generated.")

        elif action == 'update_hardware_tokens':
            member = Member.query.filter_by(user_id=current_user.id).first()
            if member:
                member.nfc_uid = request.form.get('nfc_uid')
                member.biometric_token = request.form.get('biometric_token')
                db.session.commit()
                log_security_event(current_user.id, "Hardware check-in tokens updated")
                flash("Hardware tokens updated successfully.")

        return redirect(url_for('auth.settings'))

    search_query = request.args.get('q', '')

    if current_user.role == 'Admin':
        webhooks = Webhook.query.all()
        users = User.query.all()
        audit_base = AuditLog.query
        if search_query:
            audit_base = audit_base.filter(AuditLog.action.contains(search_query))
        audit_logs = audit_base.order_by(AuditLog.timestamp.desc()).limit(50).all()
    else:
        webhooks = Webhook.query.filter_by(franchise_id=current_user.franchise_id).all()
        users = []
        audit_logs = AuditLog.query.filter_by(user_id=current_user.id).order_by(AuditLog.timestamp.desc()).limit(10).all()

    return render_template('settings.html', webhooks=webhooks, users=users, audit_logs=audit_logs)
