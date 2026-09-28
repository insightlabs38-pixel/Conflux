from django.core.management.base import BaseCommand
from django.utils import timezone
from events.models import Event

from integrations.privacy import enforce_retention


class Command(BaseCommand):
    help = "Preview (default) or apply per-event retention policies that are due."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, apply=False, **options):
        now = timezone.now()
        events = Event.objects.filter(retention_policy__isnull=False).order_by("pk")
        for event in events.select_related("workspace"):
            report = enforce_retention(event, now, apply=apply)
            self.stdout.write(f"{event.public_id} {report}")
