"""
Celery Tasks for Anomaly Detection.

This module contains asynchronous tasks for detecting suspicious IP activity.
"""

import logging
from datetime import timedelta
from django.utils.timezone import now
from django.db.models import Count, Q
from celery import shared_task
from .models import RequestLog, SuspiciousIP, BlockedIP

logger = logging.getLogger(__name__)

# Thresholds for anomaly detection
REQUEST_THRESHOLD_PER_HOUR = 100
SENSITIVE_PATHS = ['/admin', '/admin/', '/login',
                   '/api/login/', '/api/password-reset/']


@shared_task(bind=True, max_retries=3)
def detect_anomalies(self):
    """
    Detect anomalous IP activity and create SuspiciousIP records.

    This task runs hourly and checks for:
    1. IPs with more than 100 requests in the last hour
    2. IPs accessing sensitive paths (admin, login)

    The task is idempotent and handles retries gracefully.
    """
    try:
        logger.info("Starting anomaly detection task...")

        # Get the last hour of request logs
        one_hour_ago = now() - timedelta(hours=1)
        recent_logs = RequestLog.objects.filter(timestamp__gte=one_hour_ago)

        # Check for IPs with excessive requests
        _check_excessive_requests(recent_logs)

        # Check for sensitive path access attempts
        _check_sensitive_paths(recent_logs)

        logger.info("Anomaly detection task completed successfully")
        return {
            'status': 'success',
            'message': 'Anomaly detection completed'
        }

    except Exception as exc:
        logger.error(f"Anomaly detection failed: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


def _check_excessive_requests(recent_logs):
    """
    Check for IPs with excessive requests in the last hour.

    Args:
        recent_logs: QuerySet of recent RequestLog entries.
    """
    # Group by IP and count requests
    ip_counts = recent_logs.values('ip_address').annotate(
        count=Count('id')
    ).filter(count__gt=REQUEST_THRESHOLD_PER_HOUR)

    for ip_data in ip_counts:
        ip_address = ip_data['ip_address']
        request_count = ip_data['count']

        # Skip if already flagged
        if SuspiciousIP.objects.filter(
            ip_address=ip_address,
            reason='high_requests',
            detected_at__gte=now() - timedelta(hours=1)
        ).exists():
            continue

        logger.warning(
            f"Anomaly detected: IP {ip_address} made {request_count} requests in 1 hour"
        )

        # Create suspicious IP record
        SuspiciousIP.objects.create(
            ip_address=ip_address,
            reason='high_requests',
            request_count=request_count,
            details={
                'requests_in_1h': request_count,
                'threshold': REQUEST_THRESHOLD_PER_HOUR,
                'detection_method': 'excessive_requests'
            }
        )


def _check_sensitive_paths(recent_logs):
    """
    Check for access attempts to sensitive paths.

    Args:
        recent_logs: QuerySet of recent RequestLog entries.
    """
    # Find IPs accessing sensitive paths
    sensitive_access = recent_logs.filter(
        path__in=SENSITIVE_PATHS
    ).values('ip_address').annotate(
        count=Count('id')
    )

    for ip_data in sensitive_access:
        ip_address = ip_data['ip_address']
        access_count = ip_data['count']

        # Skip localhost/private IPs
        if _is_private_ip(ip_address):
            continue

        # Skip if already flagged for this
        if SuspiciousIP.objects.filter(
            ip_address=ip_address,
            reason__in=['admin_access', 'login_access'],
            detected_at__gte=now() - timedelta(hours=1)
        ).exists():
            continue

        # Determine the reason based on paths
        reason = 'pattern_match'
        if any('/admin' in path for path in SENSITIVE_PATHS):
            for log in recent_logs.filter(ip_address=ip_address, path__startswith='/admin'):
                reason = 'admin_access'
                break

        if any('/login' in path for path in SENSITIVE_PATHS):
            for log in recent_logs.filter(ip_address=ip_address, path__startswith='/login'):
                reason = 'login_access'
                break

        logger.warning(
            f"Anomaly detected: IP {ip_address} accessed sensitive paths "
            f"({access_count} times) - Reason: {reason}"
        )

        # Create suspicious IP record
        SuspiciousIP.objects.create(
            ip_address=ip_address,
            reason=reason,
            request_count=access_count,
            details={
                'sensitive_paths_accessed': SENSITIVE_PATHS,
                'access_count': access_count,
                'detection_method': 'sensitive_path_access'
            }
        )


def _is_private_ip(ip_address):
    """
    Check if an IP address is private/local.

    Args:
        ip_address (str): The IP address to check.

    Returns:
        bool: True if the IP is private/local, False otherwise.
    """
    private_ranges = [
        '127.0.0.1',
        '127.',
        '192.168.',
        '10.',
        '172.16.',
        '172.17.',
        '172.18.',
        '172.19.',
        '172.20.',
        '172.21.',
        '172.22.',
        '172.23.',
        '172.24.',
        '172.25.',
        '172.26.',
        '172.27.',
        '172.28.',
        '172.29.',
        '172.30.',
        '172.31.',
        '::1',
        'localhost',
    ]

    return any(ip_address.startswith(prefix) for prefix in private_ranges)
