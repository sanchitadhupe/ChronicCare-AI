"""
Main Flask Application - Chronic Disease Monitoring
IBM watsonx.ai powered with IBM Granite Foundation Models
"""
import os
import json
import uuid
import logging
from datetime import datetime, timedelta, date

from flask import (
    Flask, render_template, redirect, url_for, flash,
    request, jsonify, abort
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from dotenv import load_dotenv
from flask_wtf.csrf import generate_csrf

from models import db, bcrypt, User, PatientProfile, HealthRecord, Medication, MedicalReport
from forms import (
    RegisterForm, LoginForm, PatientProfileForm,
    HealthRecordForm, MedicationForm, MedicalReportUploadForm
)
# ─────────────────────────────────────────────────────────────────────────────
# App Configuration
# ─────────────────────────────────────────────────────────────────────────────

# Always resolve paths relative to this file, not the working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load .env from the same folder as app.py
load_dotenv(os.path.join(BASE_DIR, '.env'))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    # Ensure instance directory exists before anything else touches the DB
    instance_dir = os.path.join(BASE_DIR, 'instance')
    os.makedirs(instance_dir, exist_ok=True)

    app = Flask(
        __name__,
        instance_path=instance_dir,
        template_folder=os.path.join(BASE_DIR, 'templates'),
        static_folder=os.path.join(BASE_DIR, 'static'),
    )

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    # Fix Render's legacy "postgres://" scheme — SQLAlchemy 2.x requires "postgresql://"
    raw_db_url = os.getenv('DATABASE_URL', '')
    if not raw_db_url or raw_db_url.startswith('sqlite:///') and not os.path.isabs(raw_db_url.replace('sqlite:///', '')):
        # Use an absolute path so SQLite can always write the file
        db_url = 'sqlite:///' + os.path.join(instance_dir, 'chronic_disease.db')
    elif raw_db_url.startswith('postgres://'):
        db_url = raw_db_url.replace('postgres://', 'postgresql://', 1)
    else:
        db_url = raw_db_url
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please sign in to access the dashboard.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Create tables (checkfirst avoids errors on existing tables)
    with app.app_context():
        db.create_all()
        # Flask-SQLAlchemy 3.x uses checkfirst by default

    # Custom Jinja2 filters
    @app.template_filter('from_json')
    def from_json_filter(value):
        if not value:
            return []
        try:
            return json.loads(value)
        except Exception:
            return []

    # Inject CSRF token and timestamp into every template
    @app.context_processor
    def inject_globals():
        return {
            'now': datetime.utcnow(),
            'current_year': datetime.utcnow().year,
            'csrf_token': generate_csrf,
        }

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
