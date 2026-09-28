import json

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from events.models import Event

from presentation.conformance import build_conformance_report


class Command(BaseCommand):
    help = "Print the accessibility conformance evidence report for one event as JSON."

    def add_arguments(self, parser):
        parser.add_argument("event_public_id")

    def handle(self, *args, event_public_id, **options):
        try:
            event = Event.objects.get(public_id=event_public_id)
        except (Event.DoesNotExist, ValueError) as exc:
            raise CommandError("Unknown event.") from exc
        report = build_conformance_report(event, now=timezone.now())
        self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
