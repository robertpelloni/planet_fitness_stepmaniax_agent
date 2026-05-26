import os
import secrets
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
from flask_login import LoginManager, login_required, current_user
from flask_wtf.csrf import CSRFProtect

from models import db, User, Lead, Member, EquipmentMetric, Alert, MemberSchedule, Feedback
import analytics

# Import Blueprints
from blueprints.auth import auth_bp
from blueprints.admin import admin_bp
from blueprints.staff import staff_bp
from blueprints.member import member_bp
from blueprints.api import api_bp
from blueprints.decorators import permission_required

app = Flask(__name__)
# Secret key should be loaded from environment for production
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')
# Use absolute path to project root DB for consistency
project_root = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(project_root, 'crm.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_utils():
    def user_is_locked(user_id):
        u = User.query.get(user_id)
        return u.is_locked if u else False
    return dict(user_is_locked=user_is_locked)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(staff_bp, url_prefix='/staff')
app.register_blueprint(member_bp, url_prefix='/member')
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/')
@login_required
def index():
    if current_user.role == 'Admin':
        return redirect(url_for('admin.dashboard'))
    elif current_user.role == 'Staff':
        return redirect(url_for('staff.staff_dashboard'))
    elif current_user.role == 'Member':
        return redirect(url_for('member.member_dashboard'))
    elif current_user.role == 'Franchisee':
         return redirect(url_for('staff.manager_dashboard'))
    return redirect(url_for('admin.dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Deprecated main route; redirect to specific dashboards based on role
    if current_user.role == 'Admin':
        return redirect(url_for('admin.dashboard'))
    elif current_user.role == 'Staff':
        return redirect(url_for('staff.staff_dashboard'))
    elif current_user.role == 'Member':
        return redirect(url_for('member.member_dashboard'))
    elif current_user.role == 'Franchisee':
         return redirect(url_for('staff.manager_dashboard'))
    return redirect(url_for('admin.dashboard'))

@app.route('/prospect/<token>')
def prospect_portal(token):
    """
    Public but secure landing page for prospective franchise partners.
    """
    lead = Lead.query.filter_by(public_token=token).first_or_404()

    # Increment view counter
    if lead.portal_views is None: lead.portal_views = 0
    lead.portal_views += 1
    db.session.commit()

    # Calculate personalized metrics
    metrics = analytics.calculate_detailed_metrics(
        num_clubs=lead.num_clubs,
        retention_lift_percent=lead.retention_lift,
        avg_monthly_fee=lead.avg_monthly_fee
    )

    return render_template('prospect_portal.html', lead=lead, metrics=metrics)

# Database Initialization Command
@app.cli.command("init-db")
def init_db():
    db.create_all()
    print(f"Database tables created in {db_path}.")

if __name__ == '__main__':
    # Default to production-safe settings; use environment for debug
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, port=5000)
