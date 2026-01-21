"""
Django Admin Configuration for IP Tracking
"""

from django.contrib import admin
from .models import RequestLog, BlockedIP, SuspiciousIP


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    """Admin interface for RequestLog model."""

    list_display = ('ip_address', 'timestamp', 'path', 'country', 'city')
    list_filter = ('timestamp', 'path', 'country', 'city')
    search_fields = ('ip_address', 'path', 'country', 'city')
    readonly_fields = ('ip_address', 'timestamp', 'path', 'country', 'city')
    ordering = ('-timestamp',)

    fieldsets = (
        ('Request Information', {
            'fields': ('ip_address', 'path', 'timestamp')
        }),
        ('Geolocation', {
            'fields': ('country', 'city')
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation of logs through admin."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion of logs for data management."""
        return True


@admin.register(BlockedIP)
class BlockedIPAdmin(admin.ModelAdmin):
    """Admin interface for BlockedIP model."""

    list_display = ('ip_address', 'blocked_at', 'reason')
    list_filter = ('blocked_at',)
    search_fields = ('ip_address',)
    readonly_fields = ('blocked_at',)
    ordering = ('-blocked_at',)

    fieldsets = (
        ('IP Information', {
            'fields': ('ip_address', 'blocked_at')
        }),
        ('Details', {
            'fields': ('reason',)
        }),
    )

    def has_add_permission(self, request):
        """Allow adding IPs through admin and management command."""
        return True

    def has_change_permission(self, request, obj=None):
        """Prevent editing of logs."""
        return False


@admin.register(SuspiciousIP)
class SuspiciousIPAdmin(admin.ModelAdmin):
    """Admin interface for SuspiciousIP model."""

    list_display = ('ip_address', 'reason', 'detected_at',
                    'request_count', 'is_investigated')
    list_filter = ('reason', 'detected_at', 'is_investigated')
    search_fields = ('ip_address',)
    readonly_fields = ('ip_address', 'detected_at',
                       'reason', 'request_count', 'details')
    ordering = ('-detected_at',)

    fieldsets = (
        ('IP Information', {
            'fields': ('ip_address', 'detected_at')
        }),
        ('Anomaly Details', {
            'fields': ('reason', 'request_count', 'details')
        }),
        ('Investigation Status', {
            'fields': ('is_investigated',)
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation, only via Celery task."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion for data management."""
        return True

    actions = ['mark_investigated']

    def mark_investigated(self, request, queryset):
        """Mark selected anomalies as investigated."""
        updated = queryset.update(is_investigated=True)
        self.message_user(
            request, f'{updated} anomalies marked as investigated.')

    mark_investigated.short_description = 'Mark selected as investigated'
