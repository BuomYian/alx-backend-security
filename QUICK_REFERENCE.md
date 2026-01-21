# Quick Reference: Tasks 1-4 Commands

## Setup & Running

### Initial Setup
```bash
cd /home/buomyian/alx-backend-security
python manage.py migrate           # Apply all migrations
python manage.py createsuperuser   # Create admin user
```

### Start Development Stack
```bash
# Terminal 1: Django Server
python manage.py runserver

# Terminal 2: Redis (required for Celery)
redis-server

# Terminal 3: Celery Worker + Beat
celery -A config worker -B -l info
```

---

## Task 1: IP Blacklisting

### Block/Unblock IPs
```bash
# Block single IP
python manage.py block_ip 192.168.1.100 --reason "Brute force attack"

# Block with default reason
python manage.py block_ip 10.0.0.50

# Unblock IP
python manage.py block_ip 192.168.1.100 --unblock

# List all blocked IPs
python manage.py block_ip --list
```

### Admin Management
```
URL: http://localhost:8000/admin/ip_tracking/blockedip/
- Add/Remove IPs
- View timestamps and reasons
- Search and filter
```

---

## Task 2: IP Geolocation Analytics

### View Geolocation Data
```bash
python manage.py shell
```

```python
from ip_tracking.models import RequestLog
from ip_tracking.geolocation import get_geolocation

# View recent logs with geolocation
RequestLog.objects.values('ip_address', 'country', 'city')[:10]

# Manual geolocation lookup
get_geolocation('8.8.8.8')  # Returns: {'country': 'United States', 'city': 'Mountain View'}
get_geolocation('127.0.0.1')  # Returns: {'country': 'Local', 'city': 'Local'}
```

### Admin Interface
```
URL: http://localhost:8000/admin/ip_tracking/requestlog/
- View all requests with geolocation
- Filter by country/city
- Search by path or IP
```

---

## Task 3: Rate Limiting

### Test Rate Limiting
```bash
# Test login endpoint (10/min limit)
for i in {1..15}; do curl -X POST http://localhost:8000/api/login/; done

# Test password reset (5/min limit)
for i in {1..10}; do curl -X POST http://localhost:8000/api/password-reset/; done
```

### API Endpoints
```
POST /api/login/              (10 requests/minute per IP)
POST /api/password-reset/     (5 requests/minute per IP)
GET  /api/logs/               (10 requests/minute per user, requires auth)
```

### Rate Limit Responses
```
HTTP 429 Too Many Requests
{
    "error": "Rate limit exceeded",
    "message": "Too many requests. Please try again later."
}
```

---

## Task 4: Anomaly Detection

### Manual Anomaly Detection
```bash
# Trigger detection manually
celery -A config call ip_tracking.tasks.detect_anomalies

# Or via shell
python manage.py shell
from ip_tracking.tasks import detect_anomalies
result = detect_anomalies.apply()  # Returns task result
```

### Generate Test Data
```bash
# Create 150 requests from localhost (triggers anomaly)
for i in {1..150}; do
    curl http://localhost:8000/ > /dev/null &
done
wait

# Then run anomaly detection
celery -A config call ip_tracking.tasks.detect_anomalies

# Check admin for new SuspiciousIP records
```

### View Anomalies
```python
python manage.py shell

from ip_tracking.models import SuspiciousIP

# All suspicious IPs
SuspiciousIP.objects.all()

# By reason
SuspiciousIP.objects.filter(reason='high_requests')
SuspiciousIP.objects.filter(reason='admin_access')

# Not yet investigated
SuspiciousIP.objects.filter(is_investigated=False)

# With details
for s in SuspiciousIP.objects.all():
    print(f"{s.ip_address}: {s.get_reason_display()}")
    print(f"  Details: {s.details}")
```

### Admin Management
```
URL: http://localhost:8000/admin/ip_tracking/suspiciousip/
- View all flagged IPs
- Filter by reason and date
- Mark as investigated (bulk action)
- View detailed anomaly information
```

---

## Database Queries

### Request Logs
```python
from ip_tracking.models import RequestLog
from django.utils.timezone import now, timedelta

# All logs from last hour
RequestLog.objects.filter(timestamp__gte=now() - timedelta(hours=1))

# Logs by country
RequestLog.objects.filter(country='United States')

# Top requesting IPs
from django.db.models import Count
RequestLog.objects.values('ip_address').annotate(
    count=Count('id')
).order_by('-count')[:10]

# Logs to sensitive paths
RequestLog.objects.filter(path__startswith='/admin')
RequestLog.objects.filter(path__startswith='/login')
```

### Blocked IPs
```python
from ip_tracking.models import BlockedIP

# All blocked IPs
BlockedIP.objects.all()

# Recently blocked
BlockedIP.objects.order_by('-blocked_at')[:10]

# Search by reason
BlockedIP.objects.filter(reason__icontains='brute')
```

### Suspicious IPs
```python
from ip_tracking.models import SuspiciousIP

# All suspicious
SuspiciousIP.objects.all()

# High request volume
SuspiciousIP.objects.filter(reason='high_requests')

# Admin access attempts
SuspiciousIP.objects.filter(reason='admin_access')

# Not investigated
SuspiciousIP.objects.filter(is_investigated=False).count()
```

---

## Logs & Debugging

### Django Logs
```bash
# View logs in real-time
tail -f logs/ip_tracking.log

# View middleware debug logs
python manage.py runserver --verbosity 3
```

### Celery Logs
```bash
# View Celery worker logs
celery -A config worker -l debug

# View Celery Beat schedule
celery -A config beat -l debug
```

### Database Logs
```bash
# Enable SQL query logging
python manage.py shell --verbosity 3
```

---

## Troubleshooting

### Redis Not Running
```bash
# Check if Redis is running
redis-cli ping  # Should return: PONG

# Start Redis
redis-server

# Clear Redis cache (if needed)
redis-cli FLUSHDB
```

### Celery Not Processing Tasks
```bash
# Check worker status
celery -A config inspect active

# View worker stats
celery -A config inspect stats

# Restart worker
pkill -f celery
celery -A config worker -B -l info &
```

### Geolocation API Issues
```bash
# Test API manually
curl https://ipapi.co/8.8.8.8/json/

# Clear geolocation cache
python manage.py shell
from django.core.cache import cache
cache.clear()
```

### Migrations Issues
```bash
# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

---

## Performance Tips

### Optimize Queries
```python
# Use select_related for ForeignKey
RequestLog.objects.select_related('user')

# Use prefetch_related for ManyToMany
RequestLog.objects.prefetch_related('tags')

# Only select needed fields
RequestLog.objects.values('ip_address', 'country')
```

### Cache Geolocation Lookup
```python
# Already cached for 24 hours via get_geolocation()
from ip_tracking.geolocation import get_geolocation
result = get_geolocation('8.8.8.8')  # Uses cache
```

### Batch Operations
```python
# Create multiple logs efficiently
logs = [
    RequestLog(ip_address='1.1.1.1', path='/path1', country='US', city='NYC'),
    RequestLog(ip_address='2.2.2.2', path='/path2', country='UK', city='London'),
]
RequestLog.objects.bulk_create(logs)

# Update multiple records
SuspiciousIP.objects.filter(is_investigated=False).update(is_investigated=True)
```

---

## Production Checklist

- [ ] Configure production Redis with persistence
- [ ] Set up email notifications for anomalies
- [ ] Configure HTTPS for sensitive endpoints
- [ ] Enable CORS for API endpoints
- [ ] Set up monitoring/alerting
- [ ] Configure database backups
- [ ] Set rate limits appropriate for your scale
- [ ] Test anomaly detection thresholds
- [ ] Set up log aggregation (ELK, etc.)
- [ ] Document incident response procedures

---

## Files Structure

```
alx-backend-security/
├── config/
│   ├── celery.py              # Celery configuration
│   ├── settings.py            # Django settings (cache, ratelimit, celery)
│   ├── urls.py                # URL routing (API endpoints)
│   └── __init__.py            # Celery app initialization
├── ip_tracking/
│   ├── models.py              # RequestLog, BlockedIP, SuspiciousIP
│   ├── middleware.py          # IP blocking + geolocation
│   ├── views.py               # Rate-limited endpoints
│   ├── geolocation.py         # Geolocation with caching
│   ├── tasks.py               # Celery anomaly detection
│   ├── admin.py               # Admin interfaces
│   ├── management/
│   │   └── commands/
│   │       └── block_ip.py    # Management command
│   └── migrations/
│       ├── 0002_blockedip.py
│       ├── 0003_requestlog_city_requestlog_country.py
│       └── 0004_suspiciousip.py
├── templates/
│   └── index.html
├── requirements.txt
├── manage.py
├── TASKS_1_4_GUIDE.md         # Detailed documentation
└── IMPLEMENTATION_SUMMARY.md  # Overview
```

---

## Useful Links

- Django Docs: https://docs.djangoproject.com/
- Celery Docs: https://docs.celeryproject.org/
- Django RateLimit: https://github.com/ccbcc/django-ratelimit
- IPApi.co: https://ipapi.co/
- Redis: https://redis.io/

---

Created: January 21, 2026
Last Updated: January 21, 2026
