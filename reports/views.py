from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from reports.models import ResearchReport
from reports.pgvector import search_reports_with_pgvector
from reports.search import cosine_similarity, generate_embedding
from reports.serializers import (
    ResearchReportSearchSerializer,
    ResearchReportSerializer,
    ResearchReportUpdateSerializer,
)


class ResearchReportListView(generics.ListAPIView):
    serializer_class = ResearchReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ResearchReport.objects.filter(user=self.request.user)


class ResearchReportDetailView(generics.RetrieveAPIView):
    serializer_class = ResearchReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ResearchReport.objects.filter(user=self.request.user)


class ResearchReportOrganizeView(generics.UpdateAPIView):
    serializer_class = ResearchReportUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ResearchReport.objects.filter(user=self.request.user)


class ResearchReportExportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        report = get_object_or_404(ResearchReport, pk=pk, user_id=request.user.id)
        export_format = request.query_params.get('file_format', request.query_params.get('format', 'md')).lower()

        if export_format == 'json':
            serializer = ResearchReportSerializer(report)
            return Response(serializer.data)

        if export_format == 'txt':
            content = report.full_report_text
            content_type = 'text/plain'
            extension = 'txt'
        else:
            content = (
                f'# {report.company_name} Research Report\n\n'
                f'## Company Overview\n{report.company_overview}\n\n'
                f'## Market Position\n{report.market_position}\n\n'
                f'## Financial Health\n{report.financial_health}\n\n'
                f'## Recent Developments\n{report.recent_developments}\n\n'
                f'## Key Risks\n{report.key_risks}\n\n'
                f'## Opportunities\n{report.opportunities}\n\n'
                f'## Overall Sentiment\n{report.overall_sentiment}/10\n'
            )
            if report.analyst_notes.strip():
                content += f'\n## Analyst Notes\n{report.analyst_notes}\n'
            content_type = 'text/markdown'
            extension = 'md'

        response = HttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{report.company_name.lower().replace(" ", "-")}-report.{extension}"'
        return response


class ResearchReportSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('query', '').strip()
        if not query:
            return Response({'detail': 'Query parameter is required.'}, status=400)

        query_embedding = generate_embedding(query)
        pgvector_results = search_reports_with_pgvector(request.user.id, query_embedding)
        if pgvector_results is not None:
            serializer = ResearchReportSearchSerializer(pgvector_results, many=True)
            return Response(serializer.data)

        reports = list(ResearchReport.objects.filter(user=request.user))
        scored_reports = []
        for report in reports:
            report.similarity = cosine_similarity(query_embedding, report.embedding)
            scored_reports.append(report)

        scored_reports.sort(key=lambda item: item.similarity, reverse=True)
        serializer = ResearchReportSearchSerializer(scored_reports[:5], many=True)
        return Response(serializer.data)
