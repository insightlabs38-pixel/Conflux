from core.models import PublicIdModel
from django.conf import settings
from django.db import models


class WebhookSubscription(PublicIdModel):
    workspace = models.ForeignKey("workspaces.Workspace", on_delete=models.CASCADE)
    event = models.ForeignKey("events.Event", null=True, blank=True, on_delete=models.CASCADE)
    url = models.URLField(max_length=2048)
    event_types = models.JSONField(default=list)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class WebhookDelivery(PublicIdModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        DEAD = "dead", "Dead"

    subscription = models.ForeignKey(
        WebhookSubscription, on_delete=models.CASCADE, related_name="deliveries"
    )
    domain_event = models.ForeignKey("audit.DomainEvent", on_delete=models.CASCADE)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    last_status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    last_error = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["subscription", "domain_event"], name="unique_webhook_delivery"
            )
        ]


class ImportedFixture(models.Model):
    """One run of the `import_fixture` command against fixtures/fixtures.json.

    The command is destructive-then-rebuild (see the command docstring), so
    there is at most one row here in practice, but the run is still recorded
    for traceability: what file, when, which upstream event.
    """

    source_path = models.CharField(max_length=500)
    event_external_id = models.CharField(max_length=64)
    event_name = models.CharField(max_length=200)
    event_submissions_close = models.DateTimeField()
    imported_at = models.DateTimeField(auto_now_add=True)


class FixtureTrack(models.Model):
    fixture = models.ForeignKey(ImportedFixture, on_delete=models.CASCADE, related_name="tracks")
    external_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)


class FixtureJudge(models.Model):
    fixture = models.ForeignKey(ImportedFixture, on_delete=models.CASCADE, related_name="judges")
    external_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    tracks = models.ManyToManyField(FixtureTrack, related_name="judges")
    # Set by `link_judge_identities` (FX-003), not by the import itself: it
    # ties one fixture judge to a real seeded acceptance User so
    # judge-scoped routes have a session to authenticate against. Cleared on
    # every re-import along with everything else on ImportedFixture.
    linked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="linked_fixture_judge",
    )


class FixtureTeam(models.Model):
    fixture = models.ForeignKey(ImportedFixture, on_delete=models.CASCADE, related_name="teams")
    external_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)


class FixtureTeamMember(models.Model):
    team = models.ForeignKey(FixtureTeam, on_delete=models.CASCADE, related_name="members")
    email = models.EmailField()


class FixtureProject(models.Model):
    # Not every (team, title, repo_url) triple is distinct: the fixture
    # deliberately contains one duplicate submission (see FX-001 receipt).
    # external_id alone is what's guaranteed unique, and even that guarantee
    # comes from the source file, not from any dedup this importer performs.
    fixture = models.ForeignKey(ImportedFixture, on_delete=models.CASCADE, related_name="projects")
    external_id = models.CharField(max_length=64, unique=True)
    team = models.ForeignKey(FixtureTeam, on_delete=models.CASCADE, related_name="projects")
    track = models.ForeignKey(FixtureTrack, on_delete=models.CASCADE, related_name="projects")
    title = models.CharField(max_length=300)
    summary = models.TextField(blank=True)
    repo_url = models.URLField(max_length=500)
    submitted_at = models.DateTimeField()


class FixtureScore(models.Model):
    fixture = models.ForeignKey(ImportedFixture, on_delete=models.CASCADE, related_name="scores")
    judge = models.ForeignKey(FixtureJudge, on_delete=models.CASCADE, related_name="scores")
    project = models.ForeignKey(FixtureProject, on_delete=models.CASCADE, related_name="scores")
    comment = models.TextField(blank=True)


class FixtureScoreCriterion(models.Model):
    # A child row per criterion, not a JSON blob on FixtureScore: the fixture
    # format allows a judge to skip a criterion or a whole review batch
    # (see fixtures/fixtures.json note in the FX-001 receipt), and this shape
    # represents "not scored" as "no row" instead of a sentinel value that a
    # later reader could mistake for a real score.
    score = models.ForeignKey(FixtureScore, on_delete=models.CASCADE, related_name="criteria")
    name = models.CharField(max_length=50)
    value = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["score", "name"], name="unique_criterion_per_score")
        ]
