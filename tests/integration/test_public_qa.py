import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from communications.models import EventQuestion
from django.test import Client
from events.models import Announcement, EventStatus
from test_announcements import fixture

pytestmark = pytest.mark.django_db


@pytest.fixture
def case():
    workspace, organizer, participant, event = fixture()
    clients = []
    for user in (organizer, participant):
        client = Client()
        client.cookies["session"] = Session.issue(user).token
        clients.append(client)
    prefix = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/communications/"
    public = f"/api/v1/events/{event.public_id}/"
    return workspace, organizer, participant, event, *clients, prefix, public


def submit(case, **data):
    return case[5].post(
        case[6] + "questions/",
        {"question": "When is lunch?", **data},
        content_type="application/json",
    )


def review(case, public_id, **data):
    return case[4].post(
        case[6] + f"questions/{public_id}/review/",
        {
            "version": 1,
            "status": "published",
            "answer": "Noon.",
            "note": "Checked schedule",
            **data,
        },
        content_type="application/json",
    )


def test_question_is_private_until_answered_and_reviewed(case):
    created = submit(case)
    assert created.status_code == 201
    data = created.json()
    assert data["status"] == "pending"
    assert "author" not in data
    public_id = data["public_id"]
    assert Client().get(case[7] + "questions/").json() == []
    assert case[5].get(case[6] + "questions/").json() == [data]
    assert review(case, public_id, answer=" ").status_code == 400
    assert review(case, public_id).status_code == 200
    published = Client().get(case[7] + "questions/").json()
    assert published[0]["answer"] == "Noon."
    audit = AuditEvent.objects.get(action="question.reviewed")
    assert audit.actor == case[1]
    assert audit.metadata["before"]["status"] == "pending"
    assert audit.metadata["after"]["version"] == 2
    assert review(case, public_id, answer="One.").status_code == 409
    assert review(case, public_id, version=2, status="hidden").status_code == 200
    assert Client().get(case[7] + "questions/").json() == []
    assert review(case, public_id, version=3).status_code == 200
    assert len(Client().get(case[7] + "questions/").json()) == 1


@pytest.mark.parametrize(
    "data", [{"question": " "}, {"question": "x" * 2001}, {"status": "published"}, {"author": 1}]
)
def test_question_invalid_input_cannot_write(case, data):
    assert submit(case, **data).status_code == 400
    assert not EventQuestion.objects.exists()
    assert not AuditEvent.objects.exists()


@pytest.mark.parametrize(
    "status,public", [("draft", True), ("closed", True), ("archived", True), ("open", False)]
)
def test_submission_requires_open_public_event(case, status, public):
    event = case[3]
    event.status = status
    event.is_public = public
    event.save()
    assert submit(case).status_code == 400
    assert not EventQuestion.objects.exists()


def test_question_authorization_and_workspace_isolation(case):
    from workspaces.models import Membership, Role, Workspace

    created = submit(case).json()
    path = case[6] + f"questions/{created['public_id']}/review/"
    assert case[5].post(path, {}, content_type="application/json").status_code == 403
    assert (
        Client().post(case[6] + "questions/", {}, content_type="application/json").status_code
        == 401
    )
    other = User.objects.create_user(username="other")
    Membership.objects.create(workspace=case[0], user=other, role=Role.PARTICIPANT)
    client = Client()
    client.cookies["session"] = Session.issue(other).token
    assert client.get(case[6] + "questions/").json() == []
    foreign = Workspace.objects.create(name="Foreign", slug="foreign")
    Membership.objects.create(workspace=foreign, user=case[1], role=Role.ORGANIZER)
    foreign_path = path.replace(str(case[0].public_id), str(foreign.public_id))
    assert case[4].post(foreign_path, {}, content_type="application/json").status_code == 404
    assert not AuditEvent.objects.filter(action="question.reviewed").exists()


def test_announcement_hide_preserves_history_and_filters_site(case):
    from presentation.models import Page, PageBlock

    announcement = Announcement.objects.create(
        event=case[3], title="Secret", body="Details", posted_by=case[1]
    )
    page = Page.objects.create(event=case[3])
    PageBlock.objects.create(page=page, kind="announcements", position=0, config={})
    path = case[6] + f"announcements/{announcement.public_id}/review/"
    assert len(Client().get(case[7] + "announcements/").json()) == 1
    data = {"version": 1, "status": "hidden", "note": "Wrong details"}
    assert case[5].post(path, data, content_type="application/json").status_code == 403
    assert case[4].post(path, data, content_type="application/json").status_code == 200
    assert Client().get(case[7] + "announcements/").json() == []
    html = Client().get(f"/e/{case[3].public_id}/").content.decode()
    assert "Secret" not in html and "Details" not in html
    assert Announcement.objects.filter(pk=announcement.pk).exists()
    assert case[4].post(path, data, content_type="application/json").status_code == 409
    data.update(version=2, status="published")
    assert case[4].post(path, data, content_type="application/json").status_code == 200
    assert "Secret" in Client().get(f"/e/{case[3].public_id}/").content.decode()
    assert "posted_by" not in Client().get(case[7] + "announcements/").json()[0]


def test_archived_review_rejects_without_mutation(case):
    created = submit(case).json()
    event = case[3]
    event.status = EventStatus.ARCHIVED
    event.save()
    assert review(case, created["public_id"]).status_code == 400
    assert EventQuestion.objects.get().status == "pending"
    assert not AuditEvent.objects.filter(action="question.reviewed").exists()


@pytest.mark.parametrize("status,public", [("draft", True), ("open", False)])
def test_public_communication_hides_nonpublic_event(case, status, public):
    event = case[3]
    event.status, event.is_public = status, public
    event.save()
    for suffix in ("questions/", "announcements/"):
        assert Client().get(case[7] + suffix).status_code == 404


def test_public_lists_are_bounded_and_deterministic(case):
    for i in range(52):
        EventQuestion.objects.create(
            event=case[3],
            author=case[2],
            question=f"Question {i}",
            answer="Answer",
            status="published",
        )
    first = Client().get(case[7] + "questions/").json()
    second = Client().get(case[7] + "questions/", {"offset": 50}).json()
    assert len(first) == 50 and len(second) == 2
    assert not {q["public_id"] for q in first} & {q["public_id"] for q in second}
    assert Client().get(case[7] + "questions/", {"offset": -1}).status_code == 400


def test_audit_failure_rolls_back_review(case, monkeypatch):
    created = submit(case).json()

    def fail(**kwargs):
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr("communications.public_qa.record_mutation", fail)
    with pytest.raises(RuntimeError, match="audit unavailable"):
        review(case, created["public_id"])
    question = EventQuestion.objects.get()
    assert question.status == "pending" and question.version == 1 and question.answer == ""


@pytest.mark.django_db(transaction=True)
def test_concurrent_reviews_apply_once(case):
    import threading
    from concurrent.futures import ThreadPoolExecutor

    from django.db import close_old_connections, connection, connections

    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row locks required")
    created = submit(case).json()
    barrier = threading.Barrier(2)
    token = case[4].cookies["session"].value
    path = case[6] + f"questions/{created['public_id']}/review/"

    def apply(answer):
        close_old_connections()
        try:
            client = Client()
            client.cookies["session"] = token
            barrier.wait(timeout=10)
            return client.post(
                path,
                {"version": 1, "status": "published", "answer": answer, "note": "Reviewed"},
                content_type="application/json",
            ).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(apply, ["Noon", "One"]))
    assert sorted(results) == [200, 409]
    assert EventQuestion.objects.get().version == 2
    assert AuditEvent.objects.filter(action="question.reviewed").count() == 1
