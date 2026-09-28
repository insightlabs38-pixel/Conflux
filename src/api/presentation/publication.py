from django.utils import timezone

from .models import PublicationSchedule, PublicationSurface


def schedule_is_open(schedule, now):
    return schedule.opens_at <= now and (schedule.closes_at is None or now < schedule.closes_at)


def publication_visible(event, surface, *, now=None):
    schedule = PublicationSchedule.objects.filter(event=event, surface=surface).first()
    if schedule is None:
        return surface != PublicationSurface.FINALISTS
    return schedule_is_open(schedule, now if now is not None else timezone.now())
