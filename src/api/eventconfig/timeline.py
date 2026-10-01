"""What each domain puts on the event timeline (PD-F002-B01-T08).

Providers only read; every item names the existing domain endpoint that changes its times. The
registry lives here because this app already knows the event's domains (see `registry.py`);
`core.timeline` stays free of them.
"""

from community.models import VotingPlan
from core import timeline
from presentation.models import PublicationSurface

CAP = 1000  # rows per provider; a timeline is for planning, not for bulk export
_BASE = "workspaces/{workspace}/events/{event}/"
_TIMES = {"starts_at": "starts_at", "ends_at": "ends_at"}


def _window(kind, key, label, opens, closes, **extra):
    """A window when both ends exist, otherwise an instant at the one that does."""
    if opens and closes:
        return timeline.TimelineItem(kind, key, label, opens, closes, **extra)
    if opens:
        return timeline.TimelineItem(kind, key, f"{label} opens", opens, None, **extra)
    if closes:
        return timeline.TimelineItem(kind, key, f"{label} closes", closes, None, **extra)
    return None


def _items(*candidates):
    return [c for c in candidates if c is not None]


def event_items(event):
    return _items(
        _window(
            "event",
            "event:window",
            "Event",
            event.starts_at,
            event.ends_at,
            source={"type": "event", "id": str(event.public_id)},
            editable=True,
            write=timeline.Write("PATCH", _BASE, _TIMES),
        )
    )


def gate_items(event):
    out = []
    for gate in event.temporal_gates.order_by("name")[:CAP]:
        out.append(
            _window(
                "gate",
                f"gate:{gate.public_id}",
                gate.name,
                gate.opens_at,
                gate.closes_at,
                source={"type": "temporal_gate", "id": str(gate.public_id)},
                editable=True,
                write=timeline.Write(
                    "PATCH",
                    f"{_BASE}temporal-gates/{gate.public_id}/",
                    {"starts_at": "opens_at", "ends_at": "closes_at"},
                ),
            )
        )
    return _items(*out)


def publication_items(event):
    labels = dict(PublicationSurface.choices)
    out = []
    for schedule in event.publication_schedules.select_related("finalist_stage")[:CAP]:
        label = f"Publish: {labels.get(schedule.surface, schedule.surface)}"
        out.append(
            timeline.TimelineItem(
                "publication",
                f"publication:{schedule.surface}",
                label,
                schedule.opens_at,
                schedule.closes_at,
                source={"type": "publication", "id": schedule.surface},
                editable=True,
                write=timeline.Write(
                    "PUT",
                    f"{_BASE}publication-schedules/{schedule.surface}/",
                    {"starts_at": "opens_at", "ends_at": "closes_at"},
                    extra=(
                        {"finalist_stage": str(schedule.finalist_stage.public_id)}
                        if schedule.finalist_stage_id
                        else {}
                    ),
                ),
            )
        )
    return out


def agenda_items(event):
    out = []
    sessions = event.agenda_sessions.select_related("location", "track")[:CAP]
    for session in sessions:
        group = {}
        if session.location_id:
            group["location"] = str(session.location.public_id)
        if session.track_id:
            group["track"] = str(session.track.public_id)
        out.append(
            timeline.TimelineItem(
                "agenda",
                f"agenda:{session.public_id}",
                session.title,
                session.starts_at,
                session.ends_at,
                source={"type": "agenda_session", "id": str(session.public_id)},
                group=group,
                editable=True,
                write=timeline.Write("PATCH", f"{_BASE}agenda/{session.public_id}/", _TIMES),
                inside_event=True,
                note="" if session.is_public else "Not on the public agenda.",
            )
        )
    return out


def office_hour_items(event):
    out = []
    for slot in event.office_hour_slots.select_related("mentor")[:CAP]:
        out.append(
            timeline.TimelineItem(
                "office_hours",
                f"office_hours:{slot.public_id}",
                f"Office hours: {slot.mentor.username}",
                slot.starts_at,
                slot.ends_at,
                source={"type": "office_hour_slot", "id": str(slot.public_id)},
                group={"mentor": str(slot.mentor.public_id)},
                inside_event=True,
            )
        )
    return out


def voting_items(event):
    plan = VotingPlan.objects.filter(event=event).first()
    if plan is None:
        return []
    return _items(
        _window(
            "voting",
            "voting:plan",
            "Community voting",
            plan.opens_at,
            plan.closes_at,
            source={"type": "voting_plan", "id": str(plan.public_id)},
            editable=True,
            write=timeline.Write(
                "PATCH",
                f"{_BASE}voting-plan/",
                {"starts_at": "opens_at", "ends_at": "closes_at"},
            ),
        )
    )


def reminder_items(event):
    due = event.reminders.filter(sent_message__isnull=True, cancelled_at__isnull=True)
    return [
        timeline.TimelineItem(
            "reminder",
            f"reminder:{reminder.public_id}",
            f"Reminder: {reminder.subject}",
            reminder.due_at,
            None,
            source={"type": "reminder", "id": str(reminder.public_id)},
            note="Sent automatically when due; cancel it from Communications.",
        )
        for reminder in due.order_by("due_at")[:CAP]
    ]


_ANNOUNCING = ("finalists", "winners", "feedback")


def publication_before_voting_closes(event, items):
    """Results-style surfaces open while the community can still vote."""
    voting = next((i for i in items if i.kind == "voting" and i.ends_at), None)
    if voting is None:
        return []
    return [
        timeline.Conflict(
            "publication_before_voting_closes",
            f"{item.label} opens before community voting closes.",
            (item.key, voting.key),
        )
        for item in items
        if item.kind == "publication"
        and item.source.get("id") in _ANNOUNCING
        and item.starts_at < voting.ends_at
    ]


for _provider in (
    timeline.Provider("event", "Event dates", event_items),
    timeline.Provider("gate", "Registration and submission windows", gate_items),
    timeline.Provider("publication", "Publication", publication_items),
    timeline.Provider("agenda", "Agenda", agenda_items),
    timeline.Provider("office_hours", "Office hours", office_hour_items),
    timeline.Provider("voting", "Community voting", voting_items),
    timeline.Provider("reminder", "Scheduled reminders", reminder_items),
):
    timeline.register_provider(_provider)
timeline.register_rule(publication_before_voting_closes)
