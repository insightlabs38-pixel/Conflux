from core.models import PublicIdModel
from django.conf import settings
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


class EventModuleSetting(PublicIdModel):
    """An organizer's explicit choice to turn an optional module on or off for one event.

    Whether a module is effectively enabled is computed in `modules.py`: this row or the module
    already having content for the event. Legacy events have no rows; everything derives from data.
    """

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="module_settings")
    module = models.SlugField(max_length=60)
    enabled = models.BooleanField()
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    changed_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "module"], name="unique_event_module_setting")
        ]
