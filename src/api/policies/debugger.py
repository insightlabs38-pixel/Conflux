from django.utils import timezone

from .evaluator import trace_evaluate
from .models import PolicyBinding
from .services import base_facts, explain_action


def debug_action(event, action, *, subject_type=None, subject_id=None):
    now = timezone.now()
    facts = base_facts(event, at=now)
    decision = explain_action(
        event, action, facts, subject_type=subject_type, subject_id=subject_id
    )
    binding = (
        PolicyBinding.objects.filter(event=event, action=action).select_related("policy").first()
    )
    policy_allowed = None
    error = None
    trace = None
    if binding is not None:
        policy_allowed, error, trace = trace_evaluate(binding.policy.ast, facts)
    return {
        "action": action,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "checked_at": now.isoformat(),
        "facts": {
            key: value.isoformat() if key == "now" else value for key, value in facts.items()
        },
        "policy": {"public_id": str(binding.policy.public_id), "name": binding.policy.name}
        if binding
        else None,
        "policy_allowed": policy_allowed,
        "allowed": decision.allowed,
        "reason": decision.explain(),
        "exception_grant_reason": decision.exception_grant_reason,
        "error": error,
        "trace": trace,
    }
