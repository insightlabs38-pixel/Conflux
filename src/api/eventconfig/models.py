from core.models import PublicIdModel
from django.db import models
from events.models import Event


class EventProfile(PublicIdModel):
    """Where an event's starting configuration came from (PD-F001-B01).

    Provenance only: every configured value lives in its own domain row, and whether one still
    matches the preset is computed by comparing it with the preset baseline, never stored. Events
    created before presets existed, or built by hand, have no profile (custom/legacy).
    """

    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name="profile")
    preset_key = models.SlugField(max_length=60)
    preset_version = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
