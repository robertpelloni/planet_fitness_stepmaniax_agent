import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from models import db, User, EquipmentMetric, Alert, MemberSchedule
import sqlite3

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
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
@login_required
def index():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # 1. Fetch CRM Summary using standard connection for performance
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT status, count(*) as count FROM leads GROUP BY status")
    crm_stats = cursor.fetchall()

    # 2. Fetch Equipment Metrics using SQLAlchemy
    metrics = EquipmentMetric.query.all()

    # 3. Fetch Alerts
    alerts = Alert.query.filter_by(is_resolved=False).order_by(Alert.timestamp.desc()).all()

    # 4. Fetch Schedules
    schedules = MemberSchedule.query.order_by(MemberSchedule.start_time.asc()).all()

    return render_template('dashboard.html',
                           crm_stats=crm_stats,
                           metrics=metrics,
                           alerts=alerts,
                           schedules=schedules)

# Database Initialization Command
@app.cli.command("init-db")
def init_db():
    db.create_all()
    print(f"Database tables created in {db_path}.")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
