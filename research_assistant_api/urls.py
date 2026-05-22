"""
URL configuration for research_assistant_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.shortcuts import render
from reports.views import ResearchReportSearchView


def website_home(request):
    return render(request, 'index.html')


def api_root(_request):
    return JsonResponse(
        {
            'name': 'LLM-Powered Research Assistant API',
            'status': 'ok',
            'endpoints': {
                'register': '/api/users/register/',
                'login': '/api/users/login/',
                'me': '/api/users/me/',
                'research_jobs': '/api/research/jobs/',
                'reports': '/api/reports/',
                'search': '/api/search/?query=ai',
            },
        }
    )

urlpatterns = [
    path('', website_home, name='website-home'),
    path('api/health/', api_root, name='api-health'),
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/research/', include('research.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/usage/', include('usage.urls')),
    path('api/search/', ResearchReportSearchView.as_view(), name='global-report-search'),
]
