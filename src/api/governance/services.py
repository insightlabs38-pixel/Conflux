import hashlib
from datetime import timedelta

from audit.services import record_mutation
from core.authz import has_any_role
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from evaluations.models import (
    Assignment,
    Ballot,
    ConflictOfInterest,
    EvaluationPlan,
    NormalizationRun,
)
from policies.models import Action, ExceptionGrant
from presentation.records import _envelope, sign_record
from projects.models import Project
from workspaces.models import Role

from .models import (
    AssignmentResponse,
    AssignmentResponseStatus,
    DeadlineExceptionRequest,
    GovernanceSettings,
    PublicationRequest,
    RequestStatus,
    ResultCorrection,
    RulesAcknowledgement,
    RulesVersion,
    SubmissionReceipt,
)

MAX_EXCEPTION_WINDOW = timedelta(days=7)
DECLINE_PREFIX = "Declined assignment: "


def _is_organizer(user, workspace):
    return has_any_role(user, workspace, Role.ORGANIZER, Role.ADMIN)


def approval_required(event):
    return GovernanceSettings.objects.filter(
        event=event, require_publication_approval=True
    ).exists()


@transaction.atomic
def set_settings(event, actor, *, require_publication_approval):
    settings_row, _ = GovernanceSettings.objects.select_for_update().get_or_create(event=event)
    settings_row.require_publication_approval = bool(require_publication_approval)
    settings_row.save()
    record_mutation(
        actor=actor,
        workspace=event.workspace,
        action="governance.settings_updated",
        target=settings_row,
        metadata={"require_publication_approval": settings_row.require_publication_approval},
    )
    return settings_row


# Rules and acknowledgements


def current_rules(event):
    return event.rules_versions.order_by("-number").first()


@transaction.atomic
def publish_rules(event, actor, *, title, body):
    if not title.strip() or not body.strip():
        raise ValidationError("Rules need a title and a body.")
    event.__class__.objects.select_for_update().get(pk=event.pk)
    number = (
        event.rules_versions.order_by("-number").values_list("number", flat=True).first() or 0
    ) + 1
    version = RulesVersion.objects.create(
        event=event, number=number, title=title.strip(), body=body, created_by=actor
    )
    record_mutation(
        actor=actor,
        workspace=event.workspace,
        action="rules.published",
        target=version,
        metadata={"number": number},
    )
    return version


@transaction.atomic
def acknowledge_rules(event, user, *, number=None):
    version = current_rules(event)
    if version is None:
        raise ValidationError("This event has no published rules.")
    if number is not None and number != version.number:
        raise ValidationError(
            f"Rules version {number} is not current; version {version.number} is."
        )
    ack, created = RulesAcknowledgement.objects.get_or_create(version=version, user=user)
    if created:
        record_mutation(
            actor=user,
            workspace=event.workspace,
            action="rules.acknowledged",
            target=version,
            metadata={"number": version.number},
        )
    return ack, created


# Result publication approval and correction history


def _resolve_tie_breaks(event, tie_breaks):
    if not isinstance(tie_breaks, dict) or not all(
        isinstance(v, int) and not isinstance(v, bool) for v in tie_breaks.values()
    ):
        raise ValidationError("tie_breaks must map project public_id to an integer.")
    resolved = {}
    for public_id, value in tie_breaks.items():
        try:
            project = Project.objects.get(event=event, public_id=public_id)
        except (Project.DoesNotExist, ValueError, ValidationError) as exc:
            raise ValidationError(f"Unknown project {public_id!r} in tie_breaks.") from exc
        resolved[str(project.id)] = value
    return resolved


def apply_publication(plan, run, tie_breaks, actor, *, reason=""):
    """The single write path for publishing results. Records a visible
    correction whenever it replaces an already-published run or tie-break set.
    """
    event = plan.stage.event
    resolved = _resolve_tie_breaks(event, tie_breaks)
    previous_run = plan.published_normalization_run
    is_correction = previous_run is not None and (
        previous_run.pk != run.pk or (plan.tie_breaks or {}) != resolved
    )
    plan.published_normalization_run = run
    plan.tie_breaks = resolved
    plan.full_clean()
    plan.save(update_fields=["published_normalization_run", "tie_breaks", "updated_at"])
    if is_correction:
        ResultCorrection.objects.create(
            plan=plan,
            previous_run=previous_run,
            run=run,
            reason=reason.strip(),
            published_by=actor,
        )
    record_mutation(
        actor=actor,
        workspace=event.workspace,
        action="results.corrected" if is_correction else "results.published",
        target=plan,
        metadata={"normalization_run": run.number},
    )
    return is_correction


@transaction.atomic
def request_publication(plan, actor, *, run, tie_breaks, reason):
    event = plan.stage.event
    if not _is_organizer(actor, event.workspace):
        raise ValidationError("Only an organizer can request result publication.")
    plan = EvaluationPlan.objects.select_for_update().get(pk=plan.pk)
    if run.plan_id != plan.pk:
        raise ValidationError("Normalization run does not belong to this plan.")
    _resolve_tie_breaks(event, tie_breaks)
    if plan.published_normalization_run_id and not reason.strip():
        raise ValidationError("Replacing published results requires a reason.")
    try:
        with transaction.atomic():
            request = PublicationRequest.objects.create(
                plan=plan,
                normalization_run=run,
                tie_breaks=tie_breaks,
                reason=reason.strip(),
                requested_by=actor,
            )
    except IntegrityError as exc:
        raise ValidationError("This plan already has a pending publication request.") from exc
    record_mutation(
        actor=actor,
        workspace=event.workspace,
        action="results.publication_requested",
        target=request,
        metadata={"plan": str(plan.public_id), "normalization_run": run.number},
    )
    return request


@transaction.atomic
def decide_publication(request, actor, *, approve, note=""):
    plan = EvaluationPlan.objects.select_for_update().get(pk=request.plan_id)
    request = PublicationRequest.objects.select_for_update().get(pk=request.pk)
    event = plan.stage.event
    if not _is_organizer(actor, event.workspace):
        raise ValidationError("Only an organizer can decide a publication request.")
    if request.status != RequestStatus.PENDING:
        raise ValidationError("This request has already been decided.")
    if approve and request.requested_by_id == actor.pk:
        raise ValidationError("A different organizer must approve this publication.")
    request.status = RequestStatus.APPROVED if approve else RequestStatus.REJECTED
    request.decided_by = actor
    request.decision_note = note.strip()
    request.decided_at = timezone.now()
    request.save()
    if approve:
        apply_publication(
            plan, request.normalization_run, request.tie_breaks, actor, reason=request.reason
        )
    record_mutation(
        actor=actor,
        workspace=event.workspace,
        action="results.publication_approved" if approve else "results.publication_rejected",
        target=request,
        metadata={"plan": str(plan.public_id)},
    )
    return request


@transaction.atomic
def cancel_publication(request, actor):
    request = PublicationRequest.objects.select_for_update().get(pk=request.pk)
    if request.requested_by_id != actor.pk:
        raise ValidationError("Only the requester can cancel a publication request.")
    if request.status != RequestStatus.PENDING:
        raise ValidationError("This request has already been decided.")
    request.status = RequestStatus.CANCELLED
    request.decided_at = timezone.now()
    request.save()
    record_mutation(
        actor=actor,
        workspace=request.plan.stage.event.workspace,
        action="results.publication_cancelled",
        target=request,
    )
    return request


# Immutable submission receipts


def issue_receipt(version):
    existing = SubmissionReceipt.objects.filter(version=version).first()
    if existing:
        return existing
    submission = version.submission
    project = submission.project
    claims = _envelope(
        "submission_receipt",
        project.event,
        {
            "project": str(project.public_id),
            "project_name": project.name,
            "stage": str(submission.stage.public_id),
            "submission": str(submission.public_id),
            "version": version.number,
            "version_id": str(version.public_id),
            "digest": version.digest,
            "finalized_at": version.finalized_at.isoformat(),
            "receipt_id": hashlib.sha256(
                f"{version.public_id}:{version.digest}".encode()
            ).hexdigest()[:16],
        },
    )
    try:
        with transaction.atomic():
            return SubmissionReceipt.objects.create(version=version, token=sign_record(claims))
    except IntegrityError:
        return SubmissionReceipt.objects.get(version=version)


# Judge assignment accept/decline


@transaction.atomic
def respond_to_assignment(plan, judge, project, *, accept, reason=""):
    version = plan.active_assignment_version
    if version is None:
        raise ValidationError("This plan has no active assignment.")
    try:
        assignment = Assignment.objects.select_for_update().get(
            version=version, judge=judge, project=project
        )
    except Assignment.DoesNotExist as exc:
        raise ValidationError("You are not assigned to this project.") from exc
    existing = AssignmentResponse.objects.filter(assignment=assignment).first()
    if existing and existing.status == AssignmentResponseStatus.DECLINED:
        raise ValidationError("A declined assignment can only be reinstated by an organizer.")
    if not accept:
        if not reason.strip():
            raise ValidationError("Declining requires a reason.")
        if Ballot.objects.filter(rubric_version__plan=plan, judge=judge, project=project).exists():
            raise ValidationError("You have already submitted a ballot for this project.")
    response, _ = AssignmentResponse.objects.update_or_create(
        assignment=assignment,
        defaults={
            "status": AssignmentResponseStatus.ACCEPTED
            if accept
            else AssignmentResponseStatus.DECLINED,
            "reason": reason.strip(),
        },
    )
    event = plan.stage.event
    if not accept:
        # A decline is enforced through the existing recusal: excluded from the
        # next assignment and rejected outright if a ballot is attempted anyway.
        ConflictOfInterest.objects.get_or_create(
            judge=judge,
            project=project,
            defaults={
                "event": event,
                "reason": DECLINE_PREFIX + reason.strip(),
                "declared_by": judge,
            },
        )
    record_mutation(
        actor=judge,
        workspace=event.workspace,
        action="assignment.accepted" if accept else "assignment.declined",
        target=response,
        metadata={"plan": str(plan.public_id), "project": str(project.public_id)},
    )
    return response


# Deadline-exception requests


@transaction.atomic
def request_exception(project, actor, *, reason):
    if not project.memberships.filter(user=actor).exists():
        raise ValidationError("Only project members can request a deadline exception.")
    if not reason.strip():
        raise ValidationError("A reason is required.")
    try:
        with transaction.atomic():
            request = DeadlineExceptionRequest.objects.create(
                event=project.event,
                project=project,
                action=Action.SUBMIT,
                reason=reason.strip(),
                requested_by=actor,
            )
    except IntegrityError as exc:
        raise ValidationError("This project already has a pending exception request.") from exc
    record_mutation(
        actor=actor,
        workspace=project.event.workspace,
        action="exception_request.created",
        target=request,
        metadata={"project": str(project.public_id)},
    )
    return request


@transaction.atomic
def decide_exception(request, actor, *, approve, note="", expires_at=None):
    request = DeadlineExceptionRequest.objects.select_for_update().get(pk=request.pk)
    event = request.event
    if not _is_organizer(actor, event.workspace):
        raise ValidationError("Only an organizer can decide an exception request.")
    if request.status != RequestStatus.PENDING:
        raise ValidationError("This request has already been decided.")
    now = timezone.now()
    grant = None
    if approve:
        if expires_at is None or expires_at <= now:
            raise ValidationError("Approval needs a future expiry.")
        if expires_at > now + MAX_EXCEPTION_WINDOW:
            raise ValidationError("An exception can last at most 7 days.")
        grant = ExceptionGrant.objects.create(
            event=event,
            action=request.action,
            subject_type="project",
            subject_id=str(request.project.public_id),
            reason=f"Requested by participant: {request.reason}",
            granted_by=actor,
            expires_at=expires_at,
        )
        record_mutation(
            actor=actor,
            workspace=event.workspace,
            action="exception_grant.created",
            target=grant,
            event_type="exception_grant.created",
            payload={"event": str(event.public_id)},
        )
    request.status = RequestStatus.APPROVED if approve else RequestStatus.REJECTED
    request.decided_by = actor
    request.decision_note = note.strip()
    request.decided_at = now
    request.grant = grant
    request.save()
    record_mutation(
        actor=actor,
        workspace=event.workspace,
        action="exception_request.approved" if approve else "exception_request.rejected",
        target=request,
        metadata={"project": str(request.project.public_id)},
    )
    return request


@transaction.atomic
def cancel_exception(request, actor):
    request = DeadlineExceptionRequest.objects.select_for_update().get(pk=request.pk)
    if request.requested_by_id != actor.pk:
        raise ValidationError("Only the requester can cancel this request.")
    if request.status != RequestStatus.PENDING:
        raise ValidationError("This request has already been decided.")
    request.status = RequestStatus.CANCELLED
    request.decided_at = timezone.now()
    request.save()
    record_mutation(
        actor=actor,
        workspace=request.event.workspace,
        action="exception_request.cancelled",
        target=request,
    )
    return request


def normalization_run_or_none(plan, public_id):
    try:
        return NormalizationRun.objects.get(plan=plan, public_id=public_id)
    except (NormalizationRun.DoesNotExist, ValueError, ValidationError):
        return None
