from celery import shared_task

from .reminders import dispatch_due_reminders


@shared_task(name="communications.tasks.dispatch_due_reminders")
def dispatch_due_reminders_task():
    return dispatch_due_reminders()
