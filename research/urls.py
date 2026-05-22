from django.urls import path

from research.views import ResearchJobDetailView, ResearchJobListCreateView, ResearchJobRetryView


urlpatterns = [
    path('jobs/', ResearchJobListCreateView.as_view(), name='research-job-list-create'),
    path('jobs/<uuid:id>/', ResearchJobDetailView.as_view(), name='research-job-detail'),
    path('jobs/<uuid:id>/retry/', ResearchJobRetryView.as_view(), name='research-job-retry'),
]
