# IITB SCAN - Local Setup Guide

This guide will help you set up the IITB SCAN Patient Information System on your local machine with MySQL Workbench.

## Prerequisites

- Python 3.11 or higher
- MySQL Server 8.0 or higher
- MySQL Workbench (optional, for GUI management)
- pip (Python package manager)

## Step 1: Clone or Download the Project

If you haven't already, download the project files to your local machine.

```bash
cd PIS
```

## Step 2: Create a Virtual Environment

It's recommended to use a virtual environment to isolate project dependencies.

### On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

## Step 3: Install Dependencies

Install all required Python packages:

```bash
pip install -r requirements-local.txt
```

## Step 4: Set Up MySQL Database

### 4.1 Create Database in MySQL

Open MySQL Workbench or use the MySQL command line:

```sql
CREATE DATABASE pis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4.2 Verify Database User

Make sure you have a MySQL user with the following credentials:
- **Username**: root
- **Password**: admin
- **Database**: pis

If you need to create/update the user:

```sql
-- Create user if it doesn't exist
CREATE USER 'root'@'localhost' IDENTIFIED BY 'admin';

-- Grant privileges
GRANT ALL PRIVILEGES ON pis.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
```

## Step 5: Configure Environment Variables

Create a `.env` file in the PIS directory with the following content:

```env
# Database Configuration
DATABASE_URL=mysql+pymysql://root:admin@localhost:3306/pis

# Flask Configuration
SECRET_KEY=your-secret-key-here-change-this-in-production
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1

# Application Settings
HOST=127.0.0.1
PORT=5000
```

**Note**: Change `your-secret-key-here-change-this-in-production` to a strong random string for production use.

## Step 6: Initialize the Database

Run the Flask application once to create all database tables:

```bash
python app.py
```

The application will:
1. Create all necessary tables
2. Create a default admin user (username: `admin`, password: `admin123`)
3. Add 10 default security questions

**Important**: Press `Ctrl+C` to stop after the database is initialized.

## Step 7: Run the Application

Start the Flask development server:

```bash
python app.py
```

The application will be available at: http://127.0.0.1:5000

## Step 8: Login

Open your web browser and navigate to http://127.0.0.1:5000

### Default Admin Credentials:
- **Username**: admin
- **Password**: admin123

**Important**: Change the default admin password after first login!

## Features

### Dark Mode / Light Mode
- Click the moon icon (🌙) in the navigation bar or floating button to toggle between dark and light modes
- Your preference is saved in browser localStorage

### Admin Features:
- Dashboard with analytics
- Patient management
- Disease, hospital, and doctor management
- Form builder for custom data collection
- Submission review and approval
- Data export (PDF, Excel)
- Audit logging
- Performance metrics

### User Features:
- Fill out patient data forms
- Select disease, hospital, and doctor
- Save draft submissions
- View submission history

## Database Management

### Using MySQL Workbench:

1. Open MySQL Workbench
2. Connect to your local MySQL server
3. Navigate to the `pis` database
4. You can:
   - View all tables
   - Run SQL queries
   - Export/import data
   - View table relationships

### Database Tables:

The application creates the following tables:
- `user` - User accounts (admin and regular users)
- `disease` - Disease catalog
- `hospital` - Hospital information
- `doctor` - Doctor profiles
- `form` - Dynamic form definitions
- `form_field` - Form field configurations
- `submission` - Patient data submissions
- `audit_log` - System activity logs
- `security_question` - Password recovery questions
- `user_security_question` - User's security answers
- And more...

## Troubleshooting

### Cannot Connect to MySQL

**Error**: `Can't connect to MySQL server on 'localhost'`

**Solution**:
1. Make sure MySQL server is running
2. Check if the port (3306) is correct
3. Verify your username and password

### Module Not Found Error

**Error**: `ModuleNotFoundError: No module named 'flask'`

**Solution**:
1. Make sure your virtual environment is activated
2. Run `pip install -r requirements-local.txt` again

### Database Permission Denied

**Error**: `Access denied for user 'root'@'localhost'`

**Solution**:
1. Check your MySQL username and password in .env file
2. Grant proper privileges to the user:
   ```sql
   GRANT ALL PRIVILEGES ON pis.* TO 'root'@'localhost';
   FLUSH PRIVILEGES;
   ```

### Port Already in Use

**Error**: `Address already in use`

**Solution**:
1. Change the PORT in your .env file to a different port (e.g., 5001)
2. Or stop the process using port 5000:
   - Windows: `netstat -ano | findstr :5000` then `taskkill /PID <PID> /F`
   - macOS/Linux: `lsof -ti:5000 | xargs kill -9`

## Production Deployment

For production deployment, consider:

1. **Use a production WSGI server** (e.g., Gunicorn instead of Flask development server):
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

2. **Secure your database credentials**
   - Use environment variables
   - Never commit credentials to version control

3. **Enable HTTPS**
   - Use a reverse proxy like Nginx
   - Get SSL certificate from Let's Encrypt

4. **Change default admin password**

5. **Set up database backups**
   ```bash
   mysqldump -u root -p pis > backup_$(date +%Y%m%d).sql
   ```

## Additional Configuration

### Changing Database Credentials

If you want to use different MySQL credentials, update the `DATABASE_URL` in your `.env` file:

```env
DATABASE_URL=mysql+pymysql://your_username:your_password@localhost:3306/your_database
```

### Using a Different Port

To run the application on a different port, update the `.env` file:

```env
PORT=8080
```

Then run:
```bash
python app.py
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the main README.md
3. Check application logs for error messages

## Development Tips

### Running Database Migrations

If you make changes to the models, you may need to drop and recreate tables:

```sql
-- In MySQL Workbench or command line
USE pis;
DROP DATABASE pis;
CREATE DATABASE pis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Then run `python app.py` again to recreate tables.

### Debugging

Enable Flask debug mode (already enabled in development):
- Debug toolbar will show
- Auto-reload on code changes
- Detailed error pages

### Testing Dark/Light Mode

The theme toggle works by:
1. Setting `data-theme="dark"` attribute on the HTML element
2. Storing preference in localStorage
3. Applying CSS variables based on the theme

Test by:
- Clicking the moon/sun toggle button
- Checking browser localStorage for `darkMode` key
- Inspecting HTML element for `data-theme` attribute
