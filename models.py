from datetime import datetime
from flask_login import UserMixin
from app import db

# Association table for many-to-many relationship between doctors and diseases
doctor_diseases = db.Table('doctor_diseases',
    db.Column('doctor_id', db.Integer, db.ForeignKey('doctor.id'), primary_key=True),
    db.Column('disease_id', db.Integer, db.ForeignKey('disease.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    submissions = db.relationship('Submission', backref='user', lazy=True, cascade='all, delete-orphan')

class Disease(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    forms = db.relationship('Form', backref='disease', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('Submission', backref='disease', lazy=True)
    doctors = db.relationship('Doctor', secondary=doctor_diseases, back_populates='diseases')

class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    doctors = db.relationship('Doctor', backref='hospital', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('Submission', backref='hospital', lazy=True)

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100))
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    diseases = db.relationship('Disease', secondary=doctor_diseases, back_populates='doctors')
    submissions = db.relationship('Submission', backref='doctor', lazy=True)

class Form(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    disease_id = db.Column(db.Integer, db.ForeignKey('disease.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    fields = db.relationship('FormField', backref='form', lazy=True, cascade='all, delete-orphan', order_by='FormField.order')
    submissions = db.relationship('Submission', backref='form', lazy=True)

class FormField(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('form.id'), nullable=False)
    field_name = db.Column(db.String(100), nullable=False)
    field_type = db.Column(db.String(50), nullable=False)  # text, textarea, number, date, select, checkbox, radio
    field_label = db.Column(db.String(200), nullable=False)
    is_required = db.Column(db.Boolean, default=False)
    options = db.Column(db.Text)  # JSON string for select/radio/checkbox options
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    form_id = db.Column(db.Integer, db.ForeignKey('form.id'), nullable=False)
    disease_id = db.Column(db.Integer, db.ForeignKey('disease.id'), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    data = db.Column(db.Text, nullable=False)  # JSON string of form data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
