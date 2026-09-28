import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime

from integrations.demo_scenarios import CHECKPOINTS, generate_demo_event, purge_demo_scenario
from integrations.models import DemoScenario


class Command(BaseCommand):
    help = "Create, list or purge deterministic synthetic demo workspaces."

    def add_arguments(self, parser):
        commands = parser.add_subparsers(dest="action", required=True)
        create = commands.add_parser("create")
        create.add_argument("--scenario", default="hackathon")
        create.add_argument("--seed", type=int, default=1)
        create.add_argument("--participants", type=int, default=8)
        create.add_argument("--judges", type=int, default=4)
        create.add_argument(
            "--password", help="Shared login password; accounts are locked without."
        )
        create.add_argument("--public", action="store_true")
        create.add_argument(
            "--checkpoint",
            choices=CHECKPOINTS,
            default="published",
            help="Lifecycle state to stop at (default: published, the closed archive).",
        )
        create.add_argument(
            "--live",
            type=int,
            help="Participants left approved but unsubmitted (default 2 before `published`).",
        )
        create.add_argument("--at", help="Timezone-aware ISO timestamp for the synthetic clock.")
        commands.add_parser("list")
        commands.add_parser("purge").add_argument("slug")

    def handle(self, *args, action, **options):
        try:
            if action == "list":
                for row in DemoScenario.objects.select_related("workspace").order_by("pk"):
                    self.stdout.write(f"{row.workspace.slug} {row.participants}p/{row.judges}j")
            elif action == "purge":
                purge_demo_scenario(options["slug"])
                self.stdout.write(f"Purged {options['slug']}.")
            else:
                at = parse_datetime(options["at"]) if options["at"] else None
                if options["at"] and at is None:
                    raise ValidationError({"at": "Use a valid ISO timestamp."})
                event = generate_demo_event(
                    scenario=options["scenario"],
                    seed=options["seed"],
                    participants=options["participants"],
                    judges=options["judges"],
                    password=options["password"],
                    public=options["public"],
                    at=at,
                    checkpoint=options["checkpoint"],
                    live=options["live"],
                )
                self.stdout.write(
                    json.dumps(
                        {
                            "workspace": event.workspace.slug,
                            "event": str(event.public_id),
                            "organizer": f"demo-{options['scenario']}-{options['seed']}-organizer",
                        }
                    )
                )
        except ValidationError as exc:
            raise CommandError(json.dumps(getattr(exc, "message_dict", exc.messages))) from exc
