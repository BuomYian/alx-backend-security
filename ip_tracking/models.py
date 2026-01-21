"""
IP Tracking Models

This module defines models for storing and managing IP tracking data.
"""

from django.db import models
from django.core.validators import validate_ipv46_address
from django.core.cache import cache


class RequestLog(models.Model):
    """
    Model to store IP address logs for every incoming request.

    Attributes:
        ip_address (str): The client's IP address (IPv4 or IPv6).
        timestamp (datetime): The time the request was received.
        path (str): The URL path that was requested.
        country (str): The country where the request originated.
        city (str): The city where the request originated.
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

    country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="The country where the request originated",
        db_index=True
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="The city where the request originated",
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


class BlockedIP(models.Model):
    """
    Model to store blacklisted IP addresses.

    Attributes:
        ip_address (str): The blacklisted IP address (IPv4 or IPv6).
        blocked_at (datetime): The timestamp when the IP was blocked.
        reason (str): The reason for blocking the IP.
    """

    ip_address = models.CharField(
        max_length=45,
        unique=True,
        validators=[validate_ipv46_address],
        help_text="The IP address to block (IPv4 or IPv6)",
        db_index=True
    )

    blocked_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the IP was added to the blacklist"
    )

    reason = models.TextField(
        blank=True,
        help_text="Reason for blocking this IP"
    )

    class Meta:
        """
        Metadata for the BlockedIP model.
        """
        verbose_name = "Blocked IP"
        verbose_name_plural = "Blocked IPs"
        ordering = ['-blocked_at']

    def __str__(self):
        """String representation of the blocked IP."""
        return f"Blocked: {self.ip_address} ({self.blocked_at.strftime('%Y-%m-%d %H:%M')})"


class SuspiciousIP(models.Model):
    """
    Model to flag and store suspicious IP addresses.

    Attributes:
        ip_address (str): The suspicious IP address (IPv4 or IPv6).
        reason (str): The reason for flagging the IP as suspicious.
        detected_at (datetime): When the suspicious activity was detected.
        request_count (int): Number of requests in the suspicious time window.
        is_investigated (bool): Whether the anomaly has been investigated.
    """

    REASON_CHOICES = [
        ('high_requests', 'High number of requests'),
        ('admin_access', 'Attempted admin access'),
        ('login_access', 'Attempted login access'),
        ('pattern_match', 'Suspicious pattern detected'),
        ('other', 'Other suspicious activity'),
    ]

    ip_address = models.CharField(
        max_length=45,
        validators=[validate_ipv46_address],
        help_text="The suspicious IP address",
        db_index=True
    )

    reason = models.CharField(
        max_length=20,
        choices=REASON_CHOICES,
        default='other',
        help_text="Reason for flagging as suspicious"
    )

    detected_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the suspicious activity was detected",
        db_index=True
    )

    request_count = models.IntegerField(
        default=0,
        help_text="Number of requests in the suspicious time window"
    )

    is_investigated = models.BooleanField(
        default=False,
        help_text="Whether the anomaly has been investigated",
        db_index=True
    )

    details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional details about the anomaly"
    )

    class Meta:
        """
        Metadata for the SuspiciousIP model.
        """
        verbose_name = "Suspicious IP"
        verbose_name_plural = "Suspicious IPs"
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['ip_address', '-detected_at']),
            models.Index(fields=['is_investigated', '-detected_at']),
        ]

    def __str__(self):
        """String representation of the suspicious IP."""
        return f"Suspicious: {self.ip_address} ({self.get_reason_display()})"
