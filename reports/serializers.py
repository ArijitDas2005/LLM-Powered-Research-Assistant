from rest_framework import serializers

from reports.models import ResearchReport


class ResearchReportSerializer(serializers.ModelSerializer):
    job_id = serializers.UUIDField(source='job.id', read_only=True)

    class Meta:
        model = ResearchReport
        fields = (
            'id',
            'job_id',
            'company_name',
            'company_overview',
            'market_position',
            'financial_health',
            'recent_developments',
            'key_risks',
            'opportunities',
            'overall_sentiment',
            'full_report_text',
            'is_bookmarked',
            'analyst_notes',
            'source_payload',
            'generated_at',
        )
        read_only_fields = fields


class ResearchReportSearchSerializer(serializers.ModelSerializer):
    similarity = serializers.FloatField(read_only=True)

    class Meta:
        model = ResearchReport
        fields = ('id', 'company_name', 'overall_sentiment', 'generated_at', 'similarity')
        read_only_fields = fields


class ResearchReportUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResearchReport
        fields = ('is_bookmarked', 'analyst_notes')
