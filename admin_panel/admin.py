from django.contrib import admin
from .models import AdminRole, AdminUser, AuditLog, LoginAttempt, PasswordResetToken, SessionSecurity

@admin.register(AdminRole)
class AdminRoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['permissions']

@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'employee_id', 'department', 'is_active_admin', 'last_login_ip']
    list_filter = ['role', 'is_active_admin', 'department']
    search_fields = ['user__username', 'user__email', 'employee_id']
    readonly_fields = ['last_login_ip', 'failed_login_attempts', 'locked_until']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'object_repr', 'timestamp', 'ip_address']
    list_filter = ['action', 'timestamp', 'content_type']
    search_fields = ['user__username', 'description', 'object_repr']
    readonly_fields = ['id', 'timestamp']
    date_hierarchy = 'timestamp'

@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['username', 'ip_address', 'success', 'failure_reason', 'timestamp']
    list_filter = ['success', 'timestamp']
    search_fields = ['username', 'ip_address']
    readonly_fields = ['timestamp']

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'created_at', 'expires_at', 'used']
    list_filter = ['used', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['token', 'created_at']

@admin.register(SessionSecurity)
class SessionSecurityAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_key', 'ip_address', 'last_activity', 'expires_at']
    list_filter = ['last_activity', 'expires_at']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['session_key', 'created_at']