from audit.services import record_mutation
from core.authz import has_any_role
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from workspaces.models import Role

from .models import (
    MAX_ACTIVE_REQUESTS_PER_PROJECT,
    MentorRequest,
    OfficeHourSignup,
    OfficeHourSlot,
    RequestStatus,
)

ACTIVE_STATUSES = (RequestStatus.PENDING, RequestStatus.CLAIMED)


def _is_mentor_like(user, workspace):
    return has_any_role(user, workspace, Role.MENTOR, Role.ORGANIZER, Role.ADMIN)


@transaction.atomic
def create_request(project, actor, *, track=None, topic, urgency):
    if not project.memberships.filter(user=actor).exists():
        raise ValidationError("Only project members can request mentorship.")
    active = MentorRequest.objects.select_for_update().filter(
        project=project, status__in=ACTIVE_STATUSES
    )
    if active.count() >= MAX_ACTIVE_REQUESTS_PER_PROJECT:
        raise ValidationError(
            f"This project already has {MAX_ACTIVE_REQUESTS_PER_PROJECT} open requests; "
            "resolve or cancel one before asking again."
        )
    request = MentorRequest(
        event=project.event,
        project=project,
        track=track,
        topic=topic,
        urgency=urgency,
        created_by=actor,
    )
    request.full_clean()
    request.save()
    record_mutation(
        actor=actor,
        workspace=project.event.workspace,
        action="mentor_request.created",
        target=request,
        metadata={"project": str(project.public_id), "urgency": request.urgency},
    )
    return request


@transaction.atomic
def claim_request(request, actor):
    workspace = request.event.workspace
    if not _is_mentor_like(actor, workspace):
        raise ValidationError("Only a mentor or organizer can claim a request.")
    request = MentorRequest.objects.select_for_update().get(pk=request.pk)
    if request.status != RequestStatus.PENDING:
        raise ValidationError("Only a pending request can be claimed.")
    request.status = RequestStatus.CLAIMED
    request.claimed_by = actor
    request.claimed_at = timezone.now()
    request.save(update_fields=["status", "claimed_by", "claimed_at", "updated_at"])
    record_mutation(
        actor=actor,
        workspace=workspace,
        action="mentor_request.claimed",
        target=request,
        metadata={"claimed_by": actor.username},
    )
    return request


@transaction.atomic
def reassign_request(request, actor, *, to_mentor):
    workspace = request.event.workspace
    if not has_any_role(actor, workspace, Role.ORGANIZER, Role.ADMIN):
        raise ValidationError("Only an organizer can reassign a request.")
    if not _is_mentor_like(to_mentor, workspace):
        raise ValidationError("The new assignee must hold the mentor role in this workspace.")
    request = MentorRequest.objects.select_for_update().get(pk=request.pk)
    if request.status not in (RequestStatus.PENDING, RequestStatus.CLAIMED):
        raise ValidationError("Only a pending or claimed request can be reassigned.")
    request.status = RequestStatus.CLAIMED
    request.claimed_by = to_mentor
    request.claimed_at = timezone.now()
    request.save(update_fields=["status", "claimed_by", "claimed_at", "updated_at"])
    record_mutation(
        actor=actor,
        workspace=workspace,
        action="mentor_request.reassigned",
        target=request,
        metadata={"claimed_by": to_mentor.username},
    )
    return request


@transaction.atomic
def resolve_request(request, actor, *, note=""):
    workspace = request.event.workspace
    request = MentorRequest.objects.select_for_update().get(pk=request.pk)
    is_claimant = request.claimed_by_id == actor.pk
    if not is_claimant and not has_any_role(actor, workspace, Role.ORGANIZER, Role.ADMIN):
        raise ValidationError("Only the claiming mentor or an organizer can resolve this.")
    if request.status != RequestStatus.CLAIMED:
        raise ValidationError("Only a claimed request can be resolved.")
    request.status = RequestStatus.RESOLVED
    request.resolved_at = timezone.now()
    request.resolution_note = note.strip()
    request.save(update_fields=["status", "resolved_at", "resolution_note", "updated_at"])
    record_mutation(
        actor=actor,
        workspace=workspace,
        action="mentor_request.resolved",
        target=request,
        metadata={"note": request.resolution_note},
    )
    return request


@transaction.atomic
def cancel_request(request, actor):
    workspace = request.event.workspace
    is_requester = request.created_by_id == actor.pk
    if not is_requester and not has_any_role(actor, workspace, Role.ORGANIZER, Role.ADMIN):
        raise ValidationError("Only the requester or an organizer can cancel this.")
    request = MentorRequest.objects.select_for_update().get(pk=request.pk)
    if request.status not in ACTIVE_STATUSES:
        raise ValidationError("Only a pending or claimed request can be cancelled.")
    request.status = RequestStatus.CANCELLED
    request.save(update_fields=["status", "updated_at"])
    record_mutation(
        actor=actor, workspace=workspace, action="mentor_request.cancelled", target=request
    )
    return request


@transaction.atomic
def sign_up_for_office_hours(slot, project, actor):
    if not project.memberships.filter(user=actor).exists():
        raise ValidationError("Only project members can sign up.")
    slot = OfficeHourSlot.objects.select_for_update().get(pk=slot.pk)
    if slot.ends_at <= timezone.now():
        raise ValidationError("This office-hours slot has already ended.")
    if slot.signups.filter(project=project).exists():
        raise ValidationError("This project already signed up for this slot.")
    if slot.signups.count() >= slot.capacity:
        raise ValidationError("This office-hours slot is full.")
    signup = OfficeHourSignup(slot=slot, project=project, created_by=actor)
    signup.full_clean()
    signup.save()
    record_mutation(
        actor=actor,
        workspace=slot.event.workspace,
        action="office_hours.signed_up",
        target=signup,
        metadata={"slot": str(slot.public_id), "project": str(project.public_id)},
    )
    return signup


@transaction.atomic
def cancel_office_hours_signup(signup, actor):
    workspace = signup.slot.event.workspace
    is_member = signup.project.memberships.filter(user=actor).exists()
    if not is_member and not has_any_role(actor, workspace, Role.ORGANIZER, Role.ADMIN):
        raise ValidationError("Only a project member or an organizer can cancel this signup.")
    record_mutation(
        actor=actor,
        workspace=workspace,
        action="office_hours.signup_cancelled",
        target=signup,
        metadata={"slot": str(signup.slot.public_id), "project": str(signup.project.public_id)},
    )
    signup.delete()
