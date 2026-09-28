import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent, DomainEvent
from communications.models import BulkReceipt, Message, MessageRecipient
from django.core import signing
from django.db import close_old_connections, connection, connections
from django.test import Client
from django.utils import timezone
from evaluations.models import (
    AssignmentVersion,
    ConflictOfInterest,
    EvaluationPlan,
    EvaluationPool,
    PoolMembership,
)
from events.models import Event, EventStatus, Track
from participation.models import Team
from policies.models import TemporalGate
from projects.models import Project, Submission
from stages.models import ParticipationMode, Stage, StageEntry, StageTransition
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


@pytest.fixture
def case():
    actor = User.objects.create_user(username="bulk-organizer")
    participant = User.objects.create_user(username="bulk-participant", email="p@example.com")
    judge = User.objects.create_user(username="bulk-judge")
    workspace = Workspace.objects.create(name="Bulk", slug="bulk")
    for user, role in [
        (actor, Role.ORGANIZER),
        (participant, Role.PARTICIPANT),
        (judge, Role.JUDGE),
    ]:
        Membership.objects.create(workspace=workspace, user=user, role=role)
    event = Event.objects.create(workspace=workspace, name="Bulk", slug="bulk")
    source = Stage.objects.create(event=event, name="First")
    target = Stage.objects.create(event=event, name="Second")
    StageTransition.objects.create(from_stage=source, to_stage=target)
    team = Team.objects.create(event=event, name="Team")
    entry = StageEntry.objects.enter(source, "team", str(team.public_id))
    project = Project.objects.create(event=event, name="Project", created_by=actor)
    Submission.objects.create(project=project, stage=source, updated_by=actor)
    track = Track.objects.create(event=event, name="New track")
    pool = EvaluationPool.objects.create(event=event, name="Pool")
    PoolMembership.objects.create(pool=pool, judge=judge)
    plan = EvaluationPlan.objects.create(stage=source, name="Plan", pool=pool)
    gate = TemporalGate.objects.create(event=event, name="Submit", closes_at=timezone.now())
    client = Client()
    client.cookies["session"] = Session.issue(actor).token
    url = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/operations/bulk/"
    return dict(
        actor=actor,
        participant=participant,
        judge=judge,
        workspace=workspace,
        event=event,
        source=source,
        target=target,
        entry=entry,
        project=project,
        track=track,
        plan=plan,
        gate=gate,
        client=client,
        url=url,
    )


def operations(c):
    return [
        {
            "action": "move",
            "projects": [str(c["project"].public_id)],
            "track": str(c["track"].public_id),
        },
        {"action": "assign", "plan": str(c["plan"].public_id), "coverage": 1},
        {
            "action": "advance",
            "stage": str(c["source"].public_id),
            "to_stage": str(c["target"].public_id),
            "entries": [str(c["entry"].public_id)],
        },
        {"action": "extend", "gates": [str(c["gate"].public_id)], "seconds": 3600},
        {
            "action": "send",
            "subject": "Update",
            "body": "Welcome",
            "audience_kind": "all_participants",
        },
    ]


def post(c, ops, token=None, client=None):
    data = {"operations": ops}
    if token:
        data["preview_token"] = token
    return (client or c["client"]).post(c["url"], data=data, content_type="application/json")


def preview(c, ops):
    response = post(c, ops)
    assert response.status_code == 200, response.content
    assert response.json()["applied"] is False
    return response.json()["preview_token"]


def assert_untouched(c):
    c["project"].refresh_from_db()
    c["entry"].refresh_from_db()
    c["plan"].refresh_from_db()
    assert c["project"].track_id is None
    assert c["entry"].exited_at is None
    assert c["plan"].active_assignment_version_id is None
    assert not AssignmentVersion.objects.exists()
    assert not Message.objects.exists()
    assert not BulkReceipt.objects.exists()
    assert not AuditEvent.objects.exists()
    assert not DomainEvent.objects.exists()


def test_full_preview_apply_and_retry_are_atomic_and_audited(case, monkeypatch):
    def unexpected_email(**kwargs):
        pytest.fail("Bulk send must not invoke external email delivery")

    monkeypatch.setattr("communications.services.deliver_email", unexpected_email)
    ops = operations(case)
    closes_at = case["gate"].closes_at
    token = preview(case, ops)
    assert_untouched(case)
    response = post(case, ops, token)
    assert response.status_code == 200, response.content
    assert response.json()["applied"] is True
    case["gate"].refresh_from_db()
    case["project"].refresh_from_db()
    case["entry"].refresh_from_db()
    assert case["gate"].closes_at == closes_at + timedelta(hours=1)
    assert case["project"].track_id == case["track"].pk
    assert case["entry"].exited_at is not None
    assert StageEntry.objects.get(exited_at=None).stage_id == case["target"].pk
    assert AssignmentVersion.objects.count() == 1
    assert MessageRecipient.objects.get().user_id == case["participant"].pk
    assert BulkReceipt.objects.get().result == response.json()
    assert set(AuditEvent.objects.values_list("action", flat=True)) == {
        "project.track_moved",
        "assignment.activated",
        "stage.advanced",
        "temporal_gate.updated",
        "message.sent",
        "operations.bulk_applied",
    }
    retry = post(case, ops, token)
    assert retry.json() == response.json()
    assert (
        Message.objects.count()
        == AssignmentVersion.objects.count()
        == BulkReceipt.objects.count()
        == 1
    )
    assert AuditEvent.objects.count() == 6


@pytest.mark.parametrize(
    "index,field", [(0, "projects"), (1, "plan"), (2, "entries"), (3, "gates")]
)
def test_missing_or_foreign_targets_rollback_earlier_actions(case, index, field):
    ops = operations(case)
    ops[index][field] = [str(uuid.uuid4())] if field != "plan" else str(uuid.uuid4())
    assert post(case, ops).status_code == 400
    assert_untouched(case)


@pytest.mark.parametrize("index", range(5))
def test_changed_effects_require_new_preview_without_partial_writes(case, index):
    ops = operations(case)
    token = preview(case, ops)
    if index == 0:
        other = Track.objects.create(event=case["event"], name="Changed")
        Project.objects.filter(pk=case["project"].pk).update(track=other)
    elif index == 1:
        ConflictOfInterest.objects.create(
            event=case["event"],
            judge=case["judge"],
            project=case["project"],
            declared_by=case["actor"],
        )
    elif index == 2:
        StageEntry.objects.filter(pk=case["entry"].pk).update(exited_at=timezone.now())
    elif index == 3:
        TemporalGate.objects.filter(pk=case["gate"].pk).update(
            closes_at=timezone.now() + timedelta(days=1)
        )
    else:
        extra = User.objects.create_user(username="new-participant")
        Membership.objects.create(workspace=case["workspace"], user=extra, role=Role.PARTICIPANT)
    response = post(case, ops, token)
    assert response.status_code in (400, 409), response.content
    assert not BulkReceipt.objects.exists()
    assert not AssignmentVersion.objects.exists()
    assert not Message.objects.exists()
    assert not AuditEvent.objects.exists()


def test_invalid_stage_mode_cannot_preview_or_mutate(case):
    case["target"].participation_mode = ParticipationMode.INDIVIDUAL
    case["target"].save()
    assert post(case, operations(case)).status_code == 400
    assert_untouched(case)


def test_audit_failure_rolls_back_every_applied_operation(case, monkeypatch):
    ops = operations(case)
    token = preview(case, ops)
    from communications import bulk

    original = bulk.record_mutation

    def fail_batch_audit(**kwargs):
        if kwargs["action"] == "operations.bulk_applied":
            raise RuntimeError("audit unavailable")
        return original(**kwargs)

    monkeypatch.setattr(bulk, "record_mutation", fail_batch_audit)
    with pytest.raises(RuntimeError, match="audit unavailable"):
        post(case, ops, token)
    assert_untouched(case)


def test_token_tampering_expiry_and_changed_request_fail_closed(case, monkeypatch):
    ops = operations(case)
    token = preview(case, ops)
    assert post(case, ops, token + "x").status_code == 409
    altered = operations(case)
    altered[-1]["body"] = "Changed body"
    assert post(case, altered, token).status_code == 409
    monkeypatch.setattr(signing.time, "time", lambda: 9999999999)
    assert post(case, ops, token).status_code == 409
    assert_untouched(case)


def test_authorization_and_actor_binding(case):
    ops = operations(case)
    assert post(case, ops, client=Client()).status_code in (401, 403)
    participant = Client()
    participant.cookies["session"] = Session.issue(case["participant"]).token
    assert post(case, ops, client=participant).status_code == 403
    token = preview(case, ops)
    other = User.objects.create_user(username="other-organizer")
    Membership.objects.create(workspace=case["workspace"], user=other, role=Role.ORGANIZER)
    other_client = Client()
    other_client.cookies["session"] = Session.issue(other).token
    assert post(case, ops, token, client=other_client).status_code == 409
    assert_untouched(case)


@pytest.mark.parametrize(
    "bad",
    [
        [],
        [{"action": "unknown"}],
        [{"action": "assign", "coverage": 0}],
        [{"action": "assign", "plan": "bad", "coverage": 1}],
        [{"action": "send", "subject": " ", "body": "hi", "audience_kind": "all_participants"}],
    ],
)
def test_invalid_input_is_rejected_without_writes(case, bad):
    assert post(case, bad).status_code == 400
    assert_untouched(case)


def test_duplicate_targets_unknown_fields_and_batch_bounds(case):
    ops = operations(case)
    ops[0]["projects"] *= 2
    assert post(case, ops).status_code == 400
    ops = operations(case)
    ops[0]["force"] = True
    assert post(case, ops).status_code == 400
    ops = operations(case)
    ops[0]["coverage"] = 1
    assert post(case, ops).status_code == 400
    assert post(case, [ops[-1]] * 21).status_code == 400
    assert_untouched(case)


def test_archived_events_and_unbounded_gates_are_rejected(case):
    TemporalGate.objects.filter(pk=case["gate"].pk).update(closes_at=None)
    assert post(case, operations(case)).status_code == 400
    Event.objects.filter(pk=case["event"].pk).update(status=EventStatus.ARCHIVED)
    assert post(case, operations(case)).status_code == 400
    assert_untouched(case)


@pytest.mark.parametrize("index,field", [(0, "track"), (1, "plan"), (2, "to_stage"), (3, "gates")])
def test_real_cross_event_records_cannot_be_targeted(case, index, field):
    foreign = Event.objects.create(workspace=case["workspace"], name="Other", slug="other")
    stage = Stage.objects.create(event=foreign, name="Other stage")
    targets = {
        "track": Track.objects.create(event=foreign, name="Other track"),
        "plan": EvaluationPlan.objects.create(stage=stage, name="Other plan"),
        "to_stage": stage,
        "gates": TemporalGate.objects.create(
            event=foreign, name="Other gate", closes_at=timezone.now()
        ),
    }
    ops = operations(case)
    target = str(targets[field].public_id)
    ops[index][field] = [target] if field == "gates" else target
    assert post(case, ops).status_code == 400
    assert_untouched(case)


def test_impact_limit_rolls_back_the_whole_batch(case, monkeypatch):
    monkeypatch.setattr("communications.bulk.MAX_EFFECTS", 3)
    assert post(case, operations(case)).status_code == 400
    assert_untouched(case)


def test_matrix_and_audience_limits_are_enforced_before_delivery(case, monkeypatch):
    monkeypatch.setattr("communications.bulk.MAX_EFFECTS", 1)
    extra = User.objects.create_user(username="extra-judge")
    Membership.objects.create(workspace=case["workspace"], user=extra, role=Role.JUDGE)
    PoolMembership.objects.create(pool=case["plan"].pool, judge=extra)
    assert post(case, [operations(case)[1]]).status_code == 400
    send = {**operations(case)[-1], "audience_kind": "all_judges"}
    assert post(case, [send]).status_code == 400
    assert_untouched(case)


def test_no_edge_or_unrecognized_audience_cannot_apply(case):
    StageTransition.objects.all().delete()
    assert post(case, operations(case)).status_code == 400
    send = {**operations(case)[-1], "audience_params": {"ignored": True}}
    assert post(case, [send]).status_code == 400
    assert post(case, [operations(case)[1]] * 2).status_code == 400
    assert_untouched(case)


def test_preview_token_cannot_be_used_for_a_different_event(case):
    ops = operations(case)
    token = preview(case, ops)
    foreign = Event.objects.create(workspace=case["workspace"], name="Other", slug="other")
    case["url"] = case["url"].replace(str(case["event"].public_id), str(foreign.public_id))
    assert post(case, ops, token).status_code == 409
    assert_untouched(case)


@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(connection.vendor != "postgresql", reason="Requires PostgreSQL row locks")
def test_concurrent_retry_applies_once(case):
    ops = operations(case)
    token = preview(case, ops)
    session = case["client"].cookies["session"].value
    ready = threading.Barrier(2)

    def attempt():
        close_old_connections()
        try:
            client = Client()
            client.cookies["session"] = session
            ready.wait(timeout=10)
            response = post(case, ops, token, client)
            return response.status_code, response.json()
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(attempt) for _ in range(2)]
        results = [future.result(timeout=30) for future in futures]
    assert all(status == 200 for status, _ in results), results
    assert results[0] == results[1]
    assert (
        Message.objects.count()
        == AssignmentVersion.objects.count()
        == BulkReceipt.objects.count()
        == 1
    )
    assert AuditEvent.objects.count() == 6
