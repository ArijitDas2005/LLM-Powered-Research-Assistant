from django.urls import path

from reports.views import (
    ResearchReportDetailView,
    ResearchReportExportView,
    ResearchReportListView,
    ResearchReportOrganizeView,
    ResearchReportSearchView,
)


urlpatterns = [
    path('', ResearchReportListView.as_view(), name='report-list'),
    path('search/', ResearchReportSearchView.as_view(), name='report-search'),
    path('<int:pk>/organize/', ResearchReportOrganizeView.as_view(), name='report-organize'),
    path('<int:pk>/export/', ResearchReportExportView.as_view(), name='report-export'),
    path('<int:pk>/', ResearchReportDetailView.as_view(), name='report-detail'),
]
