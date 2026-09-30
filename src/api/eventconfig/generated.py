"""Generated configuration (PD-F001-B02): state only what is necessary, keep the rest legible.

A format already supplies most of an event's values, so a document that restates all of them buries
the few decisions the organizer actually made. This partitions the effective configuration (the one
registry reading, `configuration.effective_configuration`) into what must be stated (values the
organizer set or changed from the format's or registry's value) and what is inherited (equal to
it), which is listed for reading but never stated. Nothing is stored or computed twice: the source
of each value is the registry's.
"""

import json

from .configuration import effective_configuration

# `source` -> why it is stated. Everything else is not needed to reproduce the event.
_EXPLICIT = {"overridden": "changed", "set": "organizer"}


def _scalar(value):
    return json.dumps(value, ensure_ascii=False)


def _text(preset, explicit, inherited, derived, unset):
    lines = ["# Conflux event configuration: only what differs from the format is stated."]
    lines.append(
        f"format: {preset['key']}@{preset['version']}  # {preset['label']}"
        if preset
        else "format: none  # built by hand: values are relative to the registry defaults"
    )
    lines.append("settings:" if explicit else "settings: {}")
    for entry in explicit:
        if entry["reason"] == "changed":
            was = "the format uses" if entry["origin"] == "preset" else "the default is"
            note = f"changed; {was} {_scalar(entry['baseline'])}"
        else:
            note = "set by the organizer"
        lines.append(f"  {entry['key']}: {_scalar(entry['value'])}  # {note}")
    if inherited:
        lines += ["#", "# Inherited, not stated (equal to the format or default):"]
        lines += [f"#   {e['key']}: {_scalar(e['value'])}  # {e['origin']}" for e in inherited]
    if derived:
        lines += ["#", "# Derived, computed and never stated:"]
        lines += [f"#   {e['key']}: {_scalar(e['value'])}" for e in derived]
    if unset:
        lines += ["#", "# Not set:"]
        lines += [f"#   {key}" for key in unset]
    return "\n".join(lines) + "\n"


def generated_configuration(event):
    current = effective_configuration(event)
    preset = current["preset"]
    explicit, inherited, derived, unset = [], [], [], []
    for entry in current["settings"]:
        source = entry["source"]
        label = {"key": entry["key"], "label": entry["label"], "value": entry["value"]}
        if source == "set" and entry["default"] is not None and entry["value"] == entry["default"]:
            # The organizer's own value that equals the registry default says nothing new.
            inherited.append({**label, "origin": "default"})
        elif source in _EXPLICIT:
            # What the value would have been without the organizer: the format's, else the default.
            baseline = entry["baseline"] if entry["baseline"] is not None else entry["default"]
            explicit.append(
                {
                    **label,
                    "reason": _EXPLICIT[source],
                    "baseline": None if source == "set" else baseline,
                    "origin": "preset" if entry["baseline"] is not None else "default",
                    "write": entry["write"],
                }
            )
        elif source in ("preset", "default"):
            inherited.append({**label, "origin": source})
        elif source == "derived":
            derived.append(label)
        else:
            unset.append(entry["key"])
    return {
        "event": current["event"],
        "preset": preset,
        "explicit": explicit,
        "inherited": inherited,
        "derived": derived,
        "unset": unset,
        "document": {
            "format": f"{preset['key']}@{preset['version']}" if preset else None,
            "settings": {entry["key"]: entry["value"] for entry in explicit},
        },
        "text": _text(preset, explicit, inherited, derived, unset),
    }
