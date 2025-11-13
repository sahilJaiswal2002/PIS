from app import app, db
from models import *  # noqa: F401,F403

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Database tables created.")


