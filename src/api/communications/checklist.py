"""Event launch checklist (OPS-004): a read-only, opinionated set of checks
an organizer should clear before opening an event to participants --
independent of `Event.clean`'s own bare-minimum invariants (which only
require *some* dates once status flips to OPEN). Every check here reads
already-owned domain models; nothing is persisted or re-validated here.
"""

from dataclasses import dataclass

from community.models import VotingPlan
from evaluations.models import EvaluationPlan, EvaluationPoolStrategy
from forms.models import FormDefinition
from policies.models import TemporalGate


@dataclass(frozen=True)
class ChecklistItem:
    id: str
    severity: str  # "blocker" | "warning"
    passed: bool
    detail: str


def _window_outside_event(event, opens_at, closes_at):
    if not event.starts_at or not event.ends_at:
        return False
    if closes_at and closes_at <= event.starts_at:
        return True
    if opens_at and opens_at >= event.ends_at:
        return True
    return False


def _event_dates(event):
    passed = bool(event.starts_at and event.ends_at)
    return ChecklistItem(
        "event_dates",
        "blocker",
        passed,
        "Start and end dates are set." if passed else "Set the event start and end dates.",
    )


def _forms_published(event):
    unpublished = [
        form.name
        for form in FormDefinition.objects.filter(event=event)
        if form.versions.order_by("-number").first() is None
    ]
    passed = not unpublished
    return ChecklistItem(
        "forms_published",
        "blocker",
        passed,
        "All forms have a published version."
        if passed
        else f"Publish a version for: {', '.join(unpublished)}.",
    )


def _gate_windows(event):
    contradictory = [
        gate.name
        for gate in TemporalGate.objects.filter(event=event)
        if _window_outside_event(event, gate.opens_at, gate.closes_at)
    ]
    passed = not contradictory
    return ChecklistItem(
        "gate_windows",
        "warning",
        passed,
        "No gate windows fall outside the event dates."
        if passed
        else f"Gate window entirely outside event dates: {', '.join(contradictory)}.",
    )


def _voting_window(event):
    plan = VotingPlan.objects.filter(event=event).first()
    if plan is None:
        return ChecklistItem("voting_window", "warning", True, "No community voting configured.")
    passed = not _window_outside_event(event, plan.opens_at, plan.closes_at)
    return ChecklistItem(
        "voting_window",
        "warning",
        passed,
        "Voting window overlaps the event dates."
        if passed
        else "Community voting window is entirely outside the event dates.",
    )


def _judging_rubrics(event):
    missing = [
        plan.name
        for plan in EvaluationPlan.objects.filter(stage__event=event)
        if plan.current_rubric_version is None
    ]
    passed = not missing
    return ChecklistItem(
        "judging_rubrics",
        "blocker",
        passed,
        "Every evaluation plan has a published rubric."
        if passed
        else f"Publish a rubric for: {', '.join(missing)}.",
    )


def _judging_pools(event):
    unstaffed = [
        plan.name
        for plan in EvaluationPlan.objects.filter(stage__event=event).select_related("pool")
        if plan.pool_strategy
        in (EvaluationPoolStrategy.ALL_JUDGES, EvaluationPoolStrategy.ASSIGNED_SUBSET)
        and (plan.pool_id is None or not plan.pool.memberships.exists())
    ]
    passed = not unstaffed
    return ChecklistItem(
        "judging_pools",
        "warning",
        passed,
        "Every evaluation plan has a staffed judge pool."
        if passed
        else f"No judges assigned for: {', '.join(unstaffed)}.",
    )


def _public_page(event):
    if not event.is_public:
        return ChecklistItem("public_page", "warning", True, "Event is not public yet.")
    page = getattr(event, "page", None)
    passed = page is not None and page.blocks.exists()
    return ChecklistItem(
        "public_page",
        "warning",
        passed,
        "Public page has content."
        if passed
        else "Event is public but its page has no content blocks.",
    )


_RULES = [
    _event_dates,
    _forms_published,
    _gate_windows,
    _voting_window,
    _judging_rubrics,
    _judging_pools,
    _public_page,
]


def compute_launch_checklist(event) -> dict:
    items = [rule(event) for rule in _RULES]
    blocked = any(not item.passed and item.severity == "blocker" for item in items)
    warned = any(not item.passed and item.severity == "warning" for item in items)
    status = "blocked" if blocked else "warning" if warned else "ready"
    return {
        "status": status,
        "items": [
            {
                "id": item.id,
                "severity": item.severity,
                "passed": item.passed,
                "detail": item.detail,
            }
            for item in items
        ],
    }
