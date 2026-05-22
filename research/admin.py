from django.contrib import admin

from research.models import ResearchJob


@admin.register(ResearchJob)
class ResearchJobAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'status', 'created_at', 'completed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('company_name', 'user__username')
