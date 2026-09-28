from datetime import UTC, datetime, timedelta

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from awards.models import Award, AwardWinner
from django.db import IntegrityError, transaction
from django.test import Client
from django.utils import timezone
from evaluations.models import EvaluationPlan
from presentation.models import Page, PageBlock, PublicationSchedule
from projects.models import Project, Submission
from stages.models import Stage
from test_feedback_release_api import (
    cookie_client,
    feedback_url,
    make_fixture,
    make_published_plan,
    submit_ballot,
)
from test_public_site import make_public_event_with_finalized_project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db
NOW = datetime(2026, 9, 28, 12, tzinfo=UTC)


@pytest.fixture
def case(monkeypatch):
    monkeypatch.setattr(timezone, "now", lambda: NOW)
    event, project, _ = make_public_event_with_finalized_project()
    organizer = User.objects.create_user(username="scheduler", password="unused")
    Membership.objects.create(workspace=event.workspace, user=organizer, role=Role.ORGANIZER)
    client = cookie_client(Session.issue(organizer).token)
    base = (
        f"/api/v1/workspaces/{event.workspace.public_id}/events/{event.public_id}"
        "/publication-schedules/"
    )
    return event, project, client, base


def window(case, surface, **extra):
    return case[2].put(
        case[3] + surface + "/",
        {"opens_at": NOW.isoformat(), **extra},
        content_type="application/json",
    )


def test_schedule_updates_are_scoped_and_audited(case):
    event, _, client, base = case
    response = window(case, "gallery", opens_at=(NOW + timedelta(hours=1)).isoformat())
    assert response.status_code == 200
    assert response.json()["finalist_stage"] is None
    assert len(client.get(base).json()) == 1
    assert window(case, "gallery").status_code == 200
    assert PublicationSchedule.objects.filter(event=event).count() == 1
    audit = AuditEvent.objects.filter(action="publication.schedule_saved").latest("id")
    assert "opens_at" in audit.metadata["changes"]
    assert audit.metadata["event_id"] == str(event.public_id)
    assert client.delete(base + "gallery/").status_code == 204
    assert not event.publication_schedules.exists()
    assert AuditEvent.objects.filter(action="publication.schedule_removed").count() == 1
    assert client.delete(base + "gallery/").status_code == 404


def test_only_event_organizers_can_manage_schedules(case):
    event, project, client, base = case
    participant = cookie_client(Session.issue(project.created_by).token)
    for denied in (Client(), participant):
        assert denied.get(base).status_code in (401, 403)
        assert denied.put(base + "gallery/", {}, content_type="application/json").status_code in (
            401,
            403,
        )
        assert denied.delete(base + "gallery/").status_code in (401, 403)
    other_workspace = Workspace.objects.create(name="Other", slug="other")
    other_url = base.replace(str(event.workspace.public_id), str(other_workspace.public_id))
    assert client.get(other_url).status_code == 403
    Membership.objects.create(
        workspace=other_workspace,
        user=Session.objects.get(token=client.cookies["session"].value).user,
        role=Role.ORGANIZER,
    )
    assert client.get(other_url).status_code == 404


def test_equivalent_offsets_do_not_invent_a_schedule_change(case):
    assert (
        window(case, "gallery", opens_at="2026-09-28T07:00:00-05:00").json()["opens_at"]
        == "2026-09-28T12:00:00Z"
    )
    assert window(case, "gallery").status_code == 200
    audit = AuditEvent.objects.filter(action="publication.schedule_saved").latest("id")
    assert audit.metadata["changes"] == {}


@pytest.mark.parametrize(
    "surface,data",
    [
        ("unknown", {}),
        ("gallery", {"opens_at": "2026-09-28T12:00:00"}),
        ("gallery", {"closes_at": NOW.isoformat()}),
        ("gallery", {"closes_at": (NOW - timedelta(seconds=1)).isoformat()}),
        ("gallery", {"unexpected": True}),
        ("finalists", {}),
    ],
)
def test_invalid_schedules_leave_no_mutation(case, surface, data):
    assert window(case, surface, **data).status_code == 400
    assert not PublicationSchedule.objects.exists()
    assert not AuditEvent.objects.filter(action="publication.schedule_saved").exists()


def test_finalist_stage_must_belong_to_the_event(case):
    event = case[0]
    stage = event.stages.get()
    assert window(case, "gallery", finalist_stage=str(stage.public_id)).status_code == 400
    other = type(event).objects.create(workspace=event.workspace, name="Other", slug="other")
    foreign = Stage.objects.create(event=other, name="Finals")
    assert window(case, "finalists", finalist_stage=str(foreign.public_id)).status_code == 400
    assert window(case, "finalists", finalist_stage=str(stage.public_id)).status_code == 200


def test_gallery_window_applies_to_all_project_reads_at_exact_boundaries(case, monkeypatch):
    event, project, client, base = case
    PageBlock.objects.create(page=Page.objects.create(event=event), kind="gallery", config={})
    paths = [
        f"/e/{event.public_id}/",
        f"/e/{event.public_id}/gallery/",
        f"/e/{event.public_id}/projects/{project.public_id}/",
        f"/api/v1/events/{event.public_id}/gallery/",
        f"/api/v1/events/{event.public_id}/search/",
    ]
    assert (
        window(case, "gallery", closes_at=(NOW + timedelta(hours=1)).isoformat()).status_code == 200
    )
    for instant, visible in [
        (NOW - timedelta(microseconds=1), False),
        (NOW, True),
        (NOW + timedelta(hours=1) - timedelta(microseconds=1), True),
        (NOW + timedelta(hours=1), False),
    ]:
        monkeypatch.setattr(timezone, "now", lambda: instant)
        for path in paths:
            response = Client().get(path)
            assert (project.name in response.content.decode()) == visible
            assert response.status_code == (404 if not visible and "/projects/" in path else 200)
            assert "no-store" in response["Cache-Control"]
    assert client.delete(base + "gallery/").status_code == 204
    assert project.name in Client().get(paths[1]).content.decode()


def test_finalists_require_release_and_finalized_selected_stage(case):
    event, project, _, _ = case
    api = f"/api/v1/events/{event.public_id}/finalists/"
    html = f"/e/{event.public_id}/finalists/"
    assert Client().get(api).status_code == 404
    stage = Stage.objects.create(event=event, name="Finals")
    assert window(case, "finalists", finalist_stage=str(stage.public_id)).status_code == 200
    assert Client().get(api).json() == []
    submission = Submission.objects.create(
        project=project, stage=stage, status="finalized", updated_by=project.created_by
    )
    draft = Project.objects.create(
        event=event, name="Draft finalist", created_by=project.created_by
    )
    Submission.objects.create(
        project=draft, stage=stage, status="draft", updated_by=project.created_by
    )
    assert [item["public_id"] for item in Client().get(api).json()] == [str(project.public_id)]
    body = Client().get(html).content.decode()
    assert "Finalists" in body and project.name in body and draft.name not in body
    assert "no-store" in Client().get(html)["Cache-Control"]
    submission.status = "draft"
    submission.save()
    assert Client().get(api).json() == []
    window(
        case,
        "finalists",
        finalist_stage=str(stage.public_id),
        opens_at=(NOW + timedelta(seconds=1)).isoformat(),
    )
    assert Client().get(api).status_code == 404
    assert Client().get(html).status_code == 404


def test_winners_window_preserves_publication_and_gallery_gates(case):
    event, project, _, _ = case
    award = Award.objects.create(event=event, name="Scheduled winner", published_at=NOW)
    AwardWinner.objects.create(
        award=award, project=project, selected_by=project.created_by, source="manual"
    )
    PageBlock.objects.create(page=Page.objects.create(event=event), kind="results", config={})
    urls = [
        f"/e/{event.public_id}/",
        f"/e/{event.public_id}/results/",
        f"/api/v1/events/{event.public_id}/awards/",
    ]
    card = f"/e/{event.public_id}/results/awards/{award.public_id}/card.svg"
    window(case, "winners", opens_at=(NOW + timedelta(seconds=1)).isoformat())
    for url in urls:
        response = Client().get(url)
        assert response.status_code == 200 and award.name not in response.content.decode()
    assert Client().get(card).status_code == 404
    window(case, "winners")
    for url in urls:
        assert award.name in Client().get(url).content.decode()
    assert Client().get(card).status_code == 200
    award.published_at = None
    award.save()
    assert Client().get(card).status_code == 404
    for url in urls:
        assert award.name not in Client().get(url).content.decode()


def test_archive_gate_covers_every_public_event_surface(case):
    event, _, _, _ = case
    urls = [f"/e/{event.public_id}/", f"/api/v1/events/{event.public_id}/"]
    urls += [
        f"/api/v1/events/{event.public_id}/{surface}/"
        for surface in ("gallery", "search", "awards", "questions", "announcements")
    ]
    window(case, "archive", opens_at=(NOW + timedelta(hours=1)).isoformat())
    assert Client().get(urls[0]).status_code == 200
    event.status = "archived"
    event.save()
    for url in urls:
        assert Client().get(url).status_code == 404
    window(case, "archive")
    for url in urls:
        assert Client().get(url).status_code == 200
    event.is_public = False
    event.save()
    for url in urls:
        assert Client().get(url).status_code == 404


def test_scheduled_feedback_still_needs_opt_in_and_membership(monkeypatch):
    monkeypatch.setattr(timezone, "now", lambda: NOW)
    workspace, event, stage, project, organizer, judge, owner, outsider = make_fixture()
    organizer_client = cookie_client(Session.issue(organizer).token)
    plan_id = make_published_plan(organizer_client, workspace, event, stage)
    submit_ballot(
        cookie_client(Session.issue(judge).token),
        workspace,
        event,
        stage,
        plan_id,
        project,
        "Useful feedback",
    )
    plan = EvaluationPlan.objects.get(public_id=plan_id)
    schedule = PublicationSchedule.objects.create(event=event, surface="feedback", opens_at=NOW)
    url = feedback_url(workspace, event, stage, plan_id, project)
    owner_client = cookie_client(Session.issue(owner).token)
    assert owner_client.get(url).status_code == 403
    plan.feedback_visible_to_participants = True
    plan.save()
    assert owner_client.get(url).json()[0]["judge"] is None
    assert cookie_client(Session.issue(outsider).token).get(url).status_code == 404
    schedule.closes_at = NOW + timedelta(seconds=1)
    schedule.save()
    monkeypatch.setattr(timezone, "now", lambda: NOW + timedelta(seconds=1))
    assert owner_client.get(url).status_code == 403
    assert organizer_client.get(url).status_code == 200
    assert "no-store" in organizer_client.get(url)["Cache-Control"]


def test_database_rejects_invalid_windows_and_duplicate_surfaces(case):
    event = case[0]
    window(case, "gallery")
    with pytest.raises(IntegrityError), transaction.atomic():
        PublicationSchedule.objects.create(event=event, surface="gallery", opens_at=NOW)
    with pytest.raises(IntegrityError), transaction.atomic():
        PublicationSchedule.objects.create(
            event=event, surface="winners", opens_at=NOW, closes_at=NOW
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        PublicationSchedule.objects.create(event=event, surface="finalists", opens_at=NOW)


@pytest.mark.django_db(transaction=True)
def test_concurrent_first_saves_are_serialized_and_audited(case):
    import threading
    from concurrent.futures import ThreadPoolExecutor

    from django.db import close_old_connections, connection, connections

    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row locks required")
    barrier = threading.Barrier(2)
    token = case[2].cookies["session"].value

    def save(hours):
        close_old_connections()
        try:
            client = cookie_client(token)
            barrier.wait(timeout=10)
            return client.put(
                case[3] + "gallery/",
                {"opens_at": (NOW + timedelta(hours=hours)).isoformat()},
                content_type="application/json",
            ).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(save, [1, 2])) == [200, 200]
    assert PublicationSchedule.objects.count() == 1
    audits = list(AuditEvent.objects.filter(action="publication.schedule_saved").order_by("id"))
    assert len(audits) == 2
    assert (
        audits[1].metadata["changes"]["opens_at"]["before"]
        == audits[0].metadata["changes"]["opens_at"]
    )
