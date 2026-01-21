"""
IP Tracking App Configuration
"""

from django.apps import AppConfig


class IpTrackingConfig(AppConfig):
    """Configuration for the IP Tracking app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ip_tracking'
    verbose_name = 'IP Tracking'
