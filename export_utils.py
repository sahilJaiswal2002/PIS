import json
import csv
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


def generate_submission_pdf(submission):
    """Generate a PDF from a submission"""
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2196F3'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1976D2'),
        spaceAfter=8,
        spaceBefore=12
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    # Title
    story.append(Paragraph("IITB SCAN - Form Submission", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Submission metadata
    story.append(Paragraph("Submission Details", heading_style))
    metadata = [
        ['Field', 'Value'],
        ['Submission ID', str(submission.id)],
        ['Patient Name', submission.user.username],
        ['Patient Email', submission.user.email],
        ['Form Name', submission.form.name],
        ['Disease', submission.disease.name],
        ['Hospital', submission.hospital.name],
        ['Doctor', submission.doctor.name],
        ['Status', submission.status.title()],
        ['Submitted On', submission.created_at.strftime('%B %d, %Y at %H:%M:%S')],
        ['Updated On', submission.updated_at.strftime('%B %d, %Y at %H:%M:%S')],
    ]
    
    metadata_table = Table(metadata, colWidths=[2*inch, 4*inch])
    metadata_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E3F2FD')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(metadata_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Form data
    story.append(Paragraph("Form Responses", heading_style))
    submission_data = json.loads(submission.data)
    
    form_data = [['Field', 'Response']]
    for field in submission.form.fields:
        field_key = f'field_{field.field_name}'
        value = submission_data.get(field_key, 'Not provided')
        form_data.append([field.field_label, str(value)])
    
    form_table = Table(form_data, colWidths=[2.5*inch, 3.5*inch])
    form_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F5F5F5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(form_table)
    
    # Footer
    story.append(Spacer(1, 0.3*inch))
    footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')} | IITB SCAN - Patient Data Collection System"
    story.append(Paragraph(footer_text, ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )))
    
    # Build PDF
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer


def generate_submissions_csv(submissions, include_field_data=False):
    """Generate a CSV from multiple submissions"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    if include_field_data:
        writer.writerow([
            'ID', 'Patient', 'Email', 'Form', 'Disease', 'Hospital', 'Doctor',
            'Status', 'Form Version', 'Created At', 'Updated At'
        ])
    else:
        writer.writerow([
            'ID', 'Patient', 'Email', 'Form', 'Disease', 'Hospital', 'Doctor',
            'Status', 'Created At', 'Updated At'
        ])
    
    # Data rows
    for submission in submissions:
        row = [
            submission.id,
            submission.user.username,
            submission.user.email,
            submission.form.name,
            submission.disease.name,
            submission.hospital.name,
            submission.doctor.name,
            submission.status,
            submission.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            submission.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        ]
        
        if not include_field_data:
            row.insert(8, submission.form_version)
        
        writer.writerow(row)
    
    output.seek(0)
    return output


def generate_detailed_submissions_csv(submissions):
    """Generate a detailed CSV with all form field responses"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    if not submissions:
        return output
    
    # Build header with all possible fields
    all_fields = set()
    for sub in submissions:
        for field in sub.form.fields:
            all_fields.add(field.field_label)
    
    header = ['ID', 'Patient', 'Email', 'Form', 'Disease', 'Hospital', 'Doctor', 'Status', 'Created At']
    header.extend(sorted(all_fields))
    writer.writerow(header)
    
    # Write data rows
    for submission in submissions:
        submission_data = json.loads(submission.data)
        row = [
            submission.id,
            submission.user.username,
            submission.user.email,
            submission.form.name,
            submission.disease.name,
            submission.hospital.name,
            submission.doctor.name,
            submission.status,
            submission.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ]
        
        # Add field data
        for field in submission.form.fields:
            field_key = f'field_{field.field_name}'
            value = submission_data.get(field_key, '')
            row.append(str(value))
        
        writer.writerow(row)
    
    output.seek(0)
    return output
