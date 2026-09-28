from artifacts.models import Artifact, ArtifactStatus
from audit.services import record_mutation
from communications.models import Message, MessageRecipient
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from participation.models import TeamMembership
from projects.models import ProjectMembership, SubmissionStatus

from .models import (
    EligibilityFinding,
    EligibilityReview,
    EligibilityRules,
    FindingSeverity,
    FindingState,
    ReviewStatus,
)

LIVE_STATES = (FindingState.OPEN, FindingState.ADDRESSED)
UNUSABLE_ARTIFACT_STATES = (ArtifactStatus.REJECTED, ArtifactStatus.PURGED)


def _team_size(project):
    if project.team_id:
        return TeamMembership.objects.filter(team_id=project.team_id).count()
    return ProjectMembership.objects.filter(project=project).count()


def failing_rules(project, rules):
    """{code: message} for every configured rule the project fails right now."""
    failures = {}
    size = _team_size(project)
    if rules.min_team_size is not None and size < rules.min_team_size:
        failures["team_size_min"] = f"Teams need at least {rules.min_team_size} members."
    if rules.max_team_size is not None and size > rules.max_team_size:
        failures["team_size_max"] = f"Teams can have at most {rules.max_team_size} members."
    if rules.require_track and project.track_id is None:
        failures["track_required"] = "Choose a track for this project."
    if (
        rules.require_finalized_submission
        and not project.submissions.filter(status=SubmissionStatus.FINALIZED).exists()
    ):
        failures["finalized_submission"] = "Finalize a submission."
    present = set(
        Artifact.objects.filter(project=project)
        .exclude(status__in=UNUSABLE_ARTIFACT_STATES)
        .values_list("kind", flat=True)
    )
    for kind in rules.required_artifact_kinds:
        if kind not in present:
            failures[f"artifact_{kind}"] = f"Add a {kind.replace('_', ' ')} artifact."
    return failures


def get_rules(event):
    rules = EligibilityRules.objects.filter(event=event).first()
    return rules or EligibilityRules(event=event)


def get_review(project):
    review, _ = EligibilityReview.objects.get_or_create(project=project)
    return review


def _touch(review, status=None):
    if status is not None:
        review.status = status
    review.revision += 1
    review.save()


def notify(project, actor, subject, body):
    users = [
        m.user for m in ProjectMembership.objects.filter(project=project).select_related("user")
    ]
    message = Message(
        event=project.event,
        sent_by=actor,
        subject=subject,
        body=body,
        audience_kind="eligibility_review",
        audience_params={"project": str(project.public_id)},
        recipient_count=len(users),
    )
    message.full_clean()
    message.save()
    MessageRecipient.objects.bulk_create([MessageRecipient(message=message, user=u) for u in users])


def _audit(actor, review, action, **metadata):
    record_mutation(
        actor=actor,
        workspace=review.project.event.workspace,
        action=action,
        target=review,
        metadata={
            "project": str(review.project.public_id),
            "revision": review.revision,
            **metadata,
        },
        event_type=action,
        payload={
            "event": str(review.project.event.public_id),
            "project": str(review.project.public_id),
        },
    )


def _live_blocking(review):
    return review.findings.filter(severity=FindingSeverity.BLOCKING, state__in=LIVE_STATES)


@transaction.atomic
def sync_checks(project, actor):
    """Reconcile automated findings with the rules as they stand now."""
    review = EligibilityReview.objects.select_for_update().get(pk=get_review(project).pk)
    rules = get_rules(project.event)
    failures = failing_rules(project, rules) if rules.pk else {}
    live = {f.code: f for f in review.findings.filter(automated=True, state__in=LIVE_STATES)}
    waived = set(
        review.findings.filter(automated=True, state=FindingState.WAIVED).values_list(
            "code", flat=True
        )
    )
    opened, closed = [], []
    for code, message in failures.items():
        if code not in live and code not in waived:
            EligibilityFinding.objects.create(
                review=review,
                code=code,
                automated=True,
                severity=FindingSeverity.BLOCKING,
                message=message,
            )
            opened.append(code)
    now = timezone.now()
    for code, finding in live.items():
        if code not in failures:
            finding.state, finding.closed_at = FindingState.RESOLVED, now
            finding.resolution_note = "The requirement is now met."
            finding.save()
            closed.append(code)
    status = review.status
    if _live_blocking(review).exists() and status in (
        ReviewStatus.PENDING,
        ReviewStatus.CLEARED,
    ):
        status = ReviewStatus.NEEDS_REMEDIATION
    if opened or closed or status != review.status:
        _touch(review, status)
        _audit(actor, review, "eligibility.checked", opened=opened, auto_resolved=closed)
        if opened:
            notify(
                project,
                actor,
                "Eligibility review: action needed",
                "Open eligibility findings need your attention: "
                + "; ".join(failures[c] for c in opened),
            )
    return review


@transaction.atomic
def raise_finding(project, actor, *, message, severity):
    review = EligibilityReview.objects.select_for_update().get(pk=get_review(project).pk)
    finding = EligibilityFinding(review=review, code="manual", severity=severity, message=message)
    finding.full_clean()
    finding.save()
    status = review.status
    if severity == FindingSeverity.BLOCKING and status in (
        ReviewStatus.PENDING,
        ReviewStatus.CLEARED,
    ):
        status = ReviewStatus.NEEDS_REMEDIATION
    _touch(review, status)
    _audit(actor, review, "eligibility.finding_raised", finding=str(finding.public_id))
    notify(project, actor, "Eligibility review: action needed", message)
    return finding


@transaction.atomic
def respond(finding, user, response):
    review = EligibilityReview.objects.select_for_update().get(pk=finding.review_id)
    finding = EligibilityFinding.objects.select_for_update().get(pk=finding.pk)
    if review.status == ReviewStatus.INELIGIBLE:
        raise ValidationError("This project has been ruled ineligible.")
    if finding.state != FindingState.OPEN:
        raise ValidationError("Only an open finding can be answered.")
    if not response.strip():
        raise ValidationError({"response": "Describe what you changed."})
    finding.state = FindingState.ADDRESSED
    finding.participant_response = response
    finding.responded_by = user
    finding.addressed_at = timezone.now()
    finding.save()
    status = review.status
    if (
        status == ReviewStatus.NEEDS_REMEDIATION
        and not review.findings.filter(
            severity=FindingSeverity.BLOCKING, state=FindingState.OPEN
        ).exists()
    ):
        status = ReviewStatus.PENDING
    _touch(review, status)
    _audit(user, review, "eligibility.finding_addressed", finding=str(finding.public_id))
    return finding


@transaction.atomic
def close_finding(finding, actor, *, state, note):
    if state not in (FindingState.RESOLVED, FindingState.WAIVED):
        raise ValidationError({"state": "Close a finding as resolved or waived."})
    if state == FindingState.WAIVED and not note.strip():
        raise ValidationError({"note": "A waiver needs a reason."})
    review = EligibilityReview.objects.select_for_update().get(pk=finding.review_id)
    finding = EligibilityFinding.objects.select_for_update().get(pk=finding.pk)
    if finding.state not in LIVE_STATES:
        raise ValidationError("This finding is already closed.")
    finding.state, finding.resolution_note = state, note
    finding.closed_by, finding.closed_at = actor, timezone.now()
    finding.save()
    _touch(review)
    _audit(actor, review, "eligibility.finding_closed", finding=str(finding.public_id), state=state)
    return finding


@transaction.atomic
def decide(project, actor, *, decision, note):
    if decision not in ReviewStatus.values:
        raise ValidationError({"decision": "Unknown decision."})
    if decision == ReviewStatus.INELIGIBLE and not note.strip():
        raise ValidationError({"note": "An ineligibility ruling needs a reason."})
    review = sync_checks(project, actor)
    review = EligibilityReview.objects.select_for_update().get(pk=review.pk)
    if decision == ReviewStatus.CLEARED and _live_blocking(review).exists():
        raise ValidationError("Close or waive every blocking finding before clearing.")
    before = review.status
    review.decision_note = note
    review.decided_by, review.decided_at = actor, timezone.now()
    _touch(review, decision)
    _audit(actor, review, "eligibility.decided", before=before, after=decision)
    notify(
        project,
        actor,
        f"Eligibility review: {ReviewStatus(decision).label.lower()}",
        note or f"Your project's eligibility status is now {ReviewStatus(decision).label.lower()}.",
    )
    return review


def judgeable(queryset, event):
    """Projects an organizer has not ruled out (or, when required, has cleared)."""
    rules = EligibilityRules.objects.filter(event=event, require_clearance=True).exists()
    if rules:
        return queryset.filter(eligibility_review__status=ReviewStatus.CLEARED)
    return queryset.exclude(eligibility_review__status=ReviewStatus.INELIGIBLE)


def ensure_project_eligible(project):
    from projects.models import Project

    if not judgeable(Project.objects.filter(pk=project.pk), project.event).exists():
        raise ValidationError("Project has not passed the eligibility review.")
