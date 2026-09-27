from celery import shared_task

from .webhooks import deliver_pending, stage_deliveries


@shared_task
def process_webhooks():
    return {"staged": stage_deliveries(), "attempted": deliver_pending()}
