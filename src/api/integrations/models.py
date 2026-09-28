from core.models import PublicIdModel
from django.conf import settings
from django.db import models


class ArchiveRestoration(PublicIdModel):
    event = models.OneToOneField(
        "events.Event", on_delete=models.CASCADE, related_name="archive_restoration"
    )
    source_sha256 = models.CharField(max_length=64)
    source_archive = models.JSONField()
    identity_map = models.JSONField()
    restored_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            from django.core.exceptions import ValidationError

            raise ValidationError("Archive restoration provenance is immutable.")
        super().save(*args, **kwargs)


class DemoScenario(PublicIdModel):
    """Marks a workspace as synthetic. Its presence is the only thing that makes
    a workspace purgeable by the demo tooling.
    """

    workspace = models.OneToOneField(
        "workspaces.Workspace", on_delete=models.CASCADE, related_name="demo_scenario"
    )
    scenario = models.CharField(max_length=40)
    seed = models.PositiveIntegerField()
    participants = models.PositiveSmallIntegerField()
    judges = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class EventRetentionPolicy(PublicIdModel):
    """Organizer-chosen retention windows, counted from `event.ends_at`. A null
    window means "never automatically"; enforcement only runs on demand.
    """

    event = models.OneToOneField(
        "events.Event", on_delete=models.CASCADE, related_name="retention_policy"
    )
    participant_data_days = models.PositiveIntegerField(null=True, blank=True)
    private_artifact_days = models.PositiveIntegerField(null=True, blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    updated_at = models.DateTimeField(auto_now=True)


class WebhookPlatform(models.TextChoices):
    """S23: what shape the delivered body should take. GENERIC is the
    signed Conflux envelope every subscription used before this batch;
    DISCORD/SLACK reshape the same underlying DomainEvent into that
    platform's plain incoming-webhook message format instead -- no new
    hosted service or OAuth app, just a different body for the same
    delivery/retry/signing pipeline.
    """

    GENERIC = "generic", "Generic (signed Conflux envelope)"
    DISCORD = "discord", "Discord incoming webhook"
    SLACK = "slack", "Slack incoming webhook"


class WebhookSubscription(PublicIdModel):
    workspace = models.ForeignKey("workspaces.Workspace", on_delete=models.CASCADE)
    event = models.ForeignKey("events.Event", null=True, blank=True, on_delete=models.CASCADE)
    url = models.URLField(max_length=2048)
    event_types = models.JSONField(default=list)
    platform = models.CharField(
        max_length=10, choices=WebhookPlatform.choices, default=WebhookPlatform.GENERIC
    )
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


class WebhookAttempt(PublicIdModel):
    delivery = models.ForeignKey(WebhookDelivery, on_delete=models.CASCADE, related_name="history")
    destination = models.URLField(max_length=2048)
    body = models.TextField()
    headers = models.JSONField()
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    error = models.CharField(max_length=200, blank=True)


class EventTemplate(PublicIdModel):
    """A named, reusable configuration snapshot (TPL-001): the same
    organizer-authored-config shape `archive.build_archive` produces, saved
    independent of the source event's own lifecycle -- editing, archiving
    or deleting the event it was saved from never touches a template
    already saved from it, since the snapshot is a frozen copy, not a
    live reference.
    """

    workspace = models.ForeignKey(
        "workspaces.Workspace", on_delete=models.CASCADE, related_name="event_templates"
    )
    name = models.CharField(max_length=160)
    source_event_name = models.CharField(max_length=200, blank=True)
    sections = models.JSONField(default=list)
    archive = models.JSONField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="event_templates_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["workspace", "name"], name="unique_event_template_name")
        ]
        ordering = ["name", "pk"]

    def __str__(self):
        return self.name


class ExternalQualifierBinding(PublicIdModel):
    """Ties one external system's own opaque `external_ref` to one real,
    already-existing `Project` in this event, for good (EXTQ-001/002):
    every later import call for the same `external_ref` resolves to the
    same Project without the caller ever needing to learn our internal
    `public_id`. This is a lookup aid, not a new identity -- the Project
    remains the one and only canonical record, exactly like
    `FixtureJudge.linked_user` binds a fixture identity to a real User
    rather than inventing a shadow account.
    """

    event = models.ForeignKey(
        "events.Event", on_delete=models.CASCADE, related_name="external_qualifier_bindings"
    )
    external_ref = models.CharField(max_length=120)
    project = models.ForeignKey(
        "projects.Project", on_delete=models.PROTECT, related_name="external_qualifier_bindings"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "external_ref"], name="unique_external_qualifier_ref"
            )
        ]


class ExternalQualifierImport(PublicIdModel):
    """One received import call: a receipt of what was asked for and what
    actually happened, for organizer visibility and replay evidence.
    """

    event = models.ForeignKey(
        "events.Event", on_delete=models.CASCADE, related_name="external_qualifier_imports"
    )
    stage = models.ForeignKey(
        "stages.Stage", on_delete=models.PROTECT, related_name="external_qualifier_imports"
    )
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="external_qualifier_imports",
    )
    entries = models.JSONField(default=list)
    advanced_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]


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
