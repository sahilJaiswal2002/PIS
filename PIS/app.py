from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
import secrets
import string

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
        from models import User
        from werkzeug.security import generate_password_hash
        
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin_password = os.environ.get('ADMIN_PASSWORD')
            if not admin_password:
                alphabet = string.ascii_letters + string.digits + string.punctuation
                admin_password = ''.join(secrets.choice(alphabet) for _ in range(20))
                print("=" * 80)
                print("IMPORTANT: Auto-generated admin password (save this securely!):")
                print(f"  Username: admin")
                print(f"  Password: {admin_password}")
                print("=" * 80)
                print("Set the ADMIN_PASSWORD environment variable to use a custom password.")
                print("=" * 80)
            
            admin = User(
                username='admin',
                email='admin@iitb.ac.in',
                password=generate_password_hash(admin_password),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
    
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
