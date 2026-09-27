from core.models import PublicIdModel
from django.db import models
from events.models import Event

from .blocks import clean_config


class PageTheme(models.TextChoices):
    DEFAULT = "default", "Default"
    DARK = "dark", "Dark"
    MINIMAL = "minimal", "Minimal"


class PageBlockKind(models.TextChoices):
    HERO = "hero", "Hero"
    TRACKS = "tracks", "Tracks"
    PRIZES = "prizes", "Prizes"
    SCHEDULE = "schedule", "Schedule"
    SPONSORS = "sponsors", "Sponsors"
    FAQ = "faq", "FAQ"
    RESOURCES = "resources", "Resources"
    GALLERY = "gallery", "Gallery"
    RESULTS = "results", "Results"
    ANNOUNCEMENTS = "announcements", "Announcements"
    RICH_TEXT = "rich_text", "Rich text"
    CTA = "cta", "Call to action"


class Page(PublicIdModel):
    """One organizer-composed public landing page per event."""

    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name="page")
    theme = models.CharField(max_length=10, choices=PageTheme.choices, default=PageTheme.DEFAULT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PageBlock(PublicIdModel):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="blocks")
    kind = models.CharField(max_length=20, choices=PageBlockKind.choices)
    position = models.PositiveIntegerField(default=0)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "id"]

    def clean(self):
        self.config = clean_config(self.kind, self.config)
