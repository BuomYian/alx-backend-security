# IP Tracking Backend

A comprehensive Django application for IP address tracking, logging, geolocation, and security analysis. This module provides tools for understanding user behavior, enhancing security, and maintaining legal compliance in web applications.

## 🎯 Learning Objectives

- Understand the role of IP tracking in web security and analytics
- Implement request logging using Django middleware
- Blacklist malicious IPs and manage access control efficiently
- Use IP geolocation to enhance personalization and fraud detection
- Apply rate limiting techniques to prevent abuse
- Detect anomalies using log data and basic machine learning
- Address privacy, compliance, and ethical considerations

## 📋 Project Structure

```
alx-backend-security/
├── config/                  # Django configuration
│   ├── __init__.py
│   ├── settings.py         # Project settings
│   ├── urls.py            # URL routing
│   └── wsgi.py            # WSGI configuration
├── ip_tracking/            # IP Tracking app
│   ├── __init__.py
│   ├── apps.py            # App configuration
│   ├── middleware.py       # IPTrackingMiddleware
│   ├── models.py           # RequestLog model
│   ├── views.py            # Views (TBD)
│   ├── admin.py            # Django admin configuration (TBD)
│   └── tests.py            # Tests (TBD)
├── templates/              # HTML templates
│   └── index.html
├── manage.py               # Django management script
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## ✅ Task 0: Basic IP Logging Middleware (COMPLETED)

### Objective
Implement middleware to log the IP address, timestamp, and path of every incoming request.

### Deliverables

#### 1. **IPTrackingMiddleware** (`ip_tracking/middleware.py`)
A middleware class that:
- Extracts the client's IP address from the request
- Handles proxy scenarios (X-Forwarded-For header)
- Logs IP, timestamp, and request path to the database
- Includes error handling for failed logging operations

**Key Features:**
- `get_client_ip()`: Extracts client IP, supporting proxy detection
- Graceful error handling with logging
- Minimal performance overhead

#### 2. **RequestLog Model** (`ip_tracking/models.py`)
A Django model with:
- `ip_address` (CharField, max 45 chars): Supports IPv4 and IPv6 with validation
- `timestamp` (DateTimeField, auto): Automatically recorded on creation
- `path` (CharField, max 2048): The requested URL path

**Additional Features:**
- Database indexes on `ip_address`, `timestamp`, and `path` for efficient querying
- Composite index on `(ip_address, -timestamp)` for quick IP history lookups
- Helper methods: `get_requests_by_ip()` and `get_requests_by_path()`
- Ordered by `-timestamp` by default (newest first)
- Admin-friendly verbose naming

#### 3. **Middleware Registration** (`config/settings.py`)
The middleware is registered in the `MIDDLEWARE` list:
```python
MIDDLEWARE = [
    # ... other middleware ...
    'ip_tracking.middleware.IPTrackingMiddleware',
]
```

**Placement:** Added at the end to ensure all previous middleware processes the request before logging.

### How It Works

1. **Request Reception**: When a request arrives, the middleware intercepts it
2. **IP Extraction**: Extracts the client IP (with proxy awareness)
3. **Logging**: Creates a `RequestLog` entry with IP, timestamp, and path
4. **Error Handling**: Logs any database errors without breaking the request
5. **Request Continuation**: Passes control to the next middleware/view

### Usage Example

After running migrations, the middleware will automatically log all requests:

```bash
# Create and run migrations
python manage.py makemigrations
python manage.py migrate

# Start the development server
python manage.py runserver

# View logs in Django admin
# Navigate to /admin/ → IP Tracking → Request Logs
```

### Database Indexes

Optimized for common queries:
- Query by IP: `RequestLog.objects.filter(ip_address='192.168.1.1')`
- Query by path: `RequestLog.objects.filter(path='/api/users/')`
- Recent activity: `RequestLog.get_requests_by_ip(ip_address, limit=50)`

### Logging Configuration

Configured in `settings.py` with:
- Console and file handlers
- Rotating file handler (10 MB max, 5 backups)
- Structured log directory: `logs/ip_tracking.log`

### IP Address Handling

**IPv4 & IPv6 Support:**
- Validates all IP addresses using Django's `validate_ipv46_address`
- Max 45 characters (IPv6 max length)

**Proxy Detection:**
```python
# Behind proxy: Uses X-Forwarded-For
# Direct: Uses REMOTE_ADDR
client_ip = get_client_ip(request)
```

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/BuomYian/alx-backend-security.git
cd alx-backend-security
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 6. Start Development Server
```bash
python manage.py runserver
```

Visit `http://localhost:8000` in your browser.

## 🔐 Privacy & Compliance

### Best Practices Implemented

1. **IP Validation**: Only IPv4 and IPv6 addresses are accepted
2. **Error Handling**: Failed logging doesn't break the application
3. **Database Optimization**: Efficient indexing prevents performance issues
4. **Logging Rotation**: Prevents log files from consuming excessive disk space

### Upcoming Features (Future Tasks)

- IP anonymization/truncation
- Automatic log retention policies
- GDPR/CCPA compliance tools
- Rate limiting
- IP blacklisting
- Geolocation integration
- Anomaly detection

## 📚 Tools & Libraries

- **Django**: Web framework for request handling
- **django-ipware**: Client IP extraction (future integration)
- **Celery**: Asynchronous task processing (future)
- **Redis**: Fast caching and rate limiting (future)
- **GeoIP2**: IP geolocation (future)
- **scikit-learn**: Machine learning for anomaly detection (future)

## 🔄 Upcoming Tasks

- **Task 1**: IP Blacklisting
- **Task 2**: IP Geolocation
- **Task 3**: Rate Limiting
- **Task 4**: Anomaly Detection
- **Task 5**: Privacy & Compliance Tools

## 📖 Documentation

Each module includes docstrings following Google/PEP 257 standards:
- Middleware: IP extraction logic, error handling
- Model: Field descriptions, query helpers, indexing strategy

## 🧪 Testing (To Be Implemented)

```bash
python manage.py test ip_tracking
```

## 📝 License

This project is part of the ALX Backend Security Course.

## 👤 Author

**Repository**: [BuomYian/alx-backend-security](https://github.com/BuomYian/alx-backend-security)

---

**Status**: ✅ Task 0 Complete | Ready for Task 1
