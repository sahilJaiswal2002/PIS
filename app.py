from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=False)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')

# Ensure instance and upload folders exist
Path(app.instance_path).mkdir(parents=True, exist_ok=True)

def _compute_database_url() -> str:
    """Return a normalized SQLAlchemy URL with sensible defaults.
    - Default: MySQL on localhost (DB: pis, user: root, pass: admin)
    - Normalize legacy postgres:// to postgresql://
    """
    default_mysql_url = "mysql+pymysql://root:admin@localhost:3306/pis"
    url = os.environ.get('DATABASE_URL', default_mysql_url)
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url

app.config['SQLALCHEMY_DATABASE_URI'] = _compute_database_url()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 280,
}
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'static/uploads')

# Ensure upload directory exists
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
"""The global SQLAlchemy database handle used across the app."""
migrate = Migrate(app, db)
"""Flask-Migrate binder for Alembic migrations."""
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Enable CSRF protection
csrf = CSRFProtect(app)

# Basic production logging (Gunicorn will also configure handlers)
if os.environ.get('LOG_LEVEL'):
    logging.basicConfig(level=getattr(logging, os.environ['LOG_LEVEL'].upper(), logging.INFO))

# Import routes after app initialization
from routes import *
from admin_routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Create default admin user if not exists
        from models import User, SecurityQuestion
        from werkzeug.security import generate_password_hash

        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@iitb.ac.in',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created: username='admin', password='admin123'")

        # Create default security questions if not exists
        if SecurityQuestion.query.count() == 0:
            default_questions = [
                "What is your mother's maiden name?",
                "What was the name of your first pet?",
                "In what city were you born?",
                "What is the name of the school you attended in kindergarten?",
                "What was the make and model of your first car?",
                "What is your favorite book?",
                "What was your childhood phone number?",
                "What is the name of the street you grew up on?",
                "What is your favorite sports team?",
                "What is your all-time favorite movie?",
            ]

            for question_text in default_questions:
                question = SecurityQuestion(question=question_text)
                db.session.add(question)

            db.session.commit()
            print(f"Created {len(default_questions)} default security questions")

    app.run(host='0.0.0.0', port=5000, debug=True)
