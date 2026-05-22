from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from reports.models import ResearchReport
from research.models import ResearchJob
from research.services import validate_report_payload
from research.tasks import process_research_job
from usage.models import UsageLog


User = get_user_model()


@pytest.mark.django_db
def test_protected_endpoints_reject_unauthenticated_requests():
    client = APIClient()

    endpoints = [
        ('get', '/api/users/me/'),
        ('get', '/api/research/jobs/'),
        ('get', '/api/research/jobs/00000000-0000-0000-0000-000000000000/'),
        ('post', '/api/research/jobs/00000000-0000-0000-0000-000000000000/retry/'),
        ('get', '/api/reports/'),
        ('get', '/api/reports/1/'),
        ('patch', '/api/reports/1/organize/'),
        ('get', '/api/reports/1/export/'),
        ('get', '/api/reports/search/?query=ai'),
        ('get', '/api/search/?query=ai'),
        ('get', '/api/usage/summary/'),
    ]

    for method, path in endpoints:
        if method == 'patch':
            response = getattr(client, method)(path, {}, format='json')
        else:
            response = getattr(client, method)(path)
        assert response.status_code == 401


@pytest.mark.django_db
@patch('research.views.process_research_job.delay')
def test_research_job_is_created_and_queued(mock_delay):
    mock_delay.return_value.id = 'celery-task-123'
    user = User.objects.create_user(username='alice', password='StrongPass123!')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post('/api/research/jobs/', {'company_name': 'Tesla'}, format='json')

    assert response.status_code == 201
    job = ResearchJob.objects.get(company_name='Tesla')
    assert job.status == ResearchJob.STATUS_PENDING
    assert job.celery_task_id == 'celery-task-123'
    user.refresh_from_db()
    assert user.reports_this_month == 1


@pytest.mark.django_db
@patch('research.tasks.create_report_from_research')
@patch('research.tasks.generate_report_with_claude')
@patch('research.tasks.build_research_context')
def test_celery_task_updates_job_status(
    mock_build_context,
    mock_generate_report,
    mock_create_report,
):
    user = User.objects.create_user(username='bob', password='StrongPass123!')
    job = ResearchJob.objects.create(user=user, company_name='OpenAI')
    mock_build_context.return_value = {'company_name': 'OpenAI'}
    mock_generate_report.return_value = (
        {
            'company_overview': 'Overview',
            'market_position': 'Market',
            'financial_health': 'Financial',
            'recent_developments': 'Developments',
            'key_risks': 'Risks',
            'opportunities': 'Opportunities',
            'overall_sentiment': 8,
        },
        {'input_tokens': 100, 'output_tokens': 200},
    )

    process_research_job.run(str(job.id))

    job.refresh_from_db()
    assert job.status == ResearchJob.STATUS_COMPLETED
    assert job.completed_at is not None
    mock_create_report.assert_called_once()


@pytest.mark.django_db
def test_free_tier_limit_is_enforced(settings):
    settings.FREE_TIER_MONTHLY_REPORT_LIMIT = 1
    user = User.objects.create_user(
        username='quota-user',
        password='StrongPass123!',
        reports_this_month=1,
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post('/api/research/jobs/', {'company_name': 'NVIDIA'}, format='json')

    assert response.status_code == 403


@pytest.mark.django_db
def test_research_job_list_and_detail_are_scoped_to_owner():
    owner = User.objects.create_user(username='owner', password='StrongPass123!')
    other = User.objects.create_user(username='other', password='StrongPass123!')
    owner_job = ResearchJob.objects.create(user=owner, company_name='Anthropic')
    ResearchJob.objects.create(user=other, company_name='Stripe')
    client = APIClient()
    client.force_authenticate(user=owner)

    list_response = client.get('/api/research/jobs/')
    detail_response = client.get(f'/api/research/jobs/{owner_job.id}/')
    forbidden_detail = client.get(f'/api/research/jobs/{ResearchJob.objects.get(user=other).id}/')

    assert list_response.status_code == 200
    assert len(list_response.data) == 1
    assert list_response.data[0]['company_name'] == 'Anthropic'
    assert detail_response.status_code == 200
    assert detail_response.data['company_name'] == 'Anthropic'
    assert forbidden_detail.status_code == 404


@pytest.mark.django_db
@patch('research.views.process_research_job.delay')
def test_failed_job_can_be_retried(mock_delay):
    mock_delay.return_value.id = 'retry-task-456'
    user = User.objects.create_user(username='retry-user', password='StrongPass123!')
    job = ResearchJob.objects.create(
        user=user,
        company_name='Tesla',
        status=ResearchJob.STATUS_FAILED,
        error_message='Claude outage',
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(f'/api/research/jobs/{job.id}/retry/')

    assert response.status_code == 200
    job.refresh_from_db()
    assert job.status == ResearchJob.STATUS_PENDING
    assert job.error_message == ''
    assert job.celery_task_id == 'retry-task-456'


@pytest.mark.django_db
def test_report_list_detail_and_search_work_for_authenticated_user():
    user = User.objects.create_user(username='searcher', password='StrongPass123!')
    other = User.objects.create_user(username='outsider', password='StrongPass123!')
    job = ResearchJob.objects.create(
        user=user,
        company_name='Anthropic',
        status=ResearchJob.STATUS_COMPLETED,
    )
    other_job = ResearchJob.objects.create(
        user=other,
        company_name='Databricks',
        status=ResearchJob.STATUS_COMPLETED,
    )
    report = ResearchReport.objects.create(
        user=user,
        job=job,
        company_name='Anthropic',
        company_overview='AI safety company.',
        market_position='Strong in frontier models.',
        financial_health='Private company.',
        recent_developments='New model launched.',
        key_risks='Competition.',
        opportunities='Enterprise adoption.',
        overall_sentiment=9,
        full_report_text='AI growth and enterprise adoption',
        embedding=[1.0, 0.0, 0.0],
        source_payload={},
    )
    ResearchReport.objects.create(
        user=other,
        job=other_job,
        company_name='Databricks',
        company_overview='Data company.',
        market_position='Competes in AI data tools.',
        financial_health='Private company.',
        recent_developments='Raised funding.',
        key_risks='Competition.',
        opportunities='AI infrastructure.',
        overall_sentiment=7,
        full_report_text='data and infrastructure',
        embedding=[0.0, 1.0, 0.0],
        source_payload={},
    )
    client = APIClient()
    client.force_authenticate(user=user)

    list_response = client.get('/api/reports/')
    detail_response = client.get(f'/api/reports/{report.id}/')
    with patch('reports.views.generate_embedding', return_value=[1.0, 0.0, 0.0]):
        search_response = client.get('/api/reports/search/?query=ai growth')
        global_search_response = client.get('/api/search/?query=ai growth')

    assert list_response.status_code == 200
    assert len(list_response.data) == 1
    assert detail_response.status_code == 200
    assert detail_response.data['company_name'] == 'Anthropic'
    assert search_response.status_code == 200
    assert global_search_response.status_code == 200
    assert search_response.data[0]['company_name'] == 'Anthropic'
    assert global_search_response.data[0]['company_name'] == 'Anthropic'


@pytest.mark.django_db
def test_report_can_be_bookmarked_and_noted_and_exported():
    user = User.objects.create_user(username='report-user', password='StrongPass123!')
    job = ResearchJob.objects.create(
        user=user,
        company_name='Anthropic',
        status=ResearchJob.STATUS_COMPLETED,
    )
    report = ResearchReport.objects.create(
        user=user,
        job=job,
        company_name='Anthropic',
        company_overview='AI safety company.',
        market_position='Strong in frontier models.',
        financial_health='Private company.',
        recent_developments='New model launched.',
        key_risks='Competition.',
        opportunities='Enterprise adoption.',
        overall_sentiment=9,
        full_report_text='AI growth and enterprise adoption',
        embedding=[1.0, 0.0, 0.0],
        source_payload={},
    )
    client = APIClient()
    client.force_authenticate(user=user)

    organize_response = client.patch(
        f'/api/reports/{report.id}/organize/',
        {'is_bookmarked': True, 'analyst_notes': 'High-conviction AI name.'},
        format='json',
    )
    export_response = client.get(f'/api/reports/{report.id}/export/?file_format=md')

    assert organize_response.status_code == 200
    report.refresh_from_db()
    assert report.is_bookmarked is True
    assert report.analyst_notes == 'High-conviction AI name.'
    assert export_response.status_code == 200
    assert 'Anthropic Research Report' in export_response.content.decode()


@pytest.mark.django_db
def test_usage_logging_records_authenticated_api_calls():
    user = User.objects.create_user(username='logger', password='StrongPass123!')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/users/me/')

    assert response.status_code == 200
    assert UsageLog.objects.filter(user=user, endpoint='/api/users/me/').exists()


@pytest.mark.django_db
def test_usage_summary_returns_dashboard_metrics():
    user = User.objects.create_user(username='metrics-user', password='StrongPass123!')
    job = ResearchJob.objects.create(
        user=user,
        company_name='NVIDIA',
        status=ResearchJob.STATUS_COMPLETED,
    )
    report = ResearchReport.objects.create(
        user=user,
        job=job,
        company_name='NVIDIA',
        company_overview='Chipmaker.',
        market_position='Leader.',
        financial_health='Strong.',
        recent_developments='AI demand.',
        key_risks='Valuation.',
        opportunities='Growth.',
        overall_sentiment=8,
        full_report_text='chips and ai',
        embedding=[1.0, 0.0, 0.0],
        source_payload={},
        is_bookmarked=True,
    )
    UsageLog.objects.create(
        user=user,
        report=report,
        usage_type=UsageLog.TYPE_LLM_RESEARCH,
        endpoint='/api/research/jobs/',
        method='POST',
        status_code=200,
        llm_input_tokens=123,
        llm_output_tokens=456,
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/usage/summary/')

    assert response.status_code == 200
    assert response.data['total_jobs'] == 1
    assert response.data['total_reports'] == 1
    assert response.data['bookmarked_reports'] == 1
    assert response.data['total_llm_input_tokens'] == 123
    assert response.data['total_llm_output_tokens'] == 456


def test_validate_report_payload_rejects_incomplete_llm_json():
    with pytest.raises(ValueError):
        validate_report_payload({'company_overview': 'Only one field'})
