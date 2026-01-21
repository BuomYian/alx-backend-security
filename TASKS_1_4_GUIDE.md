# Tasks 1-4: IP Tracking Advanced Features

This document provides a comprehensive guide to all implemented features across Tasks 1-4.

## Overview

This module implements an enterprise-grade IP tracking system with the following capabilities:
- IP blacklisting with management commands
- Geolocation tracking with caching
- Rate limiting for sensitive endpoints
- Anomaly detection using Celery

---

## Task 1: IP Blacklisting

### Overview
Implement IP blocking based on a blacklist to prevent malicious requests from reaching the application.

### Files Created/Modified
- `ip_tracking/models.py` - BlockedIP model
- `ip_tracking/middleware.py` - IP blocking logic
- `ip_tracking/management/commands/block_ip.py` - Management command
- `ip_tracking/admin.py` - BlockedIPAdmin interface

### BlockedIP Model

```python
class BlockedIP(models.Model):
    ip_address: str          # IPv4 or IPv6, unique
    blocked_at: datetime     # Auto-set timestamp
    reason: str              # Text description
```

### Middleware Integration

The IPTrackingMiddleware now:
1. Extracts client IP address
2. **Checks BlockedIP model** - Returns 403 Forbidden if IP is blocked
3. Creates RequestLog entry if IP is allowed
4. Handles geolocation lookup (Task 2)

### Management Command: block_ip

**Usage:**

```bash
# Block a single IP
python manage.py block_ip 192.168.1.100 --reason "Brute force attack"

# Unblock an IP
python manage.py block_ip 192.168.1.100 --unblock

# List all blocked IPs
python manage.py block_ip --list
```

**Features:**
- Color-coded output (success/warning)
- IP address validation
- Prevents duplicate entries
- Updates reason if IP already blocked
- Lists all blocked IPs with timestamps

### Admin Interface

Access at `/admin/ip_tracking/blockedip/`
- List all blocked IPs with timestamps and reasons
- Search by IP address
- Filter by block date
- Add/remove IPs through admin panel

---

## Task 2: IP Geolocation Analytics

### Overview
Enhance logging with geolocation data (country, city) and implement 24-hour caching for performance.

### Files Created/Modified
- `ip_tracking/models.py` - Added country/city fields to RequestLog
- `ip_tracking/middleware.py` - Geolocation lookup integration
- `ip_tracking/geolocation.py` - Geolocation utility module (NEW)
- `config/settings.py` - Cache configuration

### Extended RequestLog Model

```python
class RequestLog(models.Model):
    ip_address: str      # Client IP
    timestamp: datetime  # Request time
    path: str            # Request path
    country: str         # NEW: Country name
    city: str            # NEW: City name
```

### Geolocation Module

**File:** `ip_tracking/geolocation.py`

```python
def get_geolocation(ip_address) -> dict:
    """
    Get geolocation data with 24-hour caching.
    
    Returns: {'country': str, 'city': str}
    """
```

**Features:**
- Uses IPApi.co free API
- 24-hour cache timeout (configurable)
- Automatic private IP detection (returns "Local")
- Graceful error handling with retry logic
- Caches failures to prevent repeated failed requests

### Cache Configuration

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 86400,  # 24 hours
    }
}
```

**Cache Keys:** `geo_{ip_address}` (e.g., `geo_8.8.8.8`)

### Admin Interface Updates

RequestLogAdmin now displays:
- Geolocation fields in list and detail views
- Filterable by country and city
- Searchable by country/city
- Read-only geolocation fields (auto-populated)

---

## Task 3: Rate Limiting by IP

### Overview
Implement rate limiting to prevent abuse by restricting request frequency.

### Files Created/Modified
- `ip_tracking/views.py` - Rate-limited views (NEW)
- `config/urls.py` - Added API endpoints
- `config/settings.py` - Rate limiting configuration

### Views with Rate Limiting

**File:** `ip_tracking/views.py`

#### 1. Login Endpoint
```
POST /api/login/
Rate Limit: 10 requests/minute (by IP)
```

#### 2. Password Reset
```
POST /api/password-reset/
Rate Limit: 5 requests/minute (by IP)
```

#### 3. Get User Logs (Authenticated)
```
GET /api/logs/
Rate Limit: 10 requests/minute (by authenticated user)
```

### Configuration

```python
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_VIEW = 'ip_tracking.views.rate_limit_exceeded'
```

### Rate Limit Rules

| Endpoint | Limit | Type |
|----------|-------|------|
| /api/login/ | 10/min | Per IP |
| /api/password-reset/ | 5/min | Per IP |
| /api/logs/ | 10/min | Per User |

### Response on Rate Limit Exceeded

**Status:** 429 Too Many Requests

```json
{
    "error": "Rate limit exceeded",
    "message": "Too many requests. Please try again later."
}
```

---

## Task 4: Anomaly Detection

### Overview
Implement Celery-based anomaly detection to flag suspicious IP activity automatically.

### Files Created/Modified
- `ip_tracking/models.py` - SuspiciousIP model
- `ip_tracking/tasks.py` - Celery tasks (NEW)
- `config/celery.py` - Celery configuration (NEW)
- `config/__init__.py` - Celery app initialization
- `config/settings.py` - Celery configuration

### SuspiciousIP Model

```python
class SuspiciousIP(models.Model):
    ip_address: str           # IPv4 or IPv6
    reason: str               # Choice: high_requests, admin_access, login_access, pattern_match, other
    detected_at: datetime     # Auto-set
    request_count: int        # Requests in the time window
    is_investigated: bool     # Investigation status
    details: JSONField        # Additional data (dict)
```

### Reason Codes

| Code | Description |
|------|-------------|
| `high_requests` | >100 requests/hour |
| `admin_access` | Attempted access to /admin paths |
| `login_access` | Attempted access to /login paths |
| `pattern_match` | Other suspicious patterns |
| `other` | Uncategorized suspicious activity |

### Celery Configuration

```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Runs hourly via Celery Beat
CELERY_BEAT_SCHEDULE = {
    'check-anomalies-hourly': {
        'task': 'ip_tracking.tasks.detect_anomalies',
        'schedule': crontab(minute=0),  # Every hour
    }
}
```

### Celery Task: detect_anomalies

**Schedule:** Runs every hour (via Celery Beat)

**Detection Logic:**

1. **Excessive Requests Check**
   - Counts requests per IP in the last hour
   - Flags if count > 100
   - Creates SuspiciousIP record

2. **Sensitive Path Access Check**
   - Monitors access to: `/admin`, `/login`, `/api/login/`, `/api/password-reset/`
   - Creates SuspiciousIP record for any access
   - Skips private/local IPs

**Features:**
- Idempotent design (no duplicate flagging within 1 hour)
- Automatic retry with exponential backoff (max 3 retries)
- Comprehensive logging
- JSON details field with detection metadata

### Admin Interface

Access at `/admin/ip_tracking/suspiciousip/`

**Features:**
- List with columns: IP, Reason, Detection Time, Request Count, Investigation Status
- Filter by: Reason, Detection Date, Investigation Status
- Search by IP address
- Bulk action: Mark as Investigated
- Read-only fields except `is_investigated`

---

## Starting the Services

### 1. Django Development Server

```bash
python manage.py runserver
# Starts at http://localhost:8000
```

### 2. Celery Worker (for anomaly detection)

```bash
celery -A config worker -l info
# Processes async tasks
```

### 3. Celery Beat (for hourly schedules)

```bash
celery -A config beat -l info
# Schedules hourly anomaly checks
```

### 4. Redis (required for Celery)

```bash
redis-server
# Runs on localhost:6379
```

**All-in-one with Celery:**

```bash
celery -A config worker -B -l info
# Runs both worker and beat scheduler
```

---

## Testing

### Test IP Blacklisting

```bash
# Block an IP
python manage.py block_ip 127.0.0.1 --reason "Testing"

# Visit site from that IP - should get 403 Forbidden
curl http://localhost:8000/

# Unblock
python manage.py block_ip 127.0.0.1 --unblock
```

### Test Rate Limiting

```bash
# Trigger rate limit (10 in 1 minute)
for i in {1..11}; do
    curl -X POST http://localhost:8000/api/login/
done

# 11th request gets 429
```

### Test Anomaly Detection

```bash
# Generate >100 requests to trigger anomaly
for i in {1..150}; do
    curl http://localhost:8000/ &
done
wait

# Run detection task
celery -A config call ip_tracking.tasks.detect_anomalies

# Check admin for new SuspiciousIP records
```

---

## Database Schema

### Tables Created

1. **ip_tracking_blockedip**
   - id (PK)
   - ip_address (unique, indexed)
   - blocked_at (indexed)
   - reason

2. **ip_tracking_requestlog**
   - id (PK)
   - ip_address (indexed)
   - timestamp (indexed)
   - path (indexed)
   - country (indexed)
   - city (indexed)
   - Composite indexes: (ip_address, -timestamp), (path, -timestamp)

3. **ip_tracking_suspiciousip**
   - id (PK)
   - ip_address (indexed)
   - reason
   - detected_at (indexed)
   - request_count
   - is_investigated (indexed)
   - details (JSON)
   - Composite indexes: (ip_address, -detected_at), (is_investigated, -detected_at)

---

## Performance Considerations

### Caching
- Geolocation: 24-hour cache (reduces API calls)
- Rate limiting: In-memory cache (fast checks)

### Database Indexes
- High-cardinality fields indexed (ip_address, timestamp)
- Composite indexes for common queries
- Reasonable table size management (can partition by date if needed)

### Celery
- Hourly anomaly checks (not per-request)
- Idempotent operations prevent duplicates
- Automatic retries with backoff

---

## Security Notes

1. **IP Blacklisting** - Prevents DDoS from known bad actors
2. **Rate Limiting** - Protects auth endpoints from brute force
3. **Anomaly Detection** - Flags suspicious patterns for review
4. **Geolocation** - For security audit trails
5. **Private IP Handling** - Local IPs not geolocated or flagged as suspicious

---

## Dependencies

New packages installed for Tasks 1-4:

- `django-ratelimit==4.1.0` - Rate limiting framework
- `celery==5.3.4` - Task queue system
- `redis==5.0.1` - Cache and message broker
- `requests==2.31.0` - HTTP requests for geolocation API
- `geoip2==4.7.0` - IP geolocation (already installed)

---

## Next Steps

1. Configure production Redis instance
2. Set up email notifications for suspicious activity
3. Implement IP reputation scoring
4. Add geographic restrictions by country
5. Create admin dashboard for analytics
