from django.conf import settings
from django.db.models import Sum
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from reports.models import ResearchReport
from research.models import ResearchJob
from usage.models import UsageLog
from usage.serializers import UsageSummarySerializer


class UsageSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        user.refresh_monthly_usage()
        jobs = ResearchJob.objects.filter(user=user)
        reports = ResearchReport.objects.filter(user=user)
        api_logs = UsageLog.objects.filter(user=user)
        llm_logs = api_logs.filter(usage_type=UsageLog.TYPE_LLM_RESEARCH)
        token_totals = llm_logs.aggregate(
            total_input=Sum('llm_input_tokens'),
            total_output=Sum('llm_output_tokens'),
        )
        recent_companies = list(
            jobs.order_by('-created_at').values_list('company_name', flat=True)[:5]
        )
        reports_remaining = (
            'unlimited'
            if user.subscription_tier == 'pro'
            else max(settings.FREE_TIER_MONTHLY_REPORT_LIMIT - user.reports_this_month, 0)
        )
        payload = {
            'subscription_tier': user.subscription_tier,
            'reports_this_month': user.reports_this_month,
            'reports_remaining': reports_remaining,
            'total_jobs': jobs.count(),
            'completed_jobs': jobs.filter(status=ResearchJob.STATUS_COMPLETED).count(),
            'failed_jobs': jobs.filter(status=ResearchJob.STATUS_FAILED).count(),
            'total_reports': reports.count(),
            'bookmarked_reports': reports.filter(is_bookmarked=True).count(),
            'total_api_calls': api_logs.count(),
            'total_llm_input_tokens': token_totals['total_input'] or 0,
            'total_llm_output_tokens': token_totals['total_output'] or 0,
            'recent_companies': recent_companies,
        }
        serializer = UsageSummarySerializer(payload)
        return Response(serializer.data)
