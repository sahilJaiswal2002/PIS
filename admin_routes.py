from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import json
import csv
import io
from app import app, db
from models import (
    User, Disease, Hospital, Doctor, Form, FormField, Submission, 
    SubmissionReview, DraftSubmission, AuditLog
)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need admin privileges to access this page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def log_audit(action, entity_type, entity_id, entity_name, details=None):
    """Log an audit trail of admin actions"""
    audit = AuditLog(
        user_id=current_user.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        details=json.dumps(details) if details else None,
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()

# ===== Patient Search Routes =====

@app.route('/admin/patients')
@login_required
@admin_required
def admin_patients():
    """List all patients with search functionality"""
    search_query = request.args.get('search', '')
    search_type = request.args.get('type', 'all')  # all, username, email, id
    
    query = User.query.filter_by(is_admin=False)
    
    if search_query:
        if search_type == 'username':
            query = query.filter(User.username.ilike(f'%{search_query}%'))
        elif search_type == 'email':
            query = query.filter(User.email.ilike(f'%{search_query}%'))
        elif search_type == 'id':
            try:
                query = query.filter(User.id == int(search_query))
            except ValueError:
                query = query.filter(User.id == -1)  # Return no results
        else:  # all
            query = query.filter(
                (User.username.ilike(f'%{search_query}%')) |
                (User.email.ilike(f'%{search_query}%'))
            )
    
    patients = query.order_by(User.created_at.desc()).all()
    
    return render_template('admin/patients.html', 
                         patients=patients, 
                         search_query=search_query,
                         search_type=search_type)

@app.route('/admin/patients/<int:patient_id>')
@login_required
@admin_required
def admin_patient_detail(patient_id):
    """View detailed patient information and submission history"""
    patient = User.query.filter_by(id=patient_id, is_admin=False).first_or_404()
    submissions = Submission.query.filter_by(user_id=patient_id).order_by(Submission.created_at.desc()).all()
    drafts = DraftSubmission.query.filter_by(user_id=patient_id).order_by(DraftSubmission.updated_at.desc()).all()
    
    return render_template('admin/patient_detail.html',
                         patient=patient,
                         submissions=submissions,
                         drafts=drafts)

# ===== Bulk Import Routes =====

@app.route('/admin/bulk-import', methods=['GET', 'POST'])
@login_required
@admin_required
def bulk_import():
    """Handle bulk CSV import for diseases, hospitals, doctors"""
    if request.method == 'POST':
        import_type = request.form.get('import_type')
        file = request.files.get('file')
        
        if not file or file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        try:
            stream = io.TextIOWrapper(file.stream, encoding='utf-8')
            csv_reader = csv.DictReader(stream)
            imported_count = 0
            
            if import_type == 'diseases':
                for row in csv_reader:
                    disease = Disease(
                        name=row.get('name', ''),
                        description=row.get('description', '')
                    )
                    db.session.add(disease)
                    imported_count += 1
                log_audit('Bulk Import', 'Disease', None, f'{imported_count} diseases', {'count': imported_count})
                
            elif import_type == 'hospitals':
                for row in csv_reader:
                    hospital = Hospital(
                        name=row.get('name', ''),
                        address=row.get('address', ''),
                        phone=row.get('phone', '')
                    )
                    db.session.add(hospital)
                    imported_count += 1
                log_audit('Bulk Import', 'Hospital', None, f'{imported_count} hospitals', {'count': imported_count})
                
            elif import_type == 'doctors':
                for row in csv_reader:
                    hospital = Hospital.query.filter_by(name=row.get('hospital')).first()
                    if hospital:
                        doctor = Doctor(
                            name=row.get('name', ''),
                            specialization=row.get('specialization', ''),
                            hospital_id=hospital.id
                        )
                        db.session.add(doctor)
                        imported_count += 1
                log_audit('Bulk Import', 'Doctor', None, f'{imported_count} doctors', {'count': imported_count})
            
            db.session.commit()
            flash(f'Successfully imported {imported_count} records', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Import failed: {str(e)}', 'error')
        
        return redirect(url_for('bulk_import'))
    
    return render_template('admin/bulk_import.html')

# ===== Submission Review Routes =====

@app.route('/admin/submissions-pending')
@login_required
@admin_required
def admin_submissions_pending():
    """View submissions pending review"""
    status_filter = request.args.get('status', 'submitted')
    submissions = Submission.query.filter_by(status=status_filter).order_by(Submission.created_at.desc()).all()
    
    return render_template('admin/submissions_pending.html',
                         submissions=submissions,
                         status_filter=status_filter)

@app.route('/admin/submissions/<int:submission_id>/review', methods=['GET', 'POST'])
@login_required
@admin_required
def review_submission(submission_id):
    """Review and approve/reject a submission"""
    submission = Submission.query.get_or_404(submission_id)
    
    if request.method == 'POST':
        review_status = request.form.get('review_status')
        comment = request.form.get('comment', '')
        
        review = SubmissionReview(
            submission_id=submission_id,
            reviewer_id=current_user.id,
            status=review_status,
            comment=comment
        )
        
        if review_status == 'approved':
            submission.status = 'approved'
        elif review_status == 'rejected':
            submission.status = 'rejected'
        else:
            submission.status = 'needs_revision'
        
        submission.updated_at = datetime.utcnow()
        
        db.session.add(review)
        db.session.commit()
        
        log_audit(
            'Review Submission',
            'Submission',
            submission_id,
            f'Patient: {submission.user.username}',
            {'status': review_status, 'comment': comment}
        )
        
        flash(f'Submission {review_status}', 'success')
        return redirect(url_for('admin_submissions_pending'))
    
    previous_reviews = SubmissionReview.query.filter_by(submission_id=submission_id).order_by(SubmissionReview.created_at.desc()).all()
    form = Form.query.get(submission.form_id)
    submission_data = json.loads(submission.data)
    
    return render_template('admin/submission_review.html',
                         submission=submission,
                         form=form,
                         submission_data=submission_data,
                         previous_reviews=previous_reviews)

# ===== Analytics Routes =====

@app.route('/admin/analytics')
@login_required
@admin_required
def analytics_dashboard():
    """Main analytics dashboard"""
    # Summary metrics
    total_submissions = Submission.query.count()
    approved_submissions = Submission.query.filter_by(status='approved').count()
    pending_submissions = Submission.query.filter_by(status='submitted').count()
    rejected_submissions = Submission.query.filter_by(status='rejected').count()
    
    completion_rate = 0
    if total_submissions > 0:
        completion_rate = (approved_submissions / total_submissions) * 100
    
    # Submissions by disease
    disease_stats = db.session.query(
        Disease.name,
        db.func.count(Submission.id).label('count')
    ).join(Submission).group_by(Disease.name).order_by(db.func.count(Submission.id).desc()).limit(10).all()
    
    # Submissions by hospital
    hospital_stats = db.session.query(
        Hospital.name,
        db.func.count(Submission.id).label('count')
    ).join(Submission).group_by(Hospital.name).order_by(db.func.count(Submission.id).desc()).limit(10).all()
    
    # Submissions by doctor
    doctor_stats = db.session.query(
        Doctor.name,
        db.func.count(Submission.id).label('count')
    ).join(Submission).group_by(Doctor.name).order_by(db.func.count(Submission.id).desc()).limit(10).all()
    
    # Time trend data (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_submissions = db.session.query(
        db.func.date(Submission.created_at).label('date'),
        db.func.count(Submission.id).label('count')
    ).filter(Submission.created_at >= thirty_days_ago).group_by(
        db.func.date(Submission.created_at)
    ).order_by('date').all()
    
    return render_template('admin/analytics.html',
                         total_submissions=total_submissions,
                         approved_submissions=approved_submissions,
                         pending_submissions=pending_submissions,
                         rejected_submissions=rejected_submissions,
                         completion_rate=int(completion_rate),
                         disease_stats=disease_stats,
                         hospital_stats=hospital_stats,
                         doctor_stats=doctor_stats,
                         daily_submissions=daily_submissions)

# ===== Performance Metrics Routes =====

@app.route('/admin/performance')
@login_required
@admin_required
def performance_metrics():
    """Performance metrics and drop-off analysis"""
    # Form completion metrics
    forms = Form.query.all()
    form_metrics = []
    
    for form in forms:
        total_forms_started = db.session.query(db.func.count(DraftSubmission.id)).filter_by(form_id=form.id).scalar()
        total_submitted = Submission.query.filter_by(form_id=form.id).count()
        completion_rate = 0
        if total_forms_started > 0:
            completion_rate = (total_submitted / total_forms_started) * 100
        
        avg_submission_time = 0
        submissions = Submission.query.filter_by(form_id=form.id).all()
        if submissions:
            total_time = sum((s.updated_at - s.created_at).total_seconds() for s in submissions)
            avg_submission_time = int(total_time / len(submissions))
        
        form_metrics.append({
            'form': form,
            'started': total_forms_started or 0,
            'submitted': total_submitted,
            'completion_rate': int(completion_rate),
            'avg_time_seconds': avg_submission_time
        })
    
    # Status distribution
    status_counts = db.session.query(
        Submission.status,
        db.func.count(Submission.id).label('count')
    ).group_by(Submission.status).all()
    
    return render_template('admin/performance.html',
                         form_metrics=form_metrics,
                         status_counts=status_counts)

# ===== Audit Logs Routes =====

@app.route('/admin/audit-logs')
@login_required
@admin_required
def audit_logs():
    """View audit logs of admin actions"""
    action_filter = request.args.get('action', '')
    entity_type_filter = request.args.get('entity_type', '')
    user_filter = request.args.get('user', '')
    
    query = AuditLog.query
    
    if action_filter:
        query = query.filter(AuditLog.action.ilike(f'%{action_filter}%'))
    if entity_type_filter:
        query = query.filter(AuditLog.entity_type == entity_type_filter)
    if user_filter:
        query = query.filter(AuditLog.user.has(User.username.ilike(f'%{user_filter}%')))
    
    logs = query.order_by(AuditLog.created_at.desc()).paginate(per_page=50)
    
    # Get unique values for filters
    actions = db.session.query(AuditLog.action.distinct()).all()
    entity_types = db.session.query(AuditLog.entity_type.distinct()).all()
    users = db.session.query(User.username).filter(User.is_admin == True).all()
    
    return render_template('admin/audit_logs.html',
                         logs=logs,
                         action_filter=action_filter,
                         entity_type_filter=entity_type_filter,
                         user_filter=user_filter,
                         actions=[a[0] for a in actions],
                         entity_types=[e[0] for e in entity_types],
                         users=[u[0] for u in users])

# ===== Export Routes =====

@app.route('/admin/export-submissions', methods=['GET', 'POST'])
@login_required
@admin_required
def export_submissions():
    """Export submissions to CSV"""
    if request.method == 'POST':
        format_type = request.form.get('format', 'csv')
        date_from = request.form.get('date_from')
        date_to = request.form.get('date_to')
        status_filter = request.form.get('status', '')
        
        query = Submission.query
        
        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Submission.created_at >= date_from)
        
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            date_to = date_to.replace(hour=23, minute=59, second=59)
            query = query.filter(Submission.created_at <= date_to)
        
        if status_filter:
            query = query.filter(Submission.status == status_filter)
        
        submissions = query.order_by(Submission.created_at.desc()).all()
        
        if format_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                'ID', 'Patient', 'Form', 'Disease', 'Hospital', 'Doctor',
                'Status', 'Created At', 'Updated At'
            ])
            
            for sub in submissions:
                writer.writerow([
                    sub.id,
                    sub.user.username,
                    sub.form.name,
                    sub.disease.name,
                    sub.hospital.name,
                    sub.doctor.name,
                    sub.status,
                    sub.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    sub.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
            
            log_audit('Export', 'Submission', None, f'{len(submissions)} submissions', 
                     {'format': format_type, 'count': len(submissions)})
            
            from flask import Response
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment;filename=submissions.csv'}
            )
    
    return render_template('admin/export.html')
