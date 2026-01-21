"""
IP Tracking Views with Rate Limiting.

This module provides views with rate limiting to prevent abuse.
"""

from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit
from django.contrib.auth.decorators import login_required


@ratelimit(key='ip', rate='10/m', method='POST')
@require_http_methods(["POST"])
def login_attempt(request):
    """
    Handle login attempts with rate limiting.

    Authenticated users: 10 requests/minute
    Anonymous users: 5 requests/minute (via IP)

    Args:
        request: The Django request object.

    Returns:
        JsonResponse with login status or 403 if rate limited.
    """
    # This is a demonstration endpoint
    return JsonResponse({
        'status': 'success',
        'message': 'Login attempt processed'
    })


@ratelimit(key='ip', rate='5/m', method='POST')
@require_http_methods(["POST"])
def password_reset(request):
    """
    Handle password reset requests with rate limiting.

    Rate limit: 5 requests/minute per IP

    Args:
        request: The Django request object.

    Returns:
        JsonResponse with reset status or 403 if rate limited.
    """
    return JsonResponse({
        'status': 'success',
        'message': 'Password reset email sent'
    })


@login_required
@ratelimit(key='user', rate='10/m', method='GET')
@require_http_methods(["GET"])
def api_get_logs(request):
    """
    Get user's request logs (authenticated endpoint).

    Rate limit: 10 requests/minute per authenticated user

    Args:
        request: The Django request object.

    Returns:
        JsonResponse with user's recent request logs.
    """
    from .models import RequestLog

    # Get user's IP from request logs
    user_ip = request.META.get(
        'HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
    logs = RequestLog.objects.filter(ip_address=user_ip).values(
        'ip_address', 'timestamp', 'path', 'country', 'city'
    )[:20]  # Last 20 logs

    return JsonResponse({
        'status': 'success',
        'count': logs.count(),
        'logs': list(logs)
    })


def rate_limit_exceeded(request, exception):
    """
    Handle rate limit exceeded errors.

    Args:
        request: The Django request object.
        exception: The rate limit exception.

    Returns:
        JsonResponse with error message and 429 status.
    """
    return JsonResponse({
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.'
    }, status=429)
