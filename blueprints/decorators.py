from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user, login_manager

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                if current_user.role == 'Member':
                    flash("Access restricted to management only.")
                    return redirect(url_for('member.member_dashboard'))
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def permission_required(permission_attr):
    """Granular permission check (v4.0.0)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))

            # Admins bypass granular checks
            if current_user.role == 'Admin':
                return f(*args, **kwargs)

            if not getattr(current_user, permission_attr, False):
                flash(f"Insufficient permissions: {permission_attr.replace('perm_', '').replace('_', ' ').title()}")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_api_or_role(roles):
    """Advanced decorator for v3.9.2 that handles API-Key (Global scope) or Role-Based session access."""
    from flask import request
    from models import User
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 1. Check for valid API Key (provides Global scope)
            api_key = request.headers.get('X-API-KEY') or request.args.get('api_key')
            if api_key:
                user = User.query.filter_by(api_key=api_key).first()
                if user:
                    # Optional: Set current_user or scope based on user
                    return f(*args, **kwargs)

            # 2. Check for Authenticated Session
            if not current_user.is_authenticated:
                return {"error": "Authentication required. API-KEY or Session."}, 401

            # 3. Check Role restrictions
            if current_user.role not in roles:
                return {"error": "Insufficient permissions for this resource."}, 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_api_key(f):
    """Simple API Key or Session check for public/semi-public APIs."""
    from flask import request
    from models import User
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY') or request.args.get('api_key')
        if api_key:
            user = User.query.filter_by(api_key=api_key).first()
            if user:
                return f(*args, **kwargs)

        if current_user and current_user.is_authenticated:
            return f(*args, **kwargs)
        return {"error": "Unauthorized access. API-KEY or Session required."}, 401
    return decorated_function
