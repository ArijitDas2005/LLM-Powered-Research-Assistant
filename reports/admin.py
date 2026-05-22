from django.contrib import admin

from reports.models import ResearchReport


@admin.register(ResearchReport)
class ResearchReportAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'overall_sentiment', 'generated_at')
    search_fields = ('company_name', 'user__username')
