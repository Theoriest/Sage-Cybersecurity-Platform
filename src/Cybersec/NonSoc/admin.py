from django.contrib import admin
from .models import SecurityRequest, UserNotification

@admin.register(SecurityRequest)
class SecurityRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'requester', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('title', 'description', 'requester__username')
    date_hierarchy = 'created_at'


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    date_hierarchy = 'created_at'
