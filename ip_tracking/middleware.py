"""
IP Tracking Middleware

This module implements middleware to log IP addresses, timestamps,
and request paths for all incoming requests.
"""

import logging
from django.utils.timezone import now
from django.http import HttpResponseForbidden
from .models import RequestLog, BlockedIP
from .geolocation import get_geolocation

logger = logging.getLogger(__name__)


class IPTrackingMiddleware:
    """
    Middleware to log IP addresses and request metadata.

    This middleware captures the client's IP address, request timestamp,
    and requested path, storing them in the RequestLog model for auditing
    and analysis purposes.
    """

    def __init__(self, get_response):
        """
        Initialize the middleware.

        Args:
            get_response: The next middleware or view callable.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Process the incoming request and log IP information.

        Args:
            request: The Django request object.

        Returns:
            403 Forbidden if IP is blacklisted, otherwise the response.
        """
        # Get the client's IP address
        ip_address = self.get_client_ip(request)

        # Check if IP is blacklisted
        if BlockedIP.objects.filter(ip_address=ip_address).exists():
            logger.warning(
                f"Blocked request from blacklisted IP: {ip_address}")
            return HttpResponseForbidden(
                "Access denied: Your IP address has been blocked."
            )

        # Get the request path
        request_path = request.path

        # Get geolocation data (with 24-hour caching)
        geolocation = get_geolocation(ip_address)
        country = geolocation.get('country', 'Unknown')
        city = geolocation.get('city', 'Unknown')

        # Log the request details
        try:
            RequestLog.objects.create(
                ip_address=ip_address,
                timestamp=now(),
                path=request_path,
                country=country,
                city=city
            )
        except Exception as e:
            logger.error(
                f"Failed to log request from IP {ip_address}: {str(e)}")

        # Call the next middleware or view
        response = self.get_response(request)

        return response

    @staticmethod
    def get_client_ip(request):
        """
        Extract the client's IP address from the request.

        Handles cases where the client is behind a proxy by checking
        the X-Forwarded-For header first.

        Args:
            request: The Django request object.

        Returns:
            The client's IP address as a string.
        """
        # Check for IP from a proxy
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP in the chain (the original client)
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            # Fall back to the direct connection IP
            ip_address = request.META.get('REMOTE_ADDR', 'unknown')

        return ip_address
