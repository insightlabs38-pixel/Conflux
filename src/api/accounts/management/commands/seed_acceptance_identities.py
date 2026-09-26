from django.core.management.base import BaseCommand
from django.db import transaction
from workspaces.models import Membership, Role, Workspace

from accounts.models import Session, User

# Fixed, well-known tokens: the acceptance checker's `.dogfood.toml` hands
# these back verbatim as `Cookie: session=<token>` headers and never logs in,
# so the tokens issued here must be stable across seed runs.
IDENTITIES = [
    ("organizer", Role.ORGANIZER, "acceptance-organizer"),
    ("judge_a", Role.JUDGE, "acceptance-judge-a"),
    ("judge_b", Role.JUDGE, "acceptance-judge-b"),
    ("participant", Role.PARTICIPANT, "acceptance-participant"),
]

WORKSPACE_SLUG = "acceptance"
WORKSPACE_NAME = "Acceptance Workspace"


class Command(BaseCommand):
    help = "Create deterministic acceptance-test identities, roles and sessions."

    @transaction.atomic
    def handle(self, *args, **options):
        workspace, _ = Workspace.objects.get_or_create(
            slug=WORKSPACE_SLUG, defaults={"name": WORKSPACE_NAME}
        )

        for username, role, token in IDENTITIES:
            user, created = User.objects.get_or_create(username=username)
            if created:
                # Not a normal-login credential: no attacker can authenticate
                # as this identity by guessing a password.
                user.set_unusable_password()
                user.save(update_fields=["password"])

            Membership.objects.get_or_create(user=user, workspace=workspace, role=role)

            session, _ = Session.objects.get_or_create(
                token=token, defaults={"user": user, "seed_label": username}
            )
            self.stdout.write(f"{username}: Cookie: session={session.token}")

        self.stdout.write(self.style.SUCCESS(f"Seeded acceptance workspace '{workspace.slug}'."))
