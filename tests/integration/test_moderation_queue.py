import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from accounts.models import Session, User
from artifacts.models import Artifact, ArtifactStatus, ArtifactValidation
from audit.models import AuditEvent
from communications.models import ModerationReview
from community.models import AbuseSignal, AbuseSignalType, Comment, VotingPlan
from django.db import close_old_connections, connection, connections
from django.test import Client
from django.utils import timezone
from events.models import Event, EventApplication, EventStatus, RegistrationStatus
from projects.models import Project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


@pytest.fixture
def case():
    actor = User.objects.create_user(username="review-organizer")
    author = User.objects.create_user(username="review-author")
    applicant = User.objects.create_user(username="review-applicant")
    workspace = Workspace.objects.create(name="Review", slug="review")
    Membership.objects.create(workspace=workspace, user=actor, role=Role.ORGANIZER)
    Membership.objects.create(workspace=workspace, user=author, role=Role.PARTICIPANT)
    event = Event.objects.create(workspace=workspace, name="Review", slug="review")
    project = Project.objects.create(event=event, name="First", created_by=author)
    second = Project.objects.create(event=event, name="Second", created_by=author)
    artifact = Artifact.objects.create(
        project=project,
        kind="file",
        visibility="public",
        title="File",
        object_key="files/one",
        sha256="a" * 64,
        status=ArtifactStatus.REJECTED,
        created_by=author,
    )
    duplicate = Artifact.objects.create(
        project=second,
        kind="file",
        visibility="public",
        title="Other",
        object_key="files/two",
        sha256="a" * 64,
        status=ArtifactStatus.READY,
        created_by=author,
    )
    validation = ArtifactValidation.objects.create(
        artifact=artifact, validator="mime", outcome="blocked", detail="Unsafe type"
    )
    plan = VotingPlan.objects.create(
        event=event, opens_at=timezone.now(), closes_at=timezone.now() + timedelta(days=1)
    )
    signal = AbuseSignal.objects.create(
        plan=plan,
        signal_type=AbuseSignalType.DUPLICATE_VOTE_ATTEMPT,
        detail="Already voted",
        evidence={"attempts": 2},
    )
    comment = Comment.objects.create(project=project, author=author, body="Please review")
    application = EventApplication.objects.create(event=event, user=applicant, note="Application")
    client = Client()
    client.cookies["session"] = Session.issue(actor).token
    url = (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/operations/moderation/"
    )
    return dict(
        actor=actor,
        author=author,
        applicant=applicant,
        workspace=workspace,
        event=event,
        project=project,
        artifact=artifact,
        duplicate=duplicate,
        validation=validation,
        signal=signal,
        comment=comment,
        application=application,
        client=client,
        url=url,
    )


def section(c, kind):
    response = c["client"].get(c["url"], {"kind": kind})
    assert response.status_code == 200, response.content
    return response.json()["sections"][0]


def review(c, item, disposition, **changes):
    data = {key: item[key] for key in ("kind", "source_key", "evidence_digest")}
    data.update(disposition=disposition, note="Reviewed the evidence", **changes)
    return c["client"].post(c["url"] + "reviews/", data=data, content_type="application/json")


def test_unified_queue_is_live_scoped_and_read_only(case):
    response = case["client"].get(case["url"])
    assert response.status_code == 200, response.content
    sections = response.json()["sections"]
    assert [s["kind"] for s in sections] == [
        "duplicate",
        "voting",
        "content",
        "artifact",
        "eligibility",
    ]
    assert [s["count"] for s in sections] == [1] * 5
    assert sections[0]["items"][0]["evidence"]["project_count"] == 2
    assert sections[3]["items"][0]["evidence"]["checks"][0]["outcome"] == "blocked"
    assert all(not s["items"][0]["review_current"] for s in sections)
    assert not ModerationReview.objects.exists()
    assert not AuditEvent.objects.exists()


@pytest.mark.parametrize(
    "kind,disposition",
    [
        ("duplicate", "dismiss"),
        ("voting", "resolve"),
        ("content", "hide"),
        ("artifact", "acknowledge"),
        ("eligibility", "approve"),
    ],
)
def test_reviews_preserve_evidence_and_apply_only_authorized_actions(case, kind, disposition):
    item = section(case, kind)["items"][0]
    response = review(case, item, disposition)
    assert response.status_code == 201, response.content
    stored = ModerationReview.objects.get()
    assert stored.evidence == item["evidence"]
    assert stored.evidence_digest == item["evidence_digest"]
    assert stored.actor_id == case["actor"].pk
    assert AuditEvent.objects.filter(action="moderation.reviewed").count() == 1
    assert case["client"].get(case["url"] + "reviews/").json()[0]["public_id"] == str(
        stored.public_id
    )
    if kind == "voting":
        case["signal"].refresh_from_db()
        assert case["signal"].resolved_by_id == case["actor"].pk
        assert section(case, kind)["count"] == 0
        assert AuditEvent.objects.filter(action="community_abuse.resolved").exists()
    elif kind == "content":
        case["comment"].refresh_from_db()
        assert case["comment"].hidden_by_id == case["actor"].pk
        assert section(case, kind)["count"] == 0
    elif kind == "eligibility":
        case["application"].refresh_from_db()
        assert case["application"].status == RegistrationStatus.APPROVED
        assert Membership.objects.filter(
            workspace=case["workspace"], user=case["applicant"], role=Role.PARTICIPANT
        ).exists()
        assert section(case, kind)["count"] == 0
    else:
        item = section(case, kind)["items"][0]
        assert item["review_current"] is True
        assert item["latest_review"]["disposition"] == disposition
    case["artifact"].refresh_from_db()
    assert case["artifact"].status == ArtifactStatus.REJECTED
    assert case["validation"].outcome == "blocked"


@pytest.mark.parametrize("decision,expected", [("reject", "rejected"), ("waitlist", "waitlisted")])
def test_application_decisions_use_existing_registration_semantics(case, decision, expected):
    response = review(case, section(case, "eligibility")["items"][0], decision)
    assert response.status_code == 201
    case["application"].refresh_from_db()
    assert case["application"].status == expected
    assert not Membership.objects.filter(
        workspace=case["workspace"], user=case["applicant"]
    ).exists()


@pytest.mark.parametrize("kind", ["duplicate", "voting", "content", "artifact", "eligibility"])
def test_changed_evidence_is_rejected_and_existing_review_becomes_stale(case, kind):
    item = section(case, kind)["items"][0]
    assert review(case, item, "escalate").status_code == 201
    if kind == "duplicate":
        Artifact.objects.filter(pk=case["duplicate"].pk).update(sha256="b" * 64)
    elif kind == "voting":
        AbuseSignal.objects.filter(pk=case["signal"].pk).update(detail="Changed signal")
    elif kind == "content":
        Comment.objects.filter(pk=case["comment"].pk).update(body="Changed body")
    elif kind == "artifact":
        ArtifactValidation.objects.create(
            artifact=case["artifact"], validator="mime", outcome="warning", detail="New evidence"
        )
    else:
        EventApplication.objects.filter(pk=case["application"].pk).update(
            note="Changed application"
        )
    assert review(case, item, "escalate").status_code == 409
    assert ModerationReview.objects.count() == 1
    current = section(case, kind)
    if current["items"]:
        assert current["items"][0]["review_current"] is False


def test_latest_validation_per_validator_controls_artifact_queue(case):
    case["artifact"].status = ArtifactStatus.READY
    case["artifact"].save()
    ArtifactValidation.objects.create(
        artifact=case["artifact"], validator="mime", outcome="ok", detail="Safe now"
    )
    assert section(case, "artifact")["count"] == 0
    ArtifactValidation.objects.create(
        artifact=case["artifact"], validator="reachability", outcome="retry", detail="Offline"
    )
    item = section(case, "artifact")["items"][0]
    assert {check["validator"]: check["outcome"] for check in item["evidence"]["checks"]} == {
        "mime": "ok",
        "reachability": "retry",
    }


def test_cross_event_sources_and_duplicate_hashes_do_not_mix(case):
    foreign = Event.objects.create(workspace=case["workspace"], name="Other", slug="other")
    project = Project.objects.create(event=foreign, name="Other project", created_by=case["actor"])
    comment = Comment.objects.create(project=project, author=case["actor"], body="Foreign")
    Artifact.objects.create(
        project=project,
        kind="file",
        visibility="public",
        title="Same hash",
        sha256="c" * 64,
        created_by=case["actor"],
    )
    Artifact.objects.filter(pk=case["duplicate"].pk).update(sha256="c" * 64)
    assert section(case, "duplicate")["count"] == 0
    item = section(case, "content")["items"][0]
    item["source_key"] = str(comment.public_id)
    assert review(case, item, "hide").status_code == 409
    assert not ModerationReview.objects.exists()
    comment.refresh_from_db()
    assert comment.hidden_at is None


def test_permissions_and_archive_fail_closed(case):
    assert Client().get(case["url"]).status_code in (401, 403)
    participant = Client()
    participant.cookies["session"] = Session.issue(case["author"]).token
    assert participant.get(case["url"]).status_code == 403
    assert (
        participant.post(
            case["url"] + "reviews/", data={}, content_type="application/json"
        ).status_code
        == 403
    )
    item = section(case, "content")["items"][0]
    Event.objects.filter(pk=case["event"].pk).update(status=EventStatus.ARCHIVED)
    assert review(case, item, "hide").status_code == 400
    assert not ModerationReview.objects.exists()
    assert section(case, "content")["count"] == 1


def test_invalid_disposition_cannot_override_artifact_rejection(case):
    item = section(case, "artifact")["items"][0]
    assert review(case, item, "approve").status_code == 400
    assert review(case, item, "acknowledge", evidence_digest="bogus").status_code == 400
    assert review(case, item, "acknowledge", force=True).status_code == 400
    assert not ModerationReview.objects.exists()


def test_pagination_is_bounded_and_does_not_repeat_items(case):
    Comment.objects.bulk_create(
        [
            Comment(project=case["project"], author=case["author"], body=f"Review {n}")
            for n in range(55)
        ]
    )
    first = section(case, "content")
    assert first["count"] == 56
    assert len(first["items"]) == 50
    assert first["next_offset"] == 50
    second = (
        case["client"].get(case["url"], {"kind": "content", "offset": 50}).json()["sections"][0]
    )
    assert len(second["items"]) == 6
    assert second["next_offset"] is None
    assert not {item["source_key"] for item in first["items"]} & {
        item["source_key"] for item in second["items"]
    }
    assert case["client"].get(case["url"], {"offset": -1}).status_code == 400
    assert case["client"].get(case["url"], {"kind": "bad"}).status_code == 400


@pytest.mark.parametrize(
    "kind,disposition", [("content", "hide"), ("voting", "resolve"), ("eligibility", "approve")]
)
def test_failed_review_audit_rolls_back_source_action(case, monkeypatch, kind, disposition):
    item = section(case, kind)["items"][0]
    from communications import moderation

    original = moderation.record_mutation

    def fail(**kwargs):
        if kwargs["action"] == "moderation.reviewed":
            raise RuntimeError("audit unavailable")
        return original(**kwargs)

    monkeypatch.setattr(moderation, "record_mutation", fail)
    with pytest.raises(RuntimeError, match="audit unavailable"):
        review(case, item, disposition)
    case["comment"].refresh_from_db()
    assert case["comment"].hidden_at is None
    case["signal"].refresh_from_db()
    case["application"].refresh_from_db()
    assert case["signal"].resolved_at is None
    assert case["application"].status == RegistrationStatus.PENDING
    assert not Membership.objects.filter(
        user=case["applicant"], workspace=case["workspace"]
    ).exists()
    assert not ModerationReview.objects.exists()
    assert not AuditEvent.objects.exists()


def test_other_workspace_organizer_cannot_inspect_queue_or_history(case):
    workspace = Workspace.objects.create(name="Foreign", slug="foreign")
    actor = User.objects.create_user(username="foreign-organizer")
    Membership.objects.create(workspace=workspace, user=actor, role=Role.ORGANIZER)
    client = Client()
    client.cookies["session"] = Session.issue(actor).token
    assert client.get(case["url"]).status_code == 403
    assert client.get(case["url"] + "reviews/").status_code == 403
    assert (
        client.post(case["url"] + "reviews/", data={}, content_type="application/json").status_code
        == 403
    )


def test_identical_hashes_within_one_project_are_not_duplicate_projects(case):
    case["duplicate"].project = case["project"]
    case["duplicate"].save()
    assert section(case, "duplicate")["count"] == 0


def test_history_is_immutable_and_latest_review_is_selected(case):
    item = section(case, "content")["items"][0]
    assert review(case, item, "escalate").status_code == 201
    assert review(case, item, "dismiss").status_code == 201
    updated = section(case, "content")["items"][0]
    assert updated["latest_review"]["disposition"] == "dismiss"
    history = case["client"].get(case["url"] + "reviews/", {"kind": "content"}).json()
    assert [row["disposition"] for row in history] == ["dismiss", "escalate"]
    assert all(row["evidence"] == item["evidence"] for row in history)
    assert (
        case["client"]
        .patch(case["url"] + "reviews/", data={}, content_type="application/json")
        .status_code
        == 405
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(connection.vendor != "postgresql", reason="Requires PostgreSQL row locks")
def test_concurrent_hide_records_one_source_action(case):
    item = section(case, "content")["items"][0]
    session = case["client"].cookies["session"].value
    ready = threading.Barrier(2)

    def attempt():
        close_old_connections()
        try:
            client = Client()
            client.cookies["session"] = session
            local = {**case, "client": client}
            ready.wait(timeout=10)
            return review(local, item, "hide").status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(attempt) for _ in range(2)]
        statuses = [future.result(timeout=30) for future in futures]
    assert sorted(statuses) == [201, 409]
    assert ModerationReview.objects.count() == 1
    assert AuditEvent.objects.filter(action="comment.hidden").count() == 1
