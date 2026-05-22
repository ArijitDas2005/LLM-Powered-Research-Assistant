from django.conf import settings
from django.db import models


class ResearchReport(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports',
    )
    job = models.OneToOneField(
        'research.ResearchJob',
        on_delete=models.CASCADE,
        related_name='report',
    )
    company_name = models.CharField(max_length=255)
    company_overview = models.TextField()
    market_position = models.TextField()
    financial_health = models.TextField()
    recent_developments = models.TextField()
    key_risks = models.TextField()
    opportunities = models.TextField()
    overall_sentiment = models.PositiveSmallIntegerField()
    full_report_text = models.TextField()
    is_bookmarked = models.BooleanField(default=False)
    analyst_notes = models.TextField(blank=True, default='')
    embedding = models.JSONField(default=list, blank=True)
    embedding_vector = models.TextField(blank=True, default='')
    source_payload = models.JSONField(default=dict, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f'{self.company_name} report'
