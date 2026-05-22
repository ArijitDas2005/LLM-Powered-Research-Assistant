from django.conf import settings
from django.db import models


class UsageLog(models.Model):
    TYPE_API_REQUEST = 'api_request'
    TYPE_LLM_RESEARCH = 'llm_research'

    TYPE_CHOICES = [
        (TYPE_API_REQUEST, 'API Request'),
        (TYPE_LLM_RESEARCH, 'LLM Research'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='usage_logs',
        null=True,
        blank=True,
    )
    report = models.ForeignKey(
        'reports.ResearchReport',
        on_delete=models.SET_NULL,
        related_name='usage_logs',
        null=True,
        blank=True,
    )
    usage_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_API_REQUEST)
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10, blank=True)
    status_code = models.PositiveSmallIntegerField(default=200)
    llm_input_tokens = models.PositiveIntegerField(default=0)
    llm_output_tokens = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user_id or "anon"} {self.endpoint}'
