import math

from audit.services import record_mutation
from awards.models import AwardWinner
from awards.services import select_winner
from communications.models import Message, MessageRecipient
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from evaluations.eligibility import eligible_projects
from evaluations.models import Ballot, PairwiseComparison
from projects.models import Project
from workspaces.models import Membership, Role

from .models import DeliberationNote, DeliberationRoom, DeliberationStance, RoomStatus, Stance


def _plan(room_or_award):
    award = getattr(room_or_award, "award", room_or_award)
    return award.evaluation_plan


def panel_judges(plan):
    """Judges with any live evaluation on the plan."""
    ids = set(
        Ballot.objects.filter(
            rubric_version__plan=plan, is_calibration=False, judge__isnull=False
        ).values_list("judge_id", flat=True)
    ) | set(PairwiseComparison.objects.filter(plan=plan).values_list("judge_id", flat=True))
    return ids


def has_evaluated(plan, judge, project):
    return (
        Ballot.objects.filter(
            rubric_version__plan=plan, judge=judge, project=project, is_calibration=False
        ).exists()
        or PairwiseComparison.objects.filter(plan=plan, judge=judge)
        .filter(Q(project_a=project) | Q(project_b=project))
        .exists()
    )


def is_panelist(room, user):
    return (
        user.id in panel_judges(_plan(room))
        and Membership.objects.filter(
            workspace=room.award.event.workspace, user=user, role=Role.JUDGE
        ).exists()
    )


def _lock(room):
    return DeliberationRoom.objects.select_for_update().get(pk=room.pk)


def _require_open(room):
    if room.status != RoomStatus.OPEN:
        raise ValidationError("This room is no longer accepting input.")


@transaction.atomic
def open_room(award, actor, quorum=None):
    plan = award.evaluation_plan
    if plan is None:
        raise ValidationError("Deliberation needs an award selected from an evaluation plan.")
    if award.published_at:
        raise ValidationError("Published awards cannot be deliberated.")
    panel = panel_judges(plan)
    if not panel:
        raise ValidationError("No judge has evaluated this plan yet.")
    quorum = quorum or max(1, math.ceil(len(panel) / 2))
    if not 1 <= quorum <= len(panel):
        raise ValidationError({"quorum": f"Quorum must be between 1 and {len(panel)}."})
    if DeliberationRoom.objects.filter(award=award).exists():
        raise ValidationError("This award already has a room.")
    room = DeliberationRoom.objects.create(award=award, quorum=quorum, opened_by=actor)
    users = list(
        Membership.objects.filter(
            workspace=award.event.workspace, role=Role.JUDGE, user_id__in=panel
        ).select_related("user")
    )
    message = Message.objects.create(
        event=award.event,
        sent_by=actor,
        subject=f"Deliberation open: {award.name}",
        body="Share notes and record endorsements on the projects you evaluated.",
        audience_kind="deliberation",
        audience_params={"award": str(award.public_id)},
        recipient_count=len(users),
    )
    MessageRecipient.objects.bulk_create(
        [MessageRecipient(message=message, user=m.user) for m in users]
    )
    record_mutation(
        actor=actor,
        workspace=award.event.workspace,
        action="deliberation.opened",
        target=room,
        metadata={"award": str(award.public_id), "quorum": quorum, "panel": len(panel)},
    )
    return room


def _eligible_project(room, project_public_id):
    project = Project.objects.filter(event=room.award.event, public_id=project_public_id).first()
    if project is None or not eligible_projects(_plan(room)).filter(pk=project.pk).exists():
        raise ValidationError({"project": "Unknown project for this deliberation."})
    return project


@transaction.atomic
def add_note(room, judge, body, project_public_id=None):
    room = _lock(room)
    _require_open(room)
    if not is_panelist(room, judge):
        raise PermissionError
    project = None
    if project_public_id:
        project = _eligible_project(room, project_public_id)
        if not has_evaluated(_plan(room), judge, project):
            raise PermissionError
    if not body.strip():
        raise ValidationError({"body": "A note cannot be empty."})
    note = DeliberationNote.objects.create(room=room, project=project, author=judge, body=body)
    record_mutation(
        actor=judge,
        workspace=room.award.event.workspace,
        action="deliberation.note_added",
        target=room,
        metadata={"note": str(note.public_id), "project": project_public_id},
    )
    return note


@transaction.atomic
def set_stance(room, judge, project_public_id, stance, rationale):
    room = _lock(room)
    _require_open(room)
    if not is_panelist(room, judge):
        raise PermissionError
    project = _eligible_project(room, project_public_id)
    if not has_evaluated(_plan(room), judge, project):
        raise PermissionError
    existing = DeliberationStance.objects.filter(room=room, judge=judge, project=project).first()
    before = existing.stance if existing else None
    obj, _ = DeliberationStance.objects.update_or_create(
        room=room, judge=judge, project=project, defaults={"stance": stance, "rationale": rationale}
    )
    record_mutation(
        actor=judge,
        workspace=room.award.event.workspace,
        action="deliberation.stance_set",
        target=room,
        metadata={"project": project_public_id, "before": before, "after": stance},
    )
    return obj


def tally(room):
    rows = {}
    for item in room.stances.select_related("project"):
        row = rows.setdefault(
            item.project_id,
            {
                "project": str(item.project.public_id),
                "project_name": item.project.name,
                Stance.ENDORSE: 0,
                Stance.OBJECT: 0,
                Stance.ABSTAIN: 0,
            },
        )
        row[item.stance] += 1
    result = []
    for row in rows.values():
        row["recommended"] = (
            row[Stance.ENDORSE] >= room.quorum and row[Stance.ENDORSE] > row[Stance.OBJECT]
        )
        result.append(row)
    return sorted(result, key=lambda r: (-r[Stance.ENDORSE], r["project_name"]))


@transaction.atomic
def close_room(room, actor):
    room = _lock(room)
    _require_open(room)
    room.status, room.closed_at = RoomStatus.CLOSED, timezone.now()
    room.save()
    record_mutation(
        actor=actor,
        workspace=room.award.event.workspace,
        action="deliberation.closed",
        target=room,
        metadata={"award": str(room.award.public_id)},
    )
    return room


@transaction.atomic
def finalize(room, actor, winner_public_ids, override_reason=""):
    room = _lock(room)
    if room.status == RoomStatus.FINALIZED:
        raise ValidationError("This room is already finalized.")
    award = room.award
    if AwardWinner.objects.filter(award=award).exists():
        raise ValidationError("This award already has winners.")
    if len(winner_public_ids) != award.winner_count or len(set(winner_public_ids)) != len(
        winner_public_ids
    ):
        raise ValidationError(
            {"winners": f"Choose exactly {award.winner_count} distinct projects."}
        )
    summary = {row["project"]: row for row in tally(room)}
    chosen = []
    for public_id in winner_public_ids:
        project = _eligible_project(room, public_id)
        row = summary.get(str(project.public_id))
        recommended = bool(row and row["recommended"])
        if not recommended and not override_reason.strip():
            raise ValidationError(
                {"winners": f"{project.name} is not recommended by the panel; give a reason."}
            )
        chosen.append((project, recommended, row))
    for project, recommended, row in chosen:
        select_winner(
            award=award,
            project=project,
            actor=actor,
            override_reason=override_reason,
            extra_evidence={
                "deliberation": {
                    "room": str(room.public_id),
                    "quorum": room.quorum,
                    "endorse": row[Stance.ENDORSE] if row else 0,
                    "object": row[Stance.OBJECT] if row else 0,
                    "recommended": recommended,
                }
            },
        )
    room.status, room.finalized_at = RoomStatus.FINALIZED, timezone.now()
    room.finalization = {
        "winners": winner_public_ids,
        "override_reason": override_reason,
        "tally": list(summary.values()),
    }
    room.save()
    record_mutation(
        actor=actor,
        workspace=award.event.workspace,
        action="deliberation.finalized",
        target=room,
        metadata={"award": str(award.public_id), "winners": winner_public_ids},
    )
    return room
