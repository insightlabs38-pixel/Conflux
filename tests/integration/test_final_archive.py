import hashlib
import json
from copy import deepcopy

import pytest
from accounts.models import Session, User
from artifacts.models import Artifact, ArtifactValidation
from artifacts.validators import inspect_artifact
from audit.models import AuditEvent
from awards.models import Award, AwardWinner
from deliberation.models import DeliberationNote, DeliberationRoom, DeliberationStance
from django.core.exceptions import ValidationError
from django.test import Client
from django.utils import timezone
from eligibility.models import EligibilityFinding, EligibilityReview, EligibilityRules
from evaluations.assignment import activate
from evaluations.models import (
    Ballot,
    BallotResponse,
    EvaluationPlan,
    EvaluationPool,
    PoolMembership,
    RubricVersion,
)
from evaluations.normalization import run
from evaluations.results import ranked_results
from events.models import Event
from integrations.archive import build_archive, import_archive
from integrations.final_archive import canonical_bytes
from integrations.migration_preview import preview_archive_import
from integrations.models import ArchiveRestoration
from integrations.signed_archive import sign_archive, verify_signed_archive
from onsite.models import Location, ProjectLocation
from participation.models import Team
from projects.models import Project, Submission, SubmissionVersion
from stages.models import Stage, StageEntry
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def source():
    owner = User.objects.create_user(username="restore-owner", password="unused")
    judge = User.objects.create_user(username="restore-judge", password="unused")
    workspace = Workspace.objects.create(name="Restore", slug="restore")
    Membership.objects.create(workspace=workspace, user=owner, role=Role.ORGANIZER)
    Membership.objects.create(workspace=workspace, user=judge, role=Role.JUDGE)
    event = Event.objects.create(workspace=workspace, name="Source", slug="source")
    stage = Stage.objects.create(event=event, name="Finals")
    team = Team.objects.create(event=event, name="Team")
    StageEntry.objects.enter(stage=stage, subject_type="team", subject_id=str(team.public_id))
    project = Project.objects.create(event=event, name="Winner", created_by=owner, team=team)
    artifact = Artifact.objects.create(
        project=project,
        kind="file",
        visibility="organizer",
        title="Proof",
        status="ready",
        object_key="original-object",
        byte_size=3,
        content_type="text/plain",
        sha256="a" * 64,
        created_by=owner,
    )
    ArtifactValidation.objects.create(
        artifact=artifact, validator="stored_object", outcome="ok", detail="Verified"
    )
    submission = Submission.objects.create(
        project=project,
        stage=stage,
        updated_by=owner,
        status="finalized",
        draft_payload={"artifact_ids": [str(artifact.public_id)]},
    )
    snapshot = {
        "project": str(project.public_id),
        "stage": str(stage.public_id),
        "artifacts": [{"id": str(artifact.public_id), "object_key": artifact.object_key}],
        "draft": submission.draft_payload,
        "forms": [],
        "answer": str(project.public_id),
    }
    version = SubmissionVersion.objects.create(
        submission=submission,
        number=1,
        snapshot=snapshot,
        digest=hashlib.sha256(
            json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        finalized_by=owner,
    )
    submission.current_version = version
    submission.save()
    pool = EvaluationPool.objects.create(event=event, name="Pool")
    PoolMembership.objects.create(pool=pool, judge=judge)
    plan = EvaluationPlan.objects.create(stage=stage, name="Panel", pool=pool)
    rubric = RubricVersion.objects.create(
        plan=plan,
        number=1,
        criteria=[
            {
                "id": "impact",
                "name": "Impact",
                "weight": 1,
                "min_score": 0,
                "max_score": 10,
            }
        ],
    )
    ballot = Ballot.objects.create(
        project=project, rubric_version=rubric, judge=judge, comment="Private review"
    )
    BallotResponse.objects.create(ballot=ballot, criterion_id="impact", score=7)
    normalization = run(plan)
    activate(plan, coverage=1)
    plan.refresh_from_db()
    plan.published_normalization_run = normalization
    plan.tie_breaks = {str(project.id): 1}
    plan.save()
    award = Award.objects.create(
        event=event,
        name="First",
        selection_source="evaluation",
        evaluation_plan=plan,
        published_at=timezone.now(),
    )
    room = DeliberationRoom.objects.create(
        award=award,
        status="finalized",
        quorum=1,
        opened_by=owner,
        finalization={
            "winners": [str(project.public_id)],
            "tally": [{"project": str(project.public_id), "endorse": 1}],
        },
    )
    DeliberationNote.objects.create(room=room, project=project, author=judge, body="Solid")
    DeliberationStance.objects.create(room=room, judge=judge, project=project, stance="endorse")
    AwardWinner.objects.create(
        award=award,
        project=project,
        selected_by=owner,
        source="evaluation",
        evidence={
            "plan": str(plan.public_id),
            "normalization_run": str(normalization.public_id),
            "rank": 1,
            "deliberation": {"room": str(room.public_id), "endorse": 1},
        },
    )
    rules = EligibilityRules.objects.create(event=event, min_team_size=1, require_clearance=True)
    review = EligibilityReview.objects.create(
        project=project, status="cleared", decided_by=owner, decision_note="ok"
    )
    EligibilityFinding.objects.create(
        review=review, code="manual", severity="blocking", message="m", state="waived",
        closed_by=owner, resolution_note="fine",
    )  # fmt: skip
    assert rules.pk
    hall = Location.objects.create(event=event, kind="room", name="Hall", x=0, y=0)
    table = Location.objects.create(event=event, kind="table", name="T1", parent=hall, x=1, y=2)
    ProjectLocation.objects.create(project=project, location=table)
    return workspace, event, owner, judge, project, plan


def restore(workspace, archive, slug="copy"):
    return import_archive(workspace=workspace, archive=archive, name=slug.title(), slug=slug)


def test_restore_live_evidence_results_privacy_and_provenance_without_recomputation(monkeypatch):
    workspace, event, _, _, project, plan = source()
    archive = build_archive(event, mode="final")
    original = deepcopy(archive)
    monkeypatch.setattr(
        "evaluations.normalization.run", lambda *a, **kw: pytest.fail("No recomputation")
    )
    copied = restore(workspace, archive)
    assert archive == original
    assert copied.status == "draft" and not copied.is_public
    copied_project = copied.projects.get(name=project.name)
    copied_plan = EvaluationPlan.objects.get(stage__event=copied)
    assert copied_project.public_id != project.public_id
    before = ranked_results(plan, plan.published_normalization_run)[0]
    after = ranked_results(copied_plan, copied_plan.published_normalization_run)[0]
    assert (after.rank, after.raw_score, after.final_score, after.tie_break) == (
        before.rank,
        before.raw_score,
        before.final_score,
        before.tie_break,
    )
    assert after.project_id == copied_project.pk
    assert Ballot.objects.get(project=copied_project).comment == "Private review"
    winner = AwardWinner.objects.get(award__event=copied)
    assert winner.project == copied_project
    assert winner.evidence["plan"] == str(copied_plan.public_id)
    assert winner.evidence["normalization_run"] == str(
        copied_plan.published_normalization_run.public_id
    )
    copied_room = DeliberationRoom.objects.get(award__event=copied)
    assert winner.evidence["deliberation"]["room"] == str(copied_room.public_id)
    assert copied_room.finalization["winners"] == [str(copied_project.public_id)]
    assert copied_room.finalization["tally"][0]["project"] == str(copied_project.public_id)
    assert copied_room.stances.get().judge.username == "restore-judge"
    placed = copied_project.location_assignment.location
    assert (placed.name, placed.parent.name, placed.event_id) == ("T1", "Hall", copied.pk)
    copied_review = copied_project.eligibility_review
    assert (copied_review.status, copied_review.decided_by.username) == ("cleared", "restore-owner")
    assert copied_review.findings.get().state == "waived"
    assert copied.eligibility_rules.require_clearance
    entry = StageEntry.objects.get(stage__event=copied)
    assert entry.subject_id == str(copied_project.team.public_id)
    version = copied_project.submissions.get().current_version
    assert version.snapshot["project"] == str(copied_project.public_id)
    assert version.snapshot["answer"] == str(project.public_id)
    assert (
        version.digest
        == hashlib.sha256(
            json.dumps(version.snapshot, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    artifact = Artifact.objects.get(project=copied_project)
    assert artifact.status == "pending" and artifact.object_key == ""
    assert inspect_artifact(artifact).outcome == "retry"
    provenance = copied.archive_restoration
    assert provenance.source_archive == original
    assert provenance.source_sha256 == hashlib.sha256(canonical_bytes(original)).hexdigest()
    provenance.source_sha256 = "0" * 64
    with pytest.raises(ValidationError):
        provenance.save()


def test_default_reexport_preserves_final_state_and_supports_multiple_restorations():
    workspace, event, *_ = source()
    copied = restore(workspace, build_archive(event, mode="final"))
    exported = build_archive(copied)
    assert exported == build_archive(copied)
    assert exported["format_version"] == 2 and exported["mode"] == "final"
    assert exported["provenance"][0]["source_sha256"] == copied.archive_restoration.source_sha256
    again = restore(workspace, exported, slug="again")
    reexported = build_archive(again)
    assert reexported["tables"] == exported["tables"]
    assert len(reexported["provenance"]) == 2
    assert not again.is_public
    assert build_archive(copied, mode="config")["format_version"] == 1
    with pytest.raises(ValidationError, match="cannot omit"):
        build_archive(copied, mode="final", sections=["stages"])


@pytest.mark.parametrize(
    "defect",
    [
        "missing-table",
        "duplicate",
        "foreign-reference",
        "unknown-user",
        "nonfinite",
        "bad-score",
        "bad-json",
        "invalid-version",
        "mismatched-run",
    ],
)
def test_invalid_final_archives_roll_back_every_restored_row(defect):
    workspace, event, *_ = source()
    archive = build_archive(event, mode="final")
    tables = archive["tables"]
    if defect == "missing-table":
        del tables["projects.project"]
    elif defect == "duplicate":
        tables["projects.project"].append(deepcopy(tables["projects.project"][0]))
    elif defect == "foreign-reference":
        tables["awards.awardwinner"][0]["fields"]["project"] = (
            "00000000-0000-0000-0000-000000000001"
        )
    elif defect == "unknown-user":
        archive["users"][0]["username"] = "missing-user"
    elif defect == "nonfinite":
        tables["evaluations.ballotresponse"][0]["fields"]["score"] = float("nan")
    elif defect == "bad-score":
        tables["evaluations.ballotresponse"][0]["fields"]["score"] = 100
    elif defect == "bad-json":
        tables["evaluations.normalizationrun"][0]["fields"]["evidence"] = []
    elif defect == "invalid-version":
        archive["format_version"] = True
    elif defect == "mismatched-run":
        tables["evaluations.evaluationplan"][0]["fields"]["mode"] = "pairwise"
    counts = {
        label: __import__("django.apps", fromlist=["apps"]).apps.get_model(label).objects.count()
        for label in tables
    }
    with pytest.raises(ValidationError):
        restore(workspace, archive)
    assert not Event.objects.filter(workspace=workspace, slug="copy").exists()
    assert not ArchiveRestoration.objects.exists()
    for label, count in counts.items():
        assert (
            __import__("django.apps", fromlist=["apps"]).apps.get_model(label).objects.count()
            == count
        )


def test_preview_and_signed_api_preserve_scope_audit_and_rollback():
    workspace, event, owner, judge, *_ = source()
    archive = build_archive(event, mode="final")
    preview = preview_archive_import(
        workspace=workspace, archive=archive, name="Preview", slug="preview"
    )
    assert preview["format_version"] == 2 and preview["ignored_sections"] == []
    assert not Event.objects.filter(slug="preview").exists()
    assert not ArchiveRestoration.objects.exists()
    envelope = sign_archive(archive)
    assert verify_signed_archive(envelope) == archive
    client = Client()
    client.cookies["session"] = Session.issue(judge).token
    url = f"/api/v1/workspaces/{workspace.public_id}/archive/signed/import/"
    body = {"name": "Copy", "slug": "copy", "envelope": envelope}
    assert client.post(url, body, content_type="application/json").status_code == 403
    client.cookies["session"] = Session.issue(owner).token
    created = client.post(url, body, content_type="application/json")
    assert created.status_code == 201, created.content
    copied = Event.objects.get(slug="copy")
    assert AuditEvent.objects.filter(
        action="event.archive_imported", target_id=str(copied.public_id)
    ).exists()
    export_url = f"/api/v1/workspaces/{workspace.public_id}/events/{copied.public_id}/archive/"
    assert client.get(export_url).json()["mode"] == "final"
    assert client.get(export_url, {"mode": "full"}).json()["format_version"] == 1
    assert client.get(export_url, {"mode": "bogus"}).status_code == 400


EXCLUDED_EVENT_MODELS = {
    "accounts.apicredential",
    "events.registrationinvitecode",
    "events.eventapplication",
    "events.announcement",
    "events.participantcheckin",
    "integrations.webhooksubscription",
    "integrations.externalqualifierbinding",
    "integrations.externalqualifierimport",
    "policies.exceptiongrant",
    "governance.deadlineexceptionrequest",
    "participation.marketplaceprofile",
    "presentation.savedpublicsearch",
    "evaluations.judgecoirelationship",
    "evaluations.coirule",
    "communications.eventquestion",
    "communications.moderationreview",
    "communications.bulkreceipt",
    "communications.message",
    "communications.reminder",
    "integrations.archiverestoration",
    "integrations.eventretentionpolicy",
    "taxonomy.taxonomyassignment",
    "onsite.attendance",
}


def test_every_event_owned_model_is_archived_or_explicitly_excluded():
    from django.apps import apps
    from integrations.final_archive_schema import TABLES

    unclassified = (
        {
            model._meta.label_lower
            for model in apps.get_models()
            if any(
                field.is_relation
                and field.many_to_one
                and field.related_model._meta.label_lower == "events.event"
                for field in model._meta.get_fields()
            )
        }
        - set(TABLES)
        - EXCLUDED_EVENT_MODELS
    )
    assert not unclassified, f"Classify new event-owned models for the v2 archive: {unclassified}"
    assert not set(TABLES) & EXCLUDED_EVENT_MODELS
