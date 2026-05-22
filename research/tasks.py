from celery import shared_task
from django.utils import timezone

from research.models import ResearchJob
from research.services import (
    build_research_context,
    create_report_from_research,
    generate_report_with_claude,
)


@shared_task(bind=True)
def process_research_job(self, job_id):
    job = ResearchJob.objects.select_related('user').get(id=job_id)
    job.status = ResearchJob.STATUS_PROCESSING
    job.started_at = timezone.now()
    task_id = getattr(getattr(self, 'request', None), 'id', None)
    job.celery_task_id = task_id or job.celery_task_id
    job.error_message = ''
    job.save(update_fields=['status', 'started_at', 'celery_task_id', 'error_message', 'updated_at'])

    try:
        context = build_research_context(job.company_name)
        report_json, token_usage = generate_report_with_claude(job.company_name, context)
        create_report_from_research(job, report_json, context, token_usage)
        job.raw_context = context
        job.status = ResearchJob.STATUS_COMPLETED
        job.completed_at = timezone.now()
        job.save(update_fields=['raw_context', 'status', 'completed_at', 'updated_at'])
    except Exception as exc:
        job.status = ResearchJob.STATUS_FAILED
        job.error_message = str(exc)
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'error_message', 'completed_at', 'updated_at'])
        raise
