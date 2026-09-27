"""Workspace-wide operator view built from existing event and audit records."""

from audit.models import AuditEvent
from events.models import Event
from integrations.models import EventTemplate

from .checklist import compute_launch_checklist

EVENT_LIMIT = 50
ACTIVITY_LIMIT = 20


def compute_operator_console(workspace):
    events = Event.objects.filter(workspace=workspace).order_by("-updated_at", "-pk")
    rows = []
    for event in events[:EVENT_LIMIT]:
        checklist = compute_launch_checklist(event)
        rows.append(
            {
                "public_id": str(event.public_id),
                "name": event.name,
                "status": event.status,
                "is_public": event.is_public,
                "updated_at": event.updated_at,
                "health": checklist["status"],
                "blocker_count": sum(
                    not item["passed"] and item["severity"] == "blocker"
                    for item in checklist["items"]
                ),
                "warning_count": sum(
                    not item["passed"] and item["severity"] == "warning"
                    for item in checklist["items"]
                ),
            }
        )
    templates = EventTemplate.objects.filter(workspace=workspace).order_by("name", "pk")
    activity = (
        AuditEvent.objects.filter(workspace=workspace)
        .select_related("actor")
        .order_by("-created_at", "-pk")[:ACTIVITY_LIMIT]
    )
    return {
        "event_total": events.count(),
        "events": rows,
        "template_total": templates.count(),
        "templates": [
            {
                "public_id": str(template.public_id),
                "name": template.name,
                "source_event_name": template.source_event_name,
            }
            for template in templates[:EVENT_LIMIT]
        ],
        "activity": [
            {
                "action": item.action,
                "actor": item.actor.username if item.actor else None,
                "target_type": item.target_type,
                "target_id": item.target_id,
                "created_at": item.created_at,
            }
            for item in activity
        ],
    }
