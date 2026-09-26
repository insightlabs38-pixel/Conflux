from dataclasses import dataclass, field

from django.utils import timezone

from .evaluator import is_allowed
from .models import ExceptionGrant, PolicyBinding, TemporalGate


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


@dataclass(frozen=True)
class Decision:
    """Evidence for one action-gating decision (POL-005): enough for a
    simple organizer/user-facing explanation, computed fresh on every
    call rather than persisted anywhere — a full trace/debugger UI is a
    stretch goal (see the stage/policy plan doc), not this contract.
    """

    action: str
    allowed: bool
    reason: str | None
    policy_name: str | None = None
    exception_grant_reason: str | None = None
    gate_facts: dict = field(default_factory=dict)

    def explain(self):
        """One human-readable sentence, safe to show an organizer or the
        subject the decision was about.
        """
        if self.reason:
            return self.reason
        return f"{self.action!r} is allowed (no policy configured for it)."


def explain_action(event, action, facts, *, subject_type=None, subject_id=None):
    """The full evidence behind an action-gating decision. `check_action`
    is this with only (allowed, reason) kept — most call sites only need
    the bool, this is for anywhere that needs to show its work.
    """
    gate_facts = {k: v for k, v in facts.items() if k.startswith("gate_open:")}
    binding = (
        PolicyBinding.objects.filter(event=event, action=action).select_related("policy").first()
    )
    if binding is None:
        return Decision(action=action, allowed=True, reason=None, gate_facts=gate_facts)

    if is_allowed(binding.policy.ast, facts):
        return Decision(
            action=action,
            allowed=True,
            reason=None,
            policy_name=binding.policy.name,
            gate_facts=gate_facts,
        )

    if subject_type and subject_id:
        grant = ExceptionGrant.objects.filter(
            event=event, action=action, subject_type=subject_type, subject_id=subject_id
        ).first()
        if grant and grant.is_active():
            grant_reason = grant.reason or "no reason given"
            return Decision(
                action=action,
                allowed=True,
                reason=f"Allowed via exception grant ({grant_reason}).",
                policy_name=binding.policy.name,
                exception_grant_reason=grant_reason,
                gate_facts=gate_facts,
            )

    return Decision(
        action=action,
        allowed=False,
        reason=f"Denied by policy {binding.policy.name!r} on action {action!r}.",
        policy_name=binding.policy.name,
        gate_facts=gate_facts,
    )


def check_action(event, action, facts, *, subject_type=None, subject_id=None):
    """Is `action` allowed for `event` given `facts`?

    No binding for this (event, action) means the action isn't gated by a
    policy at all — it proceeds subject to whatever the domain's own logic
    already enforces. That's a deliberate default, not an oversight: an
    organizer opts an action into policy gating by creating a binding
    (POL-006 gives them a UI for that); there is no implicit "everything
    is denied until configured" for actions nobody asked to gate.

    A denial can be overridden by an active ExceptionGrant (POL-004) for
    the exact (event, action, subject) — never checked when the policy
    would already allow, and never able to affect a different action for
    the same subject, since a grant only ever names one action.

    Returns (allowed: bool, reason: str | None). For the full evidence
    behind this decision, see `explain_action`.
    """
    decision = explain_action(
        event, action, facts, subject_type=subject_type, subject_id=subject_id
    )
    return decision.allowed, decision.reason
