from django.contrib import admin

from usage.models import UsageLog


@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = ('endpoint', 'user', 'usage_type', 'status_code', 'created_at')
    list_filter = ('usage_type', 'status_code', 'created_at')
    search_fields = ('endpoint', 'user__username')
