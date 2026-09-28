"""Organizer-defined classification labels. Deliberately non-authoritative:
nothing in eligibility, authorization, scoring, awards or results reads them.
"""

from core.models import PublicIdModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

MAX_TAXONOMIES_PER_WORKSPACE = 20
MAX_TERMS_PER_TAXONOMY = 50


class SubjectType(models.TextChoices):
    PROJECT = "project", "Project"
    PERSON = "person", "Person"
    EVENT = "event", "Event"


class Taxonomy(PublicIdModel):
    workspace = models.ForeignKey(
        "workspaces.Workspace", on_delete=models.CASCADE, related_name="taxonomies"
    )
    key = models.SlugField(max_length=50)
    name = models.CharField(max_length=80)
    applies_to = models.CharField(max_length=10, choices=SubjectType.choices)
    allows_multiple = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["key"]
        constraints = [
            models.UniqueConstraint(fields=["workspace", "key"], name="unique_taxonomy_key")
        ]


class TaxonomyTerm(PublicIdModel):
    taxonomy = models.ForeignKey(Taxonomy, on_delete=models.CASCADE, related_name="terms")
    key = models.SlugField(max_length=50)
    label = models.CharField(max_length=80)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "key"]
        constraints = [
            models.UniqueConstraint(fields=["taxonomy", "key"], name="unique_taxonomy_term_key")
        ]


class TaxonomyAssignment(PublicIdModel):
    event = models.ForeignKey(
        "events.Event", on_delete=models.CASCADE, related_name="taxonomy_assignments"
    )
    term = models.ForeignKey(TaxonomyTerm, on_delete=models.PROTECT, related_name="assignments")
    subject_type = models.CharField(max_length=10, choices=SubjectType.choices)
    project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="taxonomy_assignments",
    )
    person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="taxonomy_assignments",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["term__taxonomy__key", "term__position", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(subject_type="project", project__isnull=False, person__isnull=True)
                    | Q(subject_type="person", project__isnull=True, person__isnull=False)
                    | Q(subject_type="event", project__isnull=True, person__isnull=True)
                ),
                name="taxonomy_assignment_subject_matches_type",
            ),
            models.UniqueConstraint(
                fields=["term", "project"],
                condition=Q(project__isnull=False),
                name="unique_taxonomy_project_term",
            ),
            models.UniqueConstraint(
                fields=["term", "event", "person"],
                condition=Q(person__isnull=False),
                name="unique_taxonomy_person_term",
            ),
            models.UniqueConstraint(
                fields=["term", "event"],
                condition=Q(subject_type="event"),
                name="unique_taxonomy_event_term",
            ),
        ]

    def clean(self):
        if self.term.taxonomy.applies_to != self.subject_type:
            raise ValidationError({"term": "Term's taxonomy does not apply to this subject."})
        if self.term.taxonomy.workspace_id != self.event.workspace_id:
            raise ValidationError({"term": "Term belongs to a different workspace."})
        if self.project_id and self.project.event_id != self.event_id:
            raise ValidationError({"project": "Project belongs to a different event."})
        if (
            self.person_id
            and not self.event.workspace.memberships.filter(user_id=self.person_id).exists()
        ):
            raise ValidationError({"person": "Person is not a member of this workspace."})
