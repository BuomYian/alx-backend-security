"""
URL configuration for the IP Tracking backend project.
"""

from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from ip_tracking import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),

    # Rate-limited endpoints
    path('api/login/', views.login_attempt, name='login_attempt'),
    path('api/password-reset/', views.password_reset, name='password_reset'),
    path('api/logs/', views.api_get_logs, name='api_logs'),]
