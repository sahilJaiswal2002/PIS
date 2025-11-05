# Overview

IITB SCAN (Patient Information System) is a Flask-based medical data collection and management platform designed for healthcare providers at IIT Bombay. The system facilitates patient form submissions for various diseases, provides administrative oversight of medical data, and enables tracking of patient-doctor-hospital relationships.

The application serves two primary user roles:
- **Patients**: Submit medical forms through a guided multi-step process (disease → hospital → doctor → form)
- **Administrators**: Manage diseases, hospitals, doctors, forms, and review patient submissions

Key features include dynamic form building, submission review workflows, audit logging, analytics dashboards, bulk data import, and export capabilities in multiple formats (CSV, PDF).

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Application Structure

**Framework**: Flask 3.1.2 with SQLAlchemy ORM for database abstraction
**Design Pattern**: MVC-style architecture with route-based controllers split across `routes.py` (patient-facing) and `admin_routes.py` (administrative)

The application follows a modular structure:
- `app.py`: Core Flask application initialization and configuration
- `models.py`: SQLAlchemy database models defining entities and relationships
- `routes.py`: Patient portal routes and authentication logic
- `admin_routes.py`: Administrative dashboard and management routes
- `export_utils.py`: Data export functionality (PDF generation with ReportLab)

## Authentication & Authorization

**Authentication System**: Flask-Login with session-based user management
**Password Security**: Werkzeug password hashing (generate_password_hash/check_password_hash)
**Authorization**: Role-based access control using `is_admin` flag with decorator-based protection (`@admin_required`)

**Default Admin Account**:
- Username: `admin`
- Email: `admin@iitb.ac.in`
- Password: Auto-generated 20-character secure password on first run (displayed in console) or configurable via `ADMIN_PASSWORD` environment variable

**Security Improvements**: Development backdoors removed (no `/dev-login`, `/setup`, or `?dev=1` bypass mechanisms in production code)

## Data Model

**Core Entities**:
- `User`: Patient and admin accounts with authentication credentials
- `Disease`: Medical conditions requiring data collection
- `Hospital`: Healthcare facilities
- `Doctor`: Medical practitioners with hospital affiliations and disease specializations (many-to-many)
- `Form`: Dynamic form templates associated with diseases
- `FormField`: Individual fields within forms (text, number, date, textarea, select types)
- `Submission`: Completed patient forms with JSON data storage
- `SubmissionReview`: Admin review records with approval/rejection workflow
- `DraftSubmission`: Auto-saved incomplete forms
- `AuditLog`: Administrative action tracking

**Key Relationships**:
- Doctor ↔ Disease: Many-to-many through `doctor_diseases` association table
- Form → Disease: One-to-many (forms belong to specific diseases)
- Submission → User/Disease/Hospital/Doctor/Form: Many-to-one relationships establishing complete submission context

**Data Storage Strategy**: Form responses stored as JSON in `Submission.data` field, enabling flexible schema-less field storage while maintaining referential integrity for entities.

## Frontend Architecture

**Design System**: Material Design 3 with healthcare-focused adaptations
**Typography**: Inter (Google Fonts) for readability, JetBrains Mono for IDs/timestamps
**Styling**: Custom CSS with CSS variables for theming (light/dark mode support)
**Template Engine**: Jinja2 with template inheritance (`base.html`, `admin/base.html`, `user/base.html`)

**Layout Strategy**:
- Admin dashboard: Full-width with sidebar navigation
- Patient portal: Top navigation bar with centered content (max-width containers)
- Responsive grid layouts with Tailwind-inspired utility patterns

**Interactive Components**: Vanilla JavaScript for modals, flash message auto-hide, form progress tracking, and dark mode toggle

## Session Management

**Configuration**:
- `SECRET_KEY`: Session encryption key (configurable via `SESSION_SECRET` environment variable)
- Default development key: `'dev-secret-key-change-in-production'`
- Flask-Login handles session persistence and user object loading

## Database Configuration

**Default**: SQLite (`sqlite:///iitb_scan.db`) for development
**Production**: PostgreSQL support via `DATABASE_URL` environment variable with automatic `postgres://` → `postgresql://` URI conversion for compatibility
**Schema Management**: SQLAlchemy with `db.create_all()` on application startup
**Migrations**: Not implemented; relies on `create_all()` for schema initialization

# External Dependencies

## Python Packages

**Core Framework**:
- `flask==3.1.2`: Web application framework
- `flask-sqlalchemy==3.1.1`: SQLAlchemy integration for ORM
- `flask-login==0.6.3`: User session management and authentication
- `sqlalchemy==2.0.23`: Database abstraction layer

**Security**:
- `werkzeug==3.1.3`: Password hashing and security utilities
- `itsdangerous==2.2.0`: Cryptographic signing

**Database Drivers**:
- `psycopg2-binary`: PostgreSQL adapter (production database support)
- SQLite: Built-in Python support (development database)

**Document Generation**:
- `reportlab==4.0.7`: PDF generation for submission exports

**Template & Utilities**:
- `jinja2==3.1.4`: Template engine
- `markupsafe==2.1.5`: Template escaping
- `click==8.3.0`: CLI utilities
- `blinker==1.9.0`: Signal support
- `colorama==0.4.6`: Terminal color support

## Frontend Dependencies

**Node Packages**:
- `concurrently==^9.2.1`: Development script orchestration (listed but not actively used in current setup)

**External CDN Resources**:
- Google Fonts (Inter, JetBrains Mono) - referenced in design guidelines but implementation details not visible in provided files

## Environment Variables

**Required Configuration**:
- `SESSION_SECRET`: Flask session encryption key (defaults to insecure development key)
- `DATABASE_URL`: Database connection string (defaults to SQLite)
- `ADMIN_PASSWORD`: Initial admin password (auto-generated if not provided)
- `FLASK_DEBUG`: Debug mode flag (defaults to False)

**Database URL Format**: Supports both SQLite and PostgreSQL URIs with automatic conversion handling

## Missing Dependencies

**Security Gaps Noted**:
- CSRF protection not implemented (Flask-WTF recommended but not installed)
- No input sanitization library actively used
- SQL injection protection relies solely on SQLAlchemy ORM (no additional validation layer)

**Deployment Considerations**: No WSGI server (gunicorn/uwsgi) configured in requirements; development server only