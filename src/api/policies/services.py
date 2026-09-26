from django.utils import timezone

from .evaluator import is_allowed
from .models import PolicyBinding, TemporalGate


def base_facts(event, *, at=None):
    """Facts every action-gating call gets for free: the authoritative
    server clock, and each of the event's temporal gates' current status
    as a `gate_open:<name>` boolean. A policy references
    `{"op": "eq", "fact": "gate_open:submissions", "value": true}` rather
    than reimplementing window logic in the AST.
    """
    now = at or timezone.now()
    facts = {"now": now}
    for gate in TemporalGate.objects.filter(event=event):
        facts[f"gate_open:{gate.name}"] = gate.is_open(now)
    return facts


def check_action(event, action, facts):
    """Is `action` allowed for `event` given `facts`?

    No binding for this (event, action) means the action isn't gated by a
    policy at all — it proceeds subject to whatever the domain's own logic
    already enforces. That's a deliberate default, not an oversight: an
    organizer opts an action into policy gating by creating a binding
    (POL-006 gives them a UI for that); there is no implicit "everything
    is denied until configured" for actions nobody asked to gate.

    Returns (allowed: bool, reason: str | None). `reason` is the seed for
    POL-005's decision-evidence contract, not currently used to render
    anything.
    """
    binding = (
        PolicyBinding.objects.filter(event=event, action=action).select_related("policy").first()
    )
    if binding is None:
        return True, None
    if is_allowed(binding.policy.ast, facts):
        return True, None
    return False, f"Denied by policy {binding.policy.name!r} on action {action!r}."
