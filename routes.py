from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import json
import io
from app import app, db, login_manager
from models import User, Disease, Hospital, Doctor, Form, FormField, Submission, DraftSubmission

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need admin privileges to access this page.', 'error')
            return redirect(url_for('index'))
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
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

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
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

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
@login_required
@admin_required
def admin_dashboard():
    disease_count = Disease.query.count()
    hospital_count = Hospital.query.count()
    doctor_count = Doctor.query.count()
    form_count = Form.query.count()
    submission_count = Submission.query.count()
    
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
    
    diseases = Disease.query.all()
    return render_template('admin/form_builder.html', form=form, diseases=diseases)

@app.route('/admin/forms/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_form(id):
    form = Form.query.get_or_404(id)
    db.session.delete(form)
    db.session.commit()
    
    flash('Form deleted successfully', 'success')
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
    return render_template('admin/submission_detail.html', submission=submission)

# User Routes
@app.route('/user')
@login_required
def user_dashboard():
    submissions = Submission.query.filter_by(user_id=current_user.id).order_by(Submission.created_at.desc()).all()
    return render_template('user/dashboard.html', submissions=submissions)

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
    
    return render_template('user/fill_form.html', disease=disease, hospital=hospital, doctor=doctor, form=form)

@app.route('/user/submit/submit-form', methods=['POST'])
@login_required
def submit_form():
    disease_id = request.form.get('disease_id')
    hospital_id = request.form.get('hospital_id')
    doctor_id = request.form.get('doctor_id')
    form_id = request.form.get('form_id')
    
    # Collect form data
    form_data = {}
    for key, value in request.form.items():
        if key.startswith('field_'):
            form_data[key] = value
    
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
    return render_template('user/submission_detail.html', submission=submission)

# Export Routes
@app.route('/user/submissions/<int:id>/download-pdf')
@login_required
def download_submission_pdf(id):
    from export_utils import generate_submission_pdf

    submission = Submission.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    pdf_buffer = generate_submission_pdf(submission)

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'submission_{submission.id}_{submission.form.name.replace(" ", "_")}.pdf'
    )

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
        download_name=f'submission_{submission.id}_{submission.form.name.replace(" ", "_")}.pdf'
    )
