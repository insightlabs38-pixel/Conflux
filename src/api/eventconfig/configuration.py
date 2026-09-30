"""The effective configuration of an event (PD-F001-B01): every registry setting with its value,
default, preset baseline, where the value comes from, and whether it can be changed now."""

from . import modules
from .models import EventProfile
from .presets import baseline, get_preset
from .registry import SOURCES, SPECS, TIERS


def _plain(value):
    return (
        str(value)
        if hasattr(value, "value") and not isinstance(value, (int, float, bool))
        else value
    )


def _source(spec, value, base, has_profile):
    if spec.derived:
        return "derived"
    if spec.organizer_owned:
        return "set" if value not in (None, "", []) else "unset"
    reference = base[spec.key] if spec.key in base else spec.default
    if value != _plain(reference):
        return "overridden"
    return "preset" if has_profile and spec.key in base else "default"


def effective_configuration(event, *, module=None, tier=None, source=None, key=None):
    """Entries for the event; filters are exact except `key`, which is a prefix."""
    profile = EventProfile.objects.filter(event=event).first()
    preset = get_preset(profile.preset_key) if profile else None
    base = baseline(preset) if preset else {}
    enabled = {m["key"]: m["enabled"] for m in modules.event_modules(event)}
    entries = []
    for spec in SPECS:
        value = _plain(spec.read(event))
        entry_source = _source(spec, value, base, preset is not None)
        lock = spec.lock(event) if spec.lock else None
        constraint = spec.constraint(event) if callable(spec.constraint) else spec.constraint
        entry = {
            "key": spec.key,
            "module": spec.module,
            "tier": spec.tier,
            "label": spec.label,
            "help": spec.help,
            "schema": spec.schema,
            "value": value,
            "default": _plain(spec.default),
            "baseline": _plain(base[spec.key]) if spec.key in base else None,
            "source": entry_source,
            "editable": spec.write is not None and lock is None,
            "lock": {"code": lock.code, "message": lock.message} if lock else None,
            "constraint": constraint.strip() if constraint else None,
            "write": (
                {
                    "method": spec.write.method,
                    "path": spec.write.path,
                    "field": spec.write.field,
                    "body": spec.write.body,
                }
                if spec.write
                else None
            ),
            # A setting of a module that is off is still readable, but not offered for editing.
            "module_enabled": spec.module == "core" or enabled.get(spec.module, True),
        }
        entries.append(entry)
    if module:
        entries = [e for e in entries if e["module"] == module]
    if tier:
        entries = [e for e in entries if e["tier"] == tier]
    if source:
        entries = [e for e in entries if e["source"] == source]
    if key:
        entries = [e for e in entries if e["key"].startswith(key)]
    return {
        "event": str(event.public_id),
        "preset": (
            {"key": preset.key, "version": profile.preset_version, "label": preset.label}
            if preset
            else None
        ),
        "settings": entries,
    }


FILTER_CHOICES = {"tier": TIERS, "source": SOURCES}
