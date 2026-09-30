"""Event launch checklist (OPS-004), now a projection of the canonical readiness rules.

The rules live in `eventconfig.readiness` (PD-F001-B01); this module keeps the long-standing import
path and response shape (`status`, `items[id, severity, passed, detail]`, plus `module` and `fix`).
"""

from eventconfig.readiness import compute_readiness


def compute_launch_checklist(event) -> dict:
    return compute_readiness(event)
