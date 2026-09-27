"""VS17: first-class event registration (open/application/invite-only),
capacity + waitlist, and invite-code redemption. Approval's only durable
side effect is a workspace PARTICIPANT `Membership` -- the same grant
`workspaces.views.WorkspaceMembersView.post` already makes by hand; this
module is just the self-serve front door plus organizer review queue for
that same primitive, not a new identity concept.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from workspaces.models import Membership, Role

from .models import (
    EventApplication,
    EventRegistrationSettings,
    EventStatus,
    RegistrationInviteCode,
    RegistrationMode,
    RegistrationStatus,
)


def get_settings(event):
    settings_obj, _ = EventRegistrationSettings.objects.get_or_create(event=event)
    return settings_obj


def _approved_count(event):
    return EventApplication.objects.filter(event=event, status=RegistrationStatus.APPROVED).count()


def _capacity_available(event, settings_obj):
    return settings_obj.capacity is None or _approved_count(event) < settings_obj.capacity


def _next_waitlist_position(event):
    last = (
        EventApplication.objects.filter(event=event, status=RegistrationStatus.WAITLISTED)
        .order_by("-waitlist_position")
        .values_list("waitlist_position", flat=True)
        .first()
    )
    return (last or 0) + 1


def _grant_membership(event, user):
    Membership.objects.get_or_create(workspace=event.workspace, user=user, role=Role.PARTICIPANT)


@transaction.atomic
def apply_to_event(event, user, *, note="", code=None):
    if event.status != EventStatus.OPEN:
        raise ValidationError({"event": "Registration is not open for this event."})
    if EventApplication.objects.filter(event=event, user=user).exists():
        raise ValidationError({"detail": "You have already applied to this event."})

    settings_obj = get_settings(event)
    invite = None
    if settings_obj.mode == RegistrationMode.INVITE_ONLY:
        if not code:
            raise ValidationError({"code": "An invite code is required."})
        try:
            invite = RegistrationInviteCode.objects.select_for_update(of=("self",)).get(
                event=event, code=code
            )
        except RegistrationInviteCode.DoesNotExist as exc:
            raise ValidationError({"code": "Invalid invite code."}) from exc
        if not invite.is_valid():
            raise ValidationError({"code": "This invite code has been revoked or fully used."})

    if settings_obj.mode == RegistrationMode.APPLICATION:
        application = EventApplication(event=event, user=user, note=note)
        application.full_clean()
        application.save()
        return application

    # OPEN or INVITE_ONLY decide immediately: approve if there's room, else
    # waitlist (if enabled), else the request is rejected outright rather
    # than left pending -- nothing here needs organizer review.
    if _capacity_available(event, settings_obj):
        status, waitlist_position = RegistrationStatus.APPROVED, None
    elif settings_obj.waitlist_enabled:
        status, waitlist_position = RegistrationStatus.WAITLISTED, _next_waitlist_position(event)
    else:
        raise ValidationError({"detail": "Registration is full."})

    application = EventApplication(
        event=event,
        user=user,
        note=note,
        invite_code=invite,
        status=status,
        waitlist_position=waitlist_position,
        decided_at=timezone.now() if status == RegistrationStatus.APPROVED else None,
    )
    application.full_clean()
    application.save()
    if invite is not None:
        invite.use_count += 1
        invite.save(update_fields=["use_count"])
    if status == RegistrationStatus.APPROVED:
        _grant_membership(event, user)
    return application


@transaction.atomic
def decide_application(application, decision, *, actor):
    application = EventApplication.objects.select_for_update(of=("self",)).get(pk=application.pk)
    if application.status not in (RegistrationStatus.PENDING, RegistrationStatus.WAITLISTED):
        raise ValidationError({"detail": "This application has already been decided."})
    if decision == RegistrationStatus.APPROVED:
        application.waitlist_position = None
        _grant_membership(application.event, application.user)
    elif decision == RegistrationStatus.WAITLISTED:
        application.waitlist_position = _next_waitlist_position(application.event)
    elif decision == RegistrationStatus.REJECTED:
        application.waitlist_position = None
    else:
        raise ValidationError({"decision": "Unknown decision."})
    application.status = decision
    application.decided_by = actor
    application.decided_at = timezone.now()
    application.save(
        update_fields=["status", "waitlist_position", "decided_by", "decided_at", "updated_at"]
    )
    return application


@transaction.atomic
def create_invite_code(event, creator, *, max_uses=1):
    invite = RegistrationInviteCode(event=event, created_by=creator, max_uses=max_uses)
    invite.full_clean()
    invite.save()
    return invite


def revoke_invite_code(invite):
    invite.revoked_at = timezone.now()
    invite.save(update_fields=["revoked_at"])
    return invite
