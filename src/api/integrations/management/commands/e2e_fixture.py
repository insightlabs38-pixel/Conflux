import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from integrations.e2e_fixtures import (
    FIXTURE_SEED_BASE,
    PROFILES,
    create_fixture,
    dispose_fixture,
    fixture_scenarios,
    sweep_fixtures,
)


class Command(BaseCommand):
    help = (
        f"Create, dispose or sweep isolated browser-test fixtures (seeds >= {FIXTURE_SEED_BASE})."
    )

    def add_arguments(self, parser):
        commands = parser.add_subparsers(dest="action", required=True)
        create = commands.add_parser("create", help="Print the new fixture handle as JSON.")
        create.add_argument("profile", choices=sorted(PROFILES))
        create.add_argument("--nonce", type=int, help="Preferred per-run seed block (0-9999).")
        create.add_argument("--password", help="Shared account password (default: random).")
        commands.add_parser("dispose").add_argument("slug")
        sweep = commands.add_parser("sweep", help="Purge leftover fixtures.")
        sweep.add_argument("--older-than-minutes", type=int, default=0)
        commands.add_parser("list")

    def handle(self, *args, action, **options):
        try:
            if action == "create":
                handle = create_fixture(
                    options["profile"], nonce=options["nonce"], password=options["password"]
                )
                self.stdout.write(json.dumps(handle))
            elif action == "dispose":
                dispose_fixture(options["slug"])
                self.stdout.write(f"Disposed {options['slug']}.")
            elif action == "sweep":
                slugs = sweep_fixtures(older_than_minutes=options["older_than_minutes"])
                self.stdout.write(json.dumps({"purged": slugs}))
            else:
                for row in fixture_scenarios().select_related("workspace").order_by("seed"):
                    self.stdout.write(f"{row.workspace.slug} {row.created_at:%Y-%m-%dT%H:%MZ}")
        except ValidationError as exc:
            raise CommandError(json.dumps(getattr(exc, "message_dict", exc.messages))) from exc
