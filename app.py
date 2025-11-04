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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        from models import User
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
    
    app.run(host='0.0.0.0', port=5000, debug=True)
