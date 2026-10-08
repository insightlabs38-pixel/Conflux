"""The phase an event is in, as people talk about it (draft, open, closed, judging, published,
archived), derived on the server from what is stored so every screen and client says the same thing.

The stored `Event.status` only has draft, open, closed and archived. Judging and publishing are not
statuses but things that have happened to the event, so they are read from the data, never from a
clock and never from a client: ballots a judge has submitted (not calibration practice) mean judging
has started, and a published award means the results are out. Reading only; changing the status
still goes through the status endpoint and its consequences.

Order, first match wins: archived and draft are what they say; published beats judging; judging
needs the event to be open or closed (a draft has nothing to judge); otherwise closed or open.
"""

from .models import Event, EventStatus

PHASES = {
    "draft": ("Draft", "Not open yet: only organizers can see it."),
    "open": ("Open", "Open for registration and submissions."),
    "closed": ("Closed", "Closed to new submissions; judging has not started."),
    "judging": ("Judging", "Judging has started: ballots have been submitted."),
    "published": ("Published", "Results are published: at least one award is out."),
    "archived": ("Archived", "Archived: kept for reference, no longer active."),
}


def phase_key(event: Event) -> str:
    # function-level imports: awards and evaluations import events, not the other way round
    from awards.models import Award
    from evaluations.models import Ballot

    if event.status == EventStatus.ARCHIVED:
        return "archived"
    if event.status == EventStatus.DRAFT:
        return "draft"
    if Award.objects.filter(event=event, published_at__isnull=False).exists():
        return "published"
    if Ballot.objects.filter(project__event=event, is_calibration=False).exists():
        return "judging"
    return "closed" if event.status == EventStatus.CLOSED else "open"


def phase(event: Event) -> dict:
    key = phase_key(event)
    label, reason = PHASES[key]
    return {"key": key, "label": label, "reason": reason}
