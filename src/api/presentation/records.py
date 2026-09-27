"""REC-001/002: signed, publicly verifiable records for an event, a
project, or a judge's participation in it.

"As configured" (REC-001's goal) means every claim is read from the event's
own real data at issuance time -- there is no fixed certificate template to
fill in. Records are signed with Ed25519 (`keys.py`) and are verifiable
offline by anyone holding the published public key: verification never
needs to call back to this server (see
docs/architecture/VERIFIABLE_RECORDS.md).
"""

import jwt
from django.utils import timezone

from .keys import private_key, public_key

ISSUER = "conflux"
ALGORITHM = "EdDSA"
KINDS = ("event", "project", "judge")


class RecordVerificationError(Exception):
    """A token that doesn't parse, isn't signed by our key, or is missing a
    required claim. Never distinguishes *why* beyond the message -- a
    verifier doesn't need to know more than "not a real record"."""


def _event_claims(event):
    return {
        "public_id": str(event.public_id),
        "name": event.name,
        "starts_at": event.starts_at.isoformat() if event.starts_at else None,
        "ends_at": event.ends_at.isoformat() if event.ends_at else None,
    }


def _envelope(kind, event, subject):
    return {
        "iss": ISSUER,
        "kind": kind,
        "iat": int(timezone.now().timestamp()),
        "event": _event_claims(event),
        "subject": subject,
    }


def build_event_record(event):
    from projects.models import Project, SubmissionStatus

    finalized_projects = (
        Project.objects.filter(event=event, submissions__status=SubmissionStatus.FINALIZED)
        .distinct()
        .count()
    )
    return _envelope("event", event, {"finalized_project_count": finalized_projects})


def build_project_record(project):
    return _envelope(
        "project",
        project.event,
        {
            "public_id": str(project.public_id),
            "name": project.name,
            "track": project.track.name if project.track else None,
        },
    )


def build_judge_record(user, event):
    from evaluations.models import PoolMembership

    if not PoolMembership.objects.filter(judge=user, pool__event=event).exists():
        raise ValueError("This user is not a judge pool member for this event.")
    return _envelope(
        "judge",
        event,
        {
            "public_id": str(user.public_id),
            "display_name": user.get_full_name() or user.username,
        },
    )


def sign_record(claims):
    return jwt.encode(claims, private_key(), algorithm=ALGORITHM)


def verify_record(token):
    try:
        return jwt.decode(
            token,
            public_key(),
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            options={"require": ["iss", "kind", "iat", "event", "subject"]},
        )
    except jwt.PyJWTError as exc:
        raise RecordVerificationError(str(exc)) from exc
