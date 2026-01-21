"""
IP Tracking Models

This module defines models for storing and managing IP tracking data.
"""

from django.db import models
from django.core.validators import validate_ipv46_address


class RequestLog(models.Model):
    """
    Model to store IP address logs for every incoming request.

    Attributes:
        ip_address (str): The client's IP address (IPv4 or IPv6).
        timestamp (datetime): The time the request was received.
        path (str): The URL path that was requested.
    """

    ip_address = models.CharField(
        max_length=45,
        validators=[validate_ipv46_address],
        help_text="The client's IP address (IPv4 or IPv6)",
        db_index=True
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="The time the request was received",
        db_index=True
    )

    path = models.CharField(
        max_length=2048,
        help_text="The URL path that was requested",
        db_index=True
    )

    class Meta:
        """
        Metadata for the RequestLog model.
        """
        verbose_name = "Request Log"
        verbose_name_plural = "Request Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['ip_address', '-timestamp']),
            models.Index(fields=['path', '-timestamp']),
        ]

    def __str__(self):
        """String representation of the request log."""
        return f"{self.ip_address} - {self.timestamp} - {self.path}"

    @classmethod
    def get_requests_by_ip(cls, ip_address, limit=100):
        """
        Retrieve recent requests from a specific IP address.

        Args:
            ip_address (str): The IP address to query.
            limit (int): Maximum number of recent requests to return.

        Returns:
            QuerySet: Recent request logs from the specified IP.
        """
        return cls.objects.filter(ip_address=ip_address)[:limit]

    @classmethod
    def get_requests_by_path(cls, path, limit=100):
        """
        Retrieve recent requests to a specific path.

        Args:
            path (str): The request path to query.
            limit (int): Maximum number of recent requests to return.

        Returns:
            QuerySet: Recent request logs for the specified path.
        """
        return cls.objects.filter(path=path)[:limit]
