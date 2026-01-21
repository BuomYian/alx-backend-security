"""
Django Admin Configuration for IP Tracking
"""

from django.contrib import admin
from .models import RequestLog


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    """Admin interface for RequestLog model."""

    list_display = ('ip_address', 'timestamp', 'path')
    list_filter = ('timestamp', 'path')
    search_fields = ('ip_address', 'path')
    readonly_fields = ('ip_address', 'timestamp', 'path')
    ordering = ('-timestamp',)

    fieldsets = (
        ('Request Information', {
            'fields': ('ip_address', 'path', 'timestamp')
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation of logs through admin."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion of logs for data management."""
        return True

    def has_change_permission(self, request, obj=None):
        """Prevent editing of logs."""
        return False
