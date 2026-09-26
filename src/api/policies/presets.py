"""Common policy shapes an organizer can pick from directly (POL-006):
"no raw JSON required for common rules" doesn't mean raw JSON is removed —
`Policy.ast` still accepts it for anything a preset doesn't cover — it
means the common cases have a form control instead of a JSON editor.
"""

from .evaluator import PolicyError

PRESETS = {
    "everyone": {
        "label": "Anyone may do this",
        "params": [],
        "build": lambda **params: {"op": "true"},
    },
    "no_one": {
        "label": "No one may do this right now",
        "params": [],
        "build": lambda **params: {"op": "false"},
    },
    "organizers_only": {
        "label": "Organizers only",
        "params": [],
        "build": lambda **params: {"op": "eq", "fact": "role", "value": "organizer"},
    },
    "judges_only": {
        "label": "Judges only",
        "params": [],
        "build": lambda **params: {"op": "eq", "fact": "role", "value": "judge"},
    },
    "participants_only": {
        "label": "Participants only",
        "params": [],
        "build": lambda **params: {"op": "eq", "fact": "role", "value": "participant"},
    },
    "window_open": {
        "label": "A named window (temporal gate) is open",
        "params": ["gate_name"],
        "build": lambda **params: {
            "op": "eq",
            "fact": f"gate_open:{params['gate_name']}",
            "value": True,
        },
    },
}


def build_preset_ast(preset_slug, params=None):
    if preset_slug not in PRESETS:
        raise PolicyError(f"Unknown preset: {preset_slug!r}")
    preset = PRESETS[preset_slug]
    params = params or {}
    missing = [p for p in preset["params"] if p not in params]
    if missing:
        raise PolicyError(f"Preset {preset_slug!r} needs: {', '.join(missing)}.")
    return preset["build"](**params)
