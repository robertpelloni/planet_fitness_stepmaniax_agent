import os
import secrets
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash
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

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(24))

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

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(staff_bp)
app.register_blueprint(member_bp)
app.register_blueprint(api_bp)

@app.route('/')
@login_required
def index():
    if current_user.role == 'Member':
        return redirect(url_for('member.member_dashboard'))
    elif current_user.role == 'Staff':
        return redirect(url_for('staff.staff_dashboard'))
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main Franchisee/Admin Dashboard (v4.3.0)"""
    if current_user.role not in ['Admin', 'Franchisee']:
        if current_user.role == 'Member':
            return redirect(url_for('member.member_dashboard'))
        return redirect(url_for('staff.staff_dashboard'))

    franchise_id = current_user.franchise_id
    is_admin = (current_user.role == 'Admin')

    if is_admin:
        crm_stats = db.session.query(Lead.status, db.func.count(Lead.id).label('count')).group_by(Lead.status).all()
        metrics = EquipmentMetric.query.all()
        onboarding_stats = db.session.query(Member.onboarding_status, db.func.count(Member.id)).group_by(Member.onboarding_status).all()
        leads_list = Lead.query.all()
    else:
        crm_stats = db.session.query(Lead.status, db.func.count(Lead.id).label('count')).filter_by(id=franchise_id).group_by(Lead.status).all()
        metrics = EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()
        onboarding_stats = db.session.query(Member.onboarding_status, db.func.count(Member.id)).filter_by(franchise_id=franchise_id).group_by(Member.onboarding_status).all()
        leads_list = Lead.query.filter_by(id=franchise_id).all()

    metric_ids = [m.id for m in metrics]

    if is_admin:
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
            'avg_feedback_rating': avg_feedback
        }
        lead.propensity_score = analytics.calculate_propensity_score(lead_dict)

    if updated:
        db.session.commit()

    if is_admin:
        leads_list.sort(key=lambda x: x.propensity_score, reverse=True)

    franchise_name = "Global Admin"
    if not is_admin and leads_list:
        franchise_name = leads_list[0].company

    return render_template('dashboard.html',
                           crm_stats=crm_stats,
                           metrics=metrics,
                           alerts=alerts,
                           schedules=schedules,
                           leads_list=leads_list,
                           onboarding_stats=onboarding_dict,
                           is_admin=is_admin,
                           franchise_name=franchise_name)

@app.cli.command("init-db")
def init_db():
    db.create_all()
    print(f"Database tables created in {db_path}.")

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, port=5000)
