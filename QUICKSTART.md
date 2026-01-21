# Quick Start Guide

## Prerequisites
- Python 3.8+
- pip and virtualenv

## Setup Instructions

### 1. Create Virtual Environment
```bash
cd alx-backend-security
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 5. Start Development Server
```bash
python manage.py runserver
```

Visit `http://localhost:8000` in your browser.

## Task 0 Files Overview

### ip_tracking/middleware.py
- **IPTrackingMiddleware**: Main middleware class
- **get_client_ip()**: Static method to extract client IP with proxy support

### ip_tracking/models.py
- **RequestLog**: Django model with fields:
  - ip_address (CharField with IPv4/IPv6 validation)
  - timestamp (DateTimeField, auto)
  - path (CharField)
- Helper methods: `get_requests_by_ip()`, `get_requests_by_path()`

### config/settings.py
- Middleware registration
- Logging configuration with rotating file handler
- Database configuration (SQLite for development)
- All Django apps configured

### Admin Interface
- Access via `/admin/`
- View RequestLog entries
- Filter by IP, timestamp, or path
- Read-only logs (no manual creation)

## Database Indexes

The RequestLog model includes:
- Single indexes on: ip_address, timestamp, path
- Composite index: (ip_address, -timestamp) for efficient IP history queries

## Next Steps

After completing Task 0:
1. Run migrations with `python manage.py migrate`
2. Create a superuser with `python manage.py createsuperuser`
3. Access `/admin/` to view logged requests
4. Monitor `logs/ip_tracking.log` for middleware activity

## Troubleshooting

### Migration Errors
```bash
# If migrations fail, reset the database:
rm db.sqlite3
python manage.py migrate
```

### Import Errors
```bash
# Ensure all packages are installed:
pip install -r requirements.txt
```

### Port Already in Use
```bash
# Run on a different port:
python manage.py runserver 8001
```
