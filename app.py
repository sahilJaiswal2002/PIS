from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///iitb_scan.db').replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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
