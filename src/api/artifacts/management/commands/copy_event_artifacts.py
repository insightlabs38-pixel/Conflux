import json
import os

from botocore.exceptions import BotoCoreError, ClientError
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from events.models import Event

from artifacts.portability import copy_event_artifacts
from artifacts.storage import S3Storage


class Command(BaseCommand):
    help = "Preview or copy stored event artifacts to another S3-compatible backend"

    def add_arguments(self, parser):
        parser.add_argument("event")
        parser.add_argument("--destination-endpoint", required=True)
        parser.add_argument("--destination-bucket", required=True)
        parser.add_argument("--execute", action="store_true")

    def handle(self, *args, **options):
        access_key = os.environ.get("CONFLUX_COPY_DEST_ACCESS_KEY")
        secret_key = os.environ.get("CONFLUX_COPY_DEST_SECRET_KEY")
        if not access_key or not secret_key:
            raise CommandError("Set CONFLUX_COPY_DEST_ACCESS_KEY and CONFLUX_COPY_DEST_SECRET_KEY")
        try:
            event = Event.objects.get(public_id=options["event"])
            source = S3Storage()
            destination = S3Storage(
                endpoint=options["destination_endpoint"],
                public_endpoint=options["destination_endpoint"],
                bucket=options["destination_bucket"],
                access_key=access_key,
                secret_key=secret_key,
            )
            report = copy_event_artifacts(event, source, destination, execute=options["execute"])
        except Event.DoesNotExist as exc:
            raise CommandError("Event not found") from exc
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        except (ValidationError, BotoCoreError, ClientError, OSError) as exc:
            raise CommandError(
                f"Artifact copy failed ({type(exc).__name__}); no cutover performed"
            ) from exc
        self.stdout.write(json.dumps(report, sort_keys=True))
