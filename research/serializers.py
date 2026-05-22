from rest_framework import serializers

from research.models import ResearchJob


class ResearchJobCreateSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(max_length=255, allow_blank=False, trim_whitespace=True)

    class Meta:
        model = ResearchJob
        fields = ('id', 'company_name', 'status', 'created_at')
        read_only_fields = ('id', 'status', 'created_at')

    def validate_company_name(self, value):
        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError('Company name is required.')
        return normalized


class ResearchJobDetailSerializer(serializers.ModelSerializer):
    report_id = serializers.IntegerField(source='report.id', read_only=True)

    class Meta:
        model = ResearchJob
        fields = (
            'id',
            'company_name',
            'status',
            'error_message',
            'celery_task_id',
            'created_at',
            'updated_at',
            'started_at',
            'completed_at',
            'report_id',
        )
        read_only_fields = fields
