from celery import shared_task

from . import jobs


@shared_task(name="core.tasks.run_job")
def run_job(public_id):
    """Run one job; a duplicate delivery of an already started job does nothing."""
    job = jobs.run(public_id)
    return job.status if job else "missing"


@shared_task(name="core.tasks.sweep_jobs")
def sweep_jobs():
    return jobs.sweep()
