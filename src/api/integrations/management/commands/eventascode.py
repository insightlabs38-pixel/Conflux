import json
import sys

import yaml
from django.core.management.base import BaseCommand, CommandError
from events.models import Event

from integrations import eventascode


def _load(path):
    text = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise CommandError(f"Not valid YAML/JSON: {exc}") from exc


class Command(BaseCommand):
    help = "Export, validate, plan or apply a declarative event document (YAML or JSON)."

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["export", "validate", "plan", "apply"])
        parser.add_argument("event", help="Event public id")
        parser.add_argument("file", nargs="?", help="Document path, or - for stdin")
        parser.add_argument("--format", choices=["yaml", "json"], default="yaml")
        parser.add_argument("--prune", action="store_true")
        parser.add_argument("--digest", help="Digest from a reviewed plan (apply)")
        parser.add_argument("--auto-approve", action="store_true")

    def handle(self, *args, action, event, file, format, prune, digest, auto_approve, **options):
        try:
            target = Event.objects.get(public_id=event)
        except (Event.DoesNotExist, ValueError) as exc:
            raise CommandError("Unknown event.") from exc
        if action == "export":
            document = eventascode.export_document(target)
            self.stdout.write(
                json.dumps(document, indent=2, sort_keys=True)
                if format == "json"
                else yaml.safe_dump(document, sort_keys=False, allow_unicode=True)
            )
            return
        if not file:
            raise CommandError("Provide a document file (or - for stdin).")
        document = _load(file)
        if action == "validate":
            errors = eventascode.validate(target, document)
            self.stdout.write(json.dumps({"valid": not errors, "errors": errors}, indent=2))
            if errors:
                raise CommandError("Document is invalid.")
        elif action == "plan":
            report = eventascode.plan(target, document, prune=prune)
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
            if report["errors"]:
                raise CommandError("Plan has errors; nothing would be applied.")
        else:
            if not (digest or auto_approve):
                raise CommandError("Apply needs --digest from a reviewed plan or --auto-approve.")
            try:
                report = eventascode.apply(
                    target,
                    document,
                    expected_digest=digest or eventascode.digest(target),
                    actor=None,
                    prune=prune,
                )
            except eventascode.StaleDigest as exc:
                raise CommandError(f"{exc} Current digest: {exc.current}") from exc
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
            if report["errors"]:
                raise CommandError("Nothing applied; see errors.")
