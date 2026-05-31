from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime

db = SQLAlchemy()

def log_security_event(user_id, action):
    """
    Centralized helper for logging security events into AuditLog.
    (v5.9.1): Standardized across all blueprints.
    """
    from flask import request
    from models import AuditLog
    log = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=request.remote_addr,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.session.add(log)
    db.session.commit()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)
