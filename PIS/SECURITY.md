# Security Configuration

This document outlines the security measures implemented in this Flask application.

## Security Improvements Made

### 1. Removed Development Backdoors
- Removed `/dev-login` endpoint that allowed bypassing authentication
- Removed `/setup` endpoint that could delete all users and recreate admin
- Removed `?dev=1` parameter authentication bypass from index and admin routes
- Properly secured admin dashboard with `@login_required` and `@admin_required` decorators

### 2. Environment Variable Configuration
- `SESSION_SECRET`: Used for Flask session encryption (configured via environment)
- `DATABASE_URL`: Database connection string (configured via environment)
- `ADMIN_PASSWORD`: Admin user password (defaults to 'admin123' if not set)
- `FLASK_DEBUG`: Debug mode flag (defaults to False for security)

### 3. Default Admin Account
- Username: `admin`
- Password: **Auto-generated on first run** (displayed in console logs)
- Email: `admin@iitb.ac.in`

**IMPORTANT**: 
- On first startup, the application generates a secure random 20-character password
- This password is displayed ONCE in the console logs - save it immediately!
- Alternatively, set the `ADMIN_PASSWORD` environment variable before first run to use a custom password
- If you lose the auto-generated password, you can set `ADMIN_PASSWORD` and delete the database to recreate the admin user

## Remaining Security Considerations

### 1. CSRF Protection
The application currently does not implement CSRF tokens. For production use, consider:
- Installing Flask-WTF: `pip install flask-wtf`
- Implementing CSRF protection on all POST/DELETE/UPDATE routes
- Adding CSRF tokens to all forms

### 2. Content Security
- User-generated content (form submissions, comments) should be sanitized before display
- Consider implementing input validation and output escaping
- Template auto-escaping is enabled by default in Jinja2

### 3. SQL Injection Prevention
- The application uses SQLAlchemy ORM which provides some protection
- Search functionality uses `.ilike()` which is safer than raw SQL
- Always use parameterized queries when working with user input

### 4. Production Deployment
When deploying to production:
- Set `ADMIN_PASSWORD` to a strong, unique password
- Set `SESSION_SECRET` to a cryptographically secure random string
- Ensure `FLASK_DEBUG` is not set (defaults to False)
- Consider using a production WSGI server (Gunicorn, uWSGI)
- Enable HTTPS/TLS
- Implement rate limiting for login endpoints
- Add CSRF protection

## Environment Variables

Required for production:
```bash
SESSION_SECRET=<your-secret-key-here>
DATABASE_URL=<your-database-url>
ADMIN_PASSWORD=<secure-admin-password>
```

Optional:
```bash
FLASK_DEBUG=False  # Already defaults to False
```
