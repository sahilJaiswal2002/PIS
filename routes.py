from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import uuid
from werkzeug.utils import secure_filename
import json
import io
import secrets
from datetime import datetime, timedelta
from app import app, db, login_manager
from models import (
    User, Disease, Hospital, Doctor, Form, FormField, Submission, DraftSubmission,
    SecurityQuestion, UserSecurityQuestion, PasswordResetToken
)
from forms import LoginForm
from export_utils import generate_submission_pdf, generate_submissions_csv, generate_submissions_excel, generate_detailed_submissions_excel, generate_detailed_submissions_csv

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            app.logger.warning('User not authenticated, redirecting to login')
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
            
        if not current_user.is_admin:
            app.logger.warning(f'User {current_user.username} (ID: {current_user.id}) is not an admin')
            app.logger.warning(f'User admin status: {current_user.is_admin}')
            flash('You need admin privileges to access this page.', 'error')
            return redirect(url_for('index'))
            
        app.logger.info(f'Admin access granted to {current_user.username} (ID: {current_user.id})')
        return f(*args, **kwargs)
    return decorated_function

# Authentication Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    # Check for dev parameter
    if request.args.get('dev') == '1':
        try:
            admin = User.query.filter_by(username='admin', is_admin=True).first()
            if admin:
                login_user(admin)
                return redirect(url_for('admin_dashboard'))
        except:
            pass
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')

        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('setup_security_questions', user_id=user.id))

    return render_template('register.html')

@app.route('/setup-security-questions/<int:user_id>', methods=['GET', 'POST'])
def setup_security_questions(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        security_questions = SecurityQuestion.query.all()

        if not security_questions:
            flash('No security questions available. Please try again later.', 'error')
            return render_template('register.html')

        for q in security_questions[:3]:
            answer = request.form.get(f'answer_{q.id}', '').strip()
            if answer:
                usq = UserSecurityQuestion(
                    user_id=user.id,
                    question_id=q.id,
                    answer=answer
                )
                db.session.add(usq)

        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    security_questions = SecurityQuestion.query.all()

    if not security_questions:
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('setup_security_questions.html',
                         user=user,
                         security_questions=security_questions[:3])

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()

        if not user:
            flash('Username not found', 'error')
            return render_template('forgot_password.html')

        security_questions = user.security_questions
        if not security_questions:
            flash('No security questions set up for this account. Please contact support.', 'error')
            return render_template('forgot_password.html')

        # Create a reset token
        token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.session.add(reset_token)
        db.session.commit()

        return redirect(url_for('answer_security_questions', token=token))

    return render_template('forgot_password.html')

@app.route('/answer-security-questions/<token>', methods=['GET', 'POST'])
def answer_security_questions(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    reset_token = PasswordResetToken.query.filter_by(token=token).first_or_404()

    if reset_token.expires_at < datetime.utcnow():
        flash('Password reset token has expired', 'error')
        return redirect(url_for('forgot_password'))

    if reset_token.is_verified:
        return redirect(url_for('reset_password', token=token))

    user = reset_token.user
    security_questions = user.security_questions

    if request.method == 'POST':
        all_correct = True
        for sq in security_questions:
            answer = request.form.get(f'answer_{sq.id}', '').strip().lower()
            if answer != sq.answer.lower():
                all_correct = False
                break

        if all_correct:
            reset_token.is_verified = True
            db.session.commit()
            return redirect(url_for('reset_password', token=token))
        else:
            flash('Incorrect answers. Please try again.', 'error')

    return render_template('answer_security_questions.html',
                         security_questions=security_questions,
                         token=token)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    reset_token = PasswordResetToken.query.filter_by(token=token).first_or_404()

    if not reset_token.is_verified:
        flash('Please verify your security questions first', 'error')
        return redirect(url_for('answer_security_questions', token=token))

    if reset_token.expires_at < datetime.utcnow():
        flash('Password reset token has expired', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('reset_password.html', token=token)

        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('reset_password.html', token=token)

        user = reset_token.user
        user.password = generate_password_hash(password)
        db.session.delete(reset_token)
        db.session.commit()

        flash('Password reset successful! Please login with your new password.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Setup endpoint to initialize admin user and test database"""
    if request.method == 'POST':
        try:
            # Delete all users and recreate admin
            User.query.delete()
            db.session.commit()

            admin = User(
                username='admin',
                email='admin@iitb.ac.in',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()

            return jsonify({'status': 'success', 'message': 'Admin user created successfully', 'username': 'admin', 'password': 'admin123'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500

    # GET request - check admin user exists
    try:
        admin = User.query.filter_by(username='admin').first()
        if admin:
            return jsonify({'status': 'ok', 'message': 'Admin user exists', 'admin_id': admin.id})
        else:
            return jsonify({'status': 'not_found', 'message': 'Admin user not found. POST to create.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dev-login')
def dev_login():
    """Direct login for development - logs in as admin"""
    try:
        admin = User.query.filter_by(username='admin', is_admin=True).first()
        if admin:
            login_user(admin)
            return redirect(url_for('admin_dashboard'))
        else:
            # Create admin if doesn't exist
            admin = User(
                username='admin',
                email='admin@iitb.ac.in',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            login_user(admin)
            return redirect(url_for('admin_dashboard'))
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Admin Routes
@app.route('/admin')
@app.route('/admin/dashboard')
def admin_dashboard():
    # Allow access for development - check authentication
    if not current_user.is_authenticated or not current_user.is_admin:
        # For dev: check if ?dev=1 parameter is passed
        if request.args.get('dev') != '1':
            flash('You need admin privileges to access this page.', 'error')
            return redirect(url_for('index'))

    try:
        disease_count = Disease.query.count()
        hospital_count = Hospital.query.count()
        doctor_count = Doctor.query.count()
        form_count = Form.query.count()
        submission_count = Submission.query.count()
    except:
        # Database initialization error - show zero counts
        disease_count = 0
        hospital_count = 0
        doctor_count = 0
        form_count = 0
        submission_count = 0

    return render_template('admin/dashboard.html',
                         disease_count=disease_count,
                         hospital_count=hospital_count,
                         doctor_count=doctor_count,
                         form_count=form_count,
                         submission_count=submission_count)

@app.route('/admin/diseases')
@login_required
@admin_required
def admin_diseases():
    diseases = Disease.query.all()
    return render_template('admin/diseases.html', diseases=diseases)

@app.route('/admin/diseases/create', methods=['POST'])
@login_required
@admin_required
def create_disease():
    name = request.form.get('name')
    description = request.form.get('description', '')
    
    disease = Disease(name=name, description=description)
    db.session.add(disease)
    db.session.commit()
    
    flash('Disease created successfully', 'success')
    return redirect(url_for('admin_diseases'))

@app.route('/admin/diseases/<int:id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_disease(id):
    disease = Disease.query.get_or_404(id)
    disease.name = request.form.get('name')
    disease.description = request.form.get('description', '')
    
    db.session.commit()
    flash('Disease updated successfully', 'success')
    return redirect(url_for('admin_diseases'))

@app.route('/admin/diseases/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_disease(id):
    disease = Disease.query.get_or_404(id)
    db.session.delete(disease)
    db.session.commit()
    
    flash('Disease deleted successfully', 'success')
    return redirect(url_for('admin_diseases'))

@app.route('/admin/hospitals')
@login_required
@admin_required
def admin_hospitals():
    hospitals = Hospital.query.all()
    return render_template('admin/hospitals.html', hospitals=hospitals)

@app.route('/admin/hospitals/create', methods=['POST'])
@login_required
@admin_required
def create_hospital():
    name = request.form.get('name')
    address = request.form.get('address', '')
    phone = request.form.get('phone', '')
    
    hospital = Hospital(name=name, address=address, phone=phone)
    db.session.add(hospital)
    db.session.commit()
    
    flash('Hospital created successfully', 'success')
    return redirect(url_for('admin_hospitals'))

@app.route('/admin/hospitals/<int:id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_hospital(id):
    hospital = Hospital.query.get_or_404(id)
    hospital.name = request.form.get('name')
    hospital.address = request.form.get('address', '')
    hospital.phone = request.form.get('phone', '')
    
    db.session.commit()
    flash('Hospital updated successfully', 'success')
    return redirect(url_for('admin_hospitals'))

@app.route('/admin/hospitals/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_hospital(id):
    hospital = Hospital.query.get_or_404(id)
    db.session.delete(hospital)
    db.session.commit()
    
    flash('Hospital deleted successfully', 'success')
    return redirect(url_for('admin_hospitals'))

@app.route('/admin/doctors')
@login_required
@admin_required
def admin_doctors():
    doctors = Doctor.query.all()
    hospitals = Hospital.query.all()
    diseases = Disease.query.all()
    return render_template('admin/doctors.html', doctors=doctors, hospitals=hospitals, diseases=diseases)

@app.route('/admin/doctors/create', methods=['POST'])
@login_required
@admin_required
def create_doctor():
    name = request.form.get('name')
    specialization = request.form.get('specialization', '')
    hospital_id = request.form.get('hospital_id')
    disease_ids = request.form.getlist('disease_ids')
    
    doctor = Doctor(name=name, specialization=specialization, hospital_id=hospital_id)
    
    for disease_id in disease_ids:
        disease = Disease.query.get(disease_id)
        if disease:
            doctor.diseases.append(disease)
    
    db.session.add(doctor)
    db.session.commit()
    
    flash('Doctor created successfully', 'success')
    return redirect(url_for('admin_doctors'))

@app.route('/admin/doctors/<int:id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_doctor(id):
    doctor = Doctor.query.get_or_404(id)
    doctor.name = request.form.get('name')
    doctor.specialization = request.form.get('specialization', '')
    doctor.hospital_id = request.form.get('hospital_id')
    
    disease_ids = request.form.getlist('disease_ids')
    doctor.diseases = []
    for disease_id in disease_ids:
        disease = Disease.query.get(disease_id)
        if disease:
            doctor.diseases.append(disease)
    
    db.session.commit()
    flash('Doctor updated successfully', 'success')
    return redirect(url_for('admin_doctors'))

@app.route('/admin/doctors/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_doctor(id):
    doctor = Doctor.query.get_or_404(id)
    db.session.delete(doctor)
    db.session.commit()
    
    flash('Doctor deleted successfully', 'success')
    return redirect(url_for('admin_doctors'))

@app.route('/admin/forms')
@login_required
@admin_required
def admin_forms():
    forms = Form.query.all()
    diseases = Disease.query.all()
    return render_template('admin/forms.html', forms=forms, diseases=diseases)

@app.route('/admin/forms/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_form():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        disease_id = request.form.get('disease_id')
        fields_json = request.form.get('fields')
        
        form = Form(name=name, description=description, disease_id=disease_id)
        db.session.add(form)
        db.session.flush()
        
        if fields_json:
            fields = json.loads(fields_json)
            for idx, field in enumerate(fields):
                form_field = FormField(
                    form_id=form.id,
                    field_name=field['name'],
                    field_type=field['type'],
                    field_label=field['label'],
                    is_required=field.get('required', False),
                    options=json.dumps(field.get('options', [])) if field.get('options') else None,
                    order=idx
                )
                db.session.add(form_field)
        
        db.session.commit()
        flash('Form created successfully', 'success')
        return redirect(url_for('admin_forms'))
    
    diseases = Disease.query.all()
    return render_template('admin/form_builder.html', form=None, diseases=diseases)

@app.route('/admin/forms/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_form(id):
    form = Form.query.get_or_404(id)
    
    if request.method == 'POST':
        form.name = request.form.get('name')
        form.description = request.form.get('description', '')
        form.disease_id = request.form.get('disease_id')
        fields_json = request.form.get('fields')
        
        # Delete existing fields
        FormField.query.filter_by(form_id=form.id).delete()
        
        if fields_json:
            fields = json.loads(fields_json)
            for idx, field in enumerate(fields):
                form_field = FormField(
                    form_id=form.id,
                    field_name=field['name'],
                    field_type=field['type'],
                    field_label=field['label'],
                    is_required=field.get('required', False),
                    options=json.dumps(field.get('options', [])) if field.get('options') else None,
                    order=idx
                )
                db.session.add(form_field)
        
        db.session.commit()
        flash('Form updated successfully', 'success')
        return redirect(url_for('admin_forms'))
    
    # For GET request, render the form builder with existing form data
    diseases = Disease.query.all()
    
    # Convert form fields to a serializable format and sort by order
    serialized_fields = []
    for field in sorted(form.fields, key=lambda x: x.order):
        try:
            options = json.loads(field.options) if field.options else []
        except json.JSONDecodeError:
            options = []
            
        field_data = {
            'name': field.field_name,
            'type': field.field_type,
            'label': field.field_label,
            'required': field.is_required,
            'options': options,
            'order': field.order
        }
        serialized_fields.append(field_data)
    
    # Create a minimal serializable form dictionary
    form_data = {
        'id': form.id,
        'name': form.name,
        'description': form.description or '',
        'disease_id': form.disease_id
    }
    
    # Convert fields to JSON string for the template
    fields_json = json.dumps(serialized_fields) if serialized_fields else '[]'
    
    # Pass the form and fields data to the template
    return render_template('admin/form_builder.html', 
                         form=form_data, 
                         diseases=diseases, 
                         fields=fields_json,
                         is_edit=True)

@app.route('/admin/forms/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_form(id):
    form = Form.query.get_or_404(id)
    if request.method == 'POST':
        db.session.delete(form)
        db.session.commit()
        flash('Form deleted successfully!', 'success')
        return redirect(url_for('admin_forms'))
    return redirect(url_for('admin_forms'))

@app.route('/admin/forms/<int:id>/copy', methods=['POST'])
@login_required
@admin_required
def copy_form(id):
    try:
        # Get the original form
        original_form = Form.query.get_or_404(id)
        
        # Create a new form with similar details
        new_form = Form(
            name=f"{original_form.name} (Copy)",
            description=original_form.description,
            disease_id=original_form.disease_id,
            version=1,
            is_active=original_form.is_active
        )
        
        # Add the new form to the session
        db.session.add(new_form)
        db.session.flush()  # This will assign an ID to new_form without committing
        
        # Copy all the form fields
        for field in original_form.fields:
            new_field = FormField(
                form_id=new_form.id,
                field_name=field.field_name,
                field_type=field.field_type,
                field_label=field.field_label,
                is_required=field.is_required,
                options=field.options,
                order=field.order
            )
            db.session.add(new_field)
        
        # Create a version snapshot
        version = FormVersion(
            form_id=new_form.id,
            version_number=1,
            fields_snapshot=json.dumps([{
                'field_name': f.field_name,
                'field_type': f.field_type,
                'field_label': f.field_label,
                'is_required': f.is_required,
                'options': f.options,
                'order': f.order
            } for f in new_form.fields]),
            created_by_id=current_user.id
        )
        db.session.add(version)
        
        # Commit all changes
        db.session.commit()
        
        flash('Form copied successfully!', 'success')
        return redirect(url_for('edit_form', id=new_form.id))
        
    except Exception as e:
        db.session.rollback()
        flash('Error copying form. Please try again.', 'error')
        app.logger.error(f'Error copying form: {str(e)}')
        return redirect(url_for('admin_forms'))

@app.route('/admin/submissions')
@login_required
@admin_required
def admin_submissions():
    submissions = Submission.query.order_by(Submission.created_at.desc()).all()
    return render_template('admin/submissions.html', submissions=submissions)

@app.route('/admin/submissions/<int:id>')
@login_required
@admin_required
def view_submission(id):
    submission = Submission.query.get_or_404(id)
    try:
        submission_data = json.loads(submission.data)
    except Exception:
        submission_data = {}
    return render_template('admin/submission_detail.html', submission=submission, submission_data=submission_data)

# User Routes
@app.route('/user')
@login_required
def user_dashboard():
    submissions = Submission.query.filter_by(user_id=current_user.id).order_by(Submission.created_at.desc()).all()
    # Build lightweight previews: first 3 form fields in form-defined order
    submission_previews = {}
    for s in submissions:
        try:
            data = json.loads(s.data)
        except Exception:
            data = {}
        rows = []
        for f in s.form.fields[:3]:
            key = f"field_{f.field_name}"
            rows.append((f.field_label, data.get(key, '')))
        submission_previews[s.id] = rows
    return render_template('user/dashboard.html', submissions=submissions, submission_previews=submission_previews)

@app.route('/user/forms/search')
@login_required
def form_search():
    """Search and filter available forms"""
    search_query = request.args.get('search', '')
    disease_filter = request.args.get('disease', '')
    hospital_filter = request.args.get('hospital', '')

    query = Form.query.filter_by(is_active=True)

    if search_query:
        query = query.filter(
            (Form.name.ilike(f'%{search_query}%')) |
            (Form.disease.has(Disease.name.ilike(f'%{search_query}%')))
        )

    if disease_filter:
        query = query.filter(Form.disease.has(Disease.name == disease_filter))

    forms = query.all()

    # Filter by hospital if specified
    if hospital_filter:
        forms = [f for f in forms if any(d.hospital.name == hospital_filter for d in f.disease.doctors)]

    diseases = Disease.query.all()
    hospitals = Hospital.query.all()

    return render_template('user/form_search.html',
                         forms=forms,
                         diseases=diseases,
                         hospitals=hospitals,
                         search_query=search_query,
                         disease_filter=disease_filter,
                         hospital_filter=hospital_filter)

@app.route('/user/submit/select-disease')
@login_required
def select_disease():
    diseases = Disease.query.all()
    return render_template('user/select_disease.html', diseases=diseases)

@app.route('/user/submit/select-hospital/<int:disease_id>')
@login_required
def select_hospital(disease_id):
    disease = Disease.query.get_or_404(disease_id)
    hospitals = Hospital.query.all()
    return render_template('user/select_hospital.html', disease=disease, hospitals=hospitals)

@app.route('/user/submit/select-doctor/<int:disease_id>/<int:hospital_id>')
@login_required
def select_doctor(disease_id, hospital_id):
    disease = Disease.query.get_or_404(disease_id)
    hospital = Hospital.query.get_or_404(hospital_id)
    doctors = Doctor.query.filter_by(hospital_id=hospital_id).all()
    
    # Filter doctors by disease if they have disease specializations
    doctors_for_disease = [d for d in doctors if disease in d.diseases or not d.diseases]
    
    return render_template('user/select_doctor.html', disease=disease, hospital=hospital, doctors=doctors_for_disease)

@app.route('/user/submit/fill-form/<int:disease_id>/<int:hospital_id>/<int:doctor_id>')
@login_required
def fill_form(disease_id, hospital_id, doctor_id):
    disease = Disease.query.get_or_404(disease_id)
    hospital = Hospital.query.get_or_404(hospital_id)
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Get the form for this disease
    form = Form.query.filter_by(disease_id=disease_id).first()
    
    if not form:
        flash('No form available for this disease', 'error')
        return redirect(url_for('select_disease'))
    
    # Build options map for choice fields to avoid using fromjson in templates
    options_map = {}
    for f in form.fields:
        if f.options:
            try:
                options_map[f.id] = json.loads(f.options)
            except Exception:
                options_map[f.id] = []
        else:
            options_map[f.id] = []
    return render_template('user/fill_form.html', disease=disease, hospital=hospital, doctor=doctor, form=form, options_map=options_map)

@app.route('/user/submit/submit-form', methods=['POST'])
@login_required
def submit_form():
    disease_id = request.form.get('disease_id')
    hospital_id = request.form.get('hospital_id')
    doctor_id = request.form.get('doctor_id')
    form_id = request.form.get('form_id')
    
    # Collect form data
    form_data = {}
    # First get all field values
    for key, value in request.form.items():
        if key.startswith('field_'):
            form_data[key] = value
    
    # Handle checkboxes (they only post when checked)
    for key in request.form.keys():
        if key.startswith('field_') and key not in form_data:
            form_data[key] = ''  # Default value for unchecked checkboxes
    
    # Handle multi-select checkboxes (they have the same name)
    for key in request.form.keys():
        if key.startswith('field_') and key.endswith('[]'):
            base_key = key[:-2]  # Remove '[]' from the end
            values = request.form.getlist(key)
            form_data[base_key] = ','.join(values)

    # Determine patient name from submitted fields and form schema for folder naming
    def _slugify(text):
        s = (text or '').strip().lower()
        out = []
        for ch in s:
            if ch.isalnum():
                out.append(ch)
            elif ch in [' ', '-', '.', '_']:
                out.append('_')
        slug = ''.join(out).strip('_')
        while '__' in slug:
            slug = slug.replace('__', '_')
        return slug[:64] if slug else ''

    patient_name_value = None
    try:
        form_obj = Form.query.get(form_id)
    except Exception:
        form_obj = None
    if form_obj:
        for f in form_obj.fields:
            if f.field_type == 'file':
                continue
            fname = (f.field_name or '').lower()
            flabel = (f.field_label or '').lower()
            if fname in ['patient_name', 'name', 'full_name'] or 'name' in fname or 'name' in flabel:
                v = request.form.get(f'field_{f.field_name}')
                if v:
                    patient_name_value = v
                    break
    patient_slug = _slugify(patient_name_value) or f'user_{current_user.id}'

    # Handle uploaded files
    base_upload_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
    target_folder = os.path.join(base_upload_folder, patient_slug)
    os.makedirs(target_folder, exist_ok=True)
    for key in request.files:
        if key.startswith('field_'):
            file = request.files.get(key)
            if file and file.filename:
                filename = secure_filename(file.filename)
                unique_name = f"{patient_slug}_{uuid.uuid4().hex}_{filename}"
                save_path = os.path.join(target_folder, unique_name)
                file.save(save_path)
                # Store as web path
                web_path = '/' + save_path.replace('\\', '/').lstrip('/')
                form_data[key] = web_path
    
    submission = Submission(
        user_id=current_user.id,
        form_id=form_id,
        disease_id=disease_id,
        hospital_id=hospital_id,
        doctor_id=doctor_id,
        data=json.dumps(form_data)
    )
    
    db.session.add(submission)
    db.session.commit()
    
    flash('Form submitted successfully', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/user/submissions/<int:id>')
@login_required
def user_view_submission(id):
    submission = Submission.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    try:
        submission_data = json.loads(submission.data)
    except Exception:
        submission_data = {}
    return render_template('user/submission_detail.html', submission=submission, submission_data=submission_data)

# Per-form responses page with export options
@app.route('/admin/forms/<int:form_id>/responses', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_form_responses(form_id):
    form = Form.query.get_or_404(form_id)
    submissions = Submission.query.filter_by(form_id=form_id).order_by(Submission.created_at.desc()).all()
    if request.method == 'POST':
        fmt = request.form.get('format', 'excel')
        include_details = request.form.get('include_details') == 'on'
        if fmt == 'csv':
            from export_utils import generate_submission_pdf, generate_submissions_csv, generate_submissions_excel, generate_detailed_submissions_excel, generate_detailed_submissions_csv
            output = generate_detailed_submissions_csv(submissions) if include_details else generate_submissions_csv(submissions, include_field_data=False)
            return send_file(
                io.BytesIO(output.getvalue().encode()),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'form_{form_id}_submissions.csv'
            )
        else:
            from export_utils import generate_detailed_submissions_excel, generate_submissions_excel
            output = generate_detailed_submissions_excel(submissions) if include_details else generate_submissions_excel(submissions, include_field_data=False)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'form_{form_id}_submissions.xlsx'
            )
    return render_template('admin/form_responses.html', form=form, submissions=submissions)

from sqlalchemy import text

@app.route('/debug/hospitals')
@login_required
@admin_required
def debug_hospitals():
    try:
        # Try to get hospitals using ORM
        hospitals_orm = Hospital.query.order_by(Hospital.name).all()
        app.logger.info(f'Found {len(hospitals_orm)} hospitals using ORM')
        
        # Try to get hospitals using raw SQL with text()
        # First try with 'hospital' (singular)
        try:
            result = db.session.execute(text('SELECT id, name FROM hospital ORDER BY name'))
            hospitals_sql = result.fetchall()
            table_name = 'hospital'
        except Exception as e:
            # If that fails, try 'hospitals' (plural)
            try:
                result = db.session.execute(text('SELECT id, name FROM hospitals ORDER BY name'))
                hospitals_sql = result.fetchall()
                table_name = 'hospitals'
            except Exception as e2:
                hospitals_sql = []
                table_name = 'unknown'
                app.logger.warning(f'Could not find hospital table: {str(e2)}')
        
        # Get table names for debugging (MySQL version)
        try:
            tables = db.session.execute(text("SHOW TABLES")).fetchall()
            # MySQL returns tuples like [('table1',), ('table2',)]
            table_names = [t[0] for t in tables]
        except Exception as e:
            table_names = []
            app.logger.warning(f'Could not list tables: {str(e)}')
        
        app.logger.info(f'Found {len(hospitals_sql)} hospitals in {table_name} table')
        
        # Return the results
        return jsonify({
            'tables': table_names,
            'hospital_table_found': table_name in table_names,
            'hospital_table_used': table_name,
            'hospitals': [{'id': h[0], 'name': h[1]} for h in hospitals_sql] if hospitals_sql else []
        })
    except Exception as e:
        app.logger.error(f'Error in debug_hospitals: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/admin/export-forms')
@login_required
@admin_required
def export_forms():
    try:
        # Get all hospitals, diseases, and doctors for filter dropdowns
        hospitals = Hospital.query.order_by(Hospital.name).all()
        diseases = Disease.query.order_by(Disease.name).all()
        doctors = Doctor.query.order_by(Doctor.name).all()
        
        # Get the list of forms with submission counts and related data
        forms_data = db.session.query(
            Form,
            Disease.name.label('disease_name'),
            Hospital.name.label('hospital_name'),
            Doctor.name.label('doctor_name'),
            db.func.count(Submission.id).label('submission_count')
        ).outerjoin(Submission, Form.id == Submission.form_id)\
         .outerjoin(Disease, Form.disease_id == Disease.id)\
         .outerjoin(Hospital, Form.hospital_id == Hospital.id)\
         .outerjoin(Doctor, Form.doctor_id == Doctor.id)\
         .group_by(Form.id, Disease.name, Hospital.name, Doctor.name)\
         .order_by(Form.name)\
         .all()
             
        # Process the forms data
        forms = []
        for form_data in forms_data:
            form = {
                'id': form_data[0].id,
                'name': form_data[0].name,
                'disease_name': form_data[1] or 'N/A',
                'hospital_name': form_data[2] or 'N/A',
                'doctor_name': form_data[3] or 'N/A',
                'submission_count': form_data[4] or 0
            }
            forms.append(form)
        
        # Get filter parameters
        filters = {
            'form_id': request.args.get('form_id'),
            'hospital_id': request.args.get('hospital_id'),
            'disease_id': request.args.get('disease_id'),
            'doctor_id': request.args.get('doctor_id'),
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date')
        }
        
        # Build base query for submissions
        query = db.session.query(
            Submission, Form, User, Hospital, Disease, Doctor
        ).join(Form, Submission.form_id == Form.id)\
         .join(User, Submission.user_id == User.id)\
         .outerjoin(Hospital, Submission.hospital_id == Hospital.id)\
         .outerjoin(Disease, Submission.disease_id == Disease.id)\
         .outerjoin(Doctor, Submission.doctor_id == Doctor.id)
        
        # Apply filters
        if filters['form_id'] and filters['form_id'] != 'all':
            query = query.filter(Submission.form_id == filters['form_id'])
        if filters['hospital_id'] and filters['hospital_id'] != 'all':
            query = query.filter(Submission.hospital_id == filters['hospital_id'])
        if filters['disease_id'] and filters['disease_id'] != 'all':
            query = query.filter(Submission.disease_id == filters['disease_id'])
        if filters['doctor_id'] and filters['doctor_id'] != 'all':
            query = query.filter(Submission.doctor_id == filters['doctor_id'])
        if filters['start_date']:
            try:
                start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d')
                query = query.filter(Submission.created_at >= start_date)
            except ValueError:
                pass
        if filters['end_date']:
            try:
                end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d')
                end_date = end_date.replace(hour=23, minute=59, second=59)
                query = query.filter(Submission.created_at <= end_date)
            except ValueError:
                pass
        
        # Get filtered submissions
        submissions_data = query.order_by(Submission.created_at.desc()).limit(100).all()
        
        # Process submissions for the template
        submissions = []
        for sub_data in submissions_data:
            submission = {
                'id': sub_data[0].id,
                'form': {
                    'id': sub_data[1].id,
                    'name': sub_data[1].name
                },
                'user': {
                    'id': sub_data[2].id,
                    'username': sub_data[2].username
                },
                'hospital': {
                    'id': sub_data[3].id if sub_data[3] else None,
                    'name': sub_data[3].name if sub_data[3] else 'N/A'
                },
                'disease': {
                    'id': sub_data[4].id if sub_data[4] else None,
                    'name': sub_data[4].name if sub_data[4] else 'N/A'
                },
                'doctor': {
                    'id': sub_data[5].id if sub_data[5] else None,
                    'name': sub_data[5].name if sub_data[5] else 'N/A'
                },
                'created_at': sub_data[0].created_at,
                'status': sub_data[0].status
            }
            submissions.append(submission)
        
        return render_template('admin/export_forms.html',
                           forms=forms,
                           hospitals=hospitals,
                           diseases=diseases,
                           doctors=doctors,
                           submissions=submissions,
                           current_filters=filters)
                           
    except Exception as e:
        app.logger.error(f'Error in export_forms: {str(e)}')
        flash('An error occurred while loading the export page. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/user/submissions/<int:id>/download-csv')
@login_required
def download_submission_csv(id):
    from export_utils import generate_submissions_csv

    submission = Submission.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    csv_buffer = generate_submissions_csv([submission], include_field_data=False)

    return send_file(
        io.BytesIO(csv_buffer.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'submission_{submission.id}.csv'
    )

@app.route('/admin/submissions/export')
@login_required
@admin_required
def export_user_data():
    # Get filter parameters from request
    user_id = request.args.get('user_id')
    form_id = request.args.get('form_id')
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    export_format = request.args.get('format', 'excel')

    # Base query
    query = Submission.query.join(User).join(Form).options(
        db.joinedload(Submission.user),
        db.joinedload(Submission.form),
        db.joinedload(Submission.hospital),
        db.joinedload(Submission.doctor),
        db.joinedload(Submission.disease)
    )

    # Apply filters
    if user_id and user_id != 'all':
        query = query.filter(Submission.user_id == user_id)
    if form_id and form_id != 'all':
        query = query.filter(Submission.form_id == form_id)
    if status and status != 'all':
        query = query.filter(Submission.status == status)
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Submission.created_at >= start_date)
        except ValueError:
            pass
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Submission.created_at <= end_date)
        except ValueError:
            pass

    # Get all submissions matching the filters
    submissions = query.order_by(Submission.created_at.desc()).all()

    # If export requested
    if export_format in ['excel', 'csv']:
        if export_format == 'excel':
            excel_buffer = generate_detailed_submissions_excel(submissions)
            return send_file(
                excel_buffer,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'submissions_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )
        else:
            csv_buffer = generate_detailed_submissions_csv(submissions)
            return send_file(
                io.BytesIO(csv_buffer.getvalue().encode()),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'submissions_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )

    # Get data for filter dropdowns
    users = User.query.order_by(User.username).all()
    forms = Form.query.order_by(Form.name).all()
    statuses = ['submitted', 'approved', 'rejected', 'needs_revision']

    return render_template('admin/export_data.html', 
                         submissions=submissions,
                         users=users,
                         forms=forms,
                         statuses=statuses,
                         current_filters={
                             'user_id': user_id,
                             'form_id': form_id,
                             'status': status,
                             'start_date': start_date,
                             'end_date': end_date
                         })

@app.route('/admin/submissions/<int:id>/download-pdf')
@login_required
@admin_required
def admin_download_submission_pdf(id):
    from export_utils import generate_submission_pdf

    submission = Submission.query.get_or_404(id)
    pdf_buffer = generate_submission_pdf(submission)

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'submission_{submission.id}.pdf'
    )
