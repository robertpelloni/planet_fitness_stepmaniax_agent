import os
import secrets
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory, abort
from flask_login import LoginManager, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from extensions import db, limiter

from models import User, Lead, Member, EquipmentMetric, Alert, MemberSchedule, Feedback
import analytics

app = Flask(__name__)

# --- Log Rotation Setup ---
if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler('logs/server.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('StepManiaX B2B Agent Startup')

campaign_logger = logging.getLogger('campaign_launcher')
campaign_handler = RotatingFileHandler('logs/campaign_launch.log', maxBytes=10240, backupCount=10)
campaign_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
campaign_logger.addHandler(campaign_handler)
campaign_logger.setLevel(logging.INFO)

# --- Configuration ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(24))

# Security Hardening (v4.5.0)
is_prod = os.environ.get('FLASK_DEBUG', 'false').lower() == 'false'
app.config['SESSION_COOKIE_SECURE'] = is_prod
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['REMEMBER_COOKIE_SECURE'] = is_prod
app.config['REMEMBER_COOKIE_HTTPONLY'] = True

project_root = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(project_root, 'crm.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Extensions Initialization ---
db.init_app(app)
csrf = CSRFProtect(app)
limiter.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.context_processor
def inject_utils():
    def user_is_locked(user_id):
        u = db.session.get(User, user_id)
        return u.is_locked if u else False
    return dict(user_is_locked=user_is_locked)

# --- Blueprints ---
from blueprints.auth import auth_bp
from blueprints.admin import admin_bp
from blueprints.staff import staff_bp
from blueprints.member import member_bp
from blueprints.api import api_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(staff_bp, url_prefix='/staff')
app.register_blueprint(member_bp, url_prefix='/member')
app.register_blueprint(api_bp, url_prefix='/api')

csrf.exempt(api_bp)

# --- Routes ---
@app.route('/')
@login_required
def index():
    if current_user.role == 'Member':
        return redirect(url_for('member.member_dashboard'))
    elif current_user.role == 'Staff':
        return redirect(url_for('staff.staff_dashboard'))
    elif current_user.role == 'Admin' or current_user.role == 'Franchisee':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Redirect legacy dashboard to namespaced dashboard."""
    return redirect(url_for('index'))

@app.route('/prospect/<token>')
def prospect_portal(token):
    """Namespaced landing page alias for external discovery."""
    return redirect(url_for('admin.prospect_portal', token=token))

@app.route('/resources/<path:filename>')
@login_required
def serve_resources(filename):
    return redirect(url_for('admin.serve_resources', filename=filename))

@app.cli.command("init-db")
def init_db():
    db.create_all()
    print(f"Database tables created in {db_path}.")

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, port=5000)
