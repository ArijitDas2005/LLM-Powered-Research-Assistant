from rest_framework import generics, permissions, status
from rest_framework.response import Response

from research.models import ResearchJob
from research.permissions import CanCreateResearchReport
from research.serializers import ResearchJobCreateSerializer, ResearchJobDetailSerializer
from research.tasks import process_research_job


class ResearchJobListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, CanCreateResearchReport]

    def get_queryset(self):
        return ResearchJob.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ResearchJobDetailSerializer
        return ResearchJobCreateSerializer

    def create(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.save(user=user)
        user.increment_report_usage()
        task_result = process_research_job.delay(str(job.id))
        job.celery_task_id = task_result.id or ''
        job.save(update_fields=['celery_task_id', 'updated_at'])
        output = ResearchJobDetailSerializer(job)
        return Response(output.data, status=status.HTTP_201_CREATED)


class ResearchJobDetailView(generics.RetrieveAPIView):
    serializer_class = ResearchJobDetailSerializer
    lookup_field = 'id'
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ResearchJob.objects.filter(user=self.request.user)


class ResearchJobRetryView(generics.GenericAPIView):
    serializer_class = ResearchJobDetailSerializer
    lookup_field = 'id'
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ResearchJob.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        job = self.get_object()
        if job.status != ResearchJob.STATUS_FAILED:
            return Response(
                {'detail': 'Only failed jobs can be retried.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        job.status = ResearchJob.STATUS_PENDING
        job.error_message = ''
        job.started_at = None
        job.completed_at = None
        job.save(update_fields=['status', 'error_message', 'started_at', 'completed_at', 'updated_at'])
        task_result = process_research_job.delay(str(job.id))
        job.celery_task_id = task_result.id or ''
        job.save(update_fields=['celery_task_id', 'updated_at'])
        return Response(ResearchJobDetailSerializer(job).data, status=status.HTTP_200_OK)
