from rest_framework import serializers


class UsageSummarySerializer(serializers.Serializer):
    subscription_tier = serializers.CharField()
    reports_this_month = serializers.IntegerField()
    reports_remaining = serializers.CharField()
    total_jobs = serializers.IntegerField()
    completed_jobs = serializers.IntegerField()
    failed_jobs = serializers.IntegerField()
    total_reports = serializers.IntegerField()
    bookmarked_reports = serializers.IntegerField()
    total_api_calls = serializers.IntegerField()
    total_llm_input_tokens = serializers.IntegerField()
    total_llm_output_tokens = serializers.IntegerField()
    recent_companies = serializers.ListField(child=serializers.CharField())
