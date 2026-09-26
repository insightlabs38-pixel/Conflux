from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from integrations.models import FixtureJudge, ImportedFixture

# Deterministic, not "first two rows returned by the database": sorted by the
# fixture's own external_id so a re-import (which recreates every row with
# new internal PKs) always links the same two fixture judges.
LINKS = [("judge_a", 0), ("judge_b", 1)]


class Command(BaseCommand):
    """Link the seeded judge_a/judge_b acceptance identities to two distinct
    fixture judges who each have at least one recorded score, so
    `judge_scores`/`peer_scores` (FX-003) have real per-user data instead of
    an empty result. Run after both `import_fixture` and
    `seed_acceptance_identities`.
    """

    help = "Link judge_a/judge_b acceptance identities to fixture judges."

    def handle(self, *args, **options):
        fixture = ImportedFixture.objects.order_by("-imported_at").first()
        if fixture is None:
            raise CommandError("No fixture imported yet; run `import_fixture` first.")

        candidates = list(
            FixtureJudge.objects.filter(fixture=fixture, scores__isnull=False)
            .distinct()
            .order_by("external_id")
        )
        if len(candidates) < len(LINKS):
            raise CommandError(
                f"Need at least {len(LINKS)} scored judges to link, found {len(candidates)}."
            )

        User = get_user_model()
        for username, index in LINKS:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist as exc:
                raise CommandError(
                    f"No seeded user {username!r}; run `seed_acceptance_identities` first."
                ) from exc
            judge = candidates[index]
            judge.linked_user = user
            judge.save(update_fields=["linked_user"])
            self.stdout.write(f"{username} -> {judge.external_id} ({judge.name})")
