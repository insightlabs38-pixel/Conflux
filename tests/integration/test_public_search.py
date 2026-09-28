import pytest
from accounts.models import Session, User
from artifacts.models import Artifact, ArtifactStatus
from audit.models import AuditEvent
from django.test import Client
from events.models import Event, EventStatus
from presentation.models import ProjectSearchTag, SavedPublicSearch
from projects.models import Project, ProjectMembership, Submission, SubmissionStatus
from stages.models import Stage
from test_public_site import make_public_event_with_finalized_project
from workspaces.models import Membership, Role

pytestmark = pytest.mark.django_db


@pytest.fixture
def case():
    event, project, track = make_public_event_with_finalized_project()
    user = project.created_by
    ProjectMembership.objects.create(project=project, user=user, role="owner")
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    prefix = f"/api/v1/workspaces/{event.workspace.public_id}/events/{event.public_id}/"
    return event, project, track, client, prefix


def search(case, **query):
    return Client().get(f"/api/v1/events/{case[0].public_id}/search/", query)


def test_text_search_combines_public_name_and_description(case):
    assert search(case, q="grades").json()["count"] == 1
    assert search(case, q="Autograder grades").json()["count"] == 1
    assert search(case, q="Autograder impossible").json()["count"] == 0
    assert search(case, q="private notes").json()["count"] == 0
    result = search(case).json()["items"][0]
    assert result["artifact_kinds"] == ["repository"]
    assert "object_key" not in str(result) and "created_by" not in result


def test_public_artifact_filter_cannot_infer_private_or_rejected_artifacts(case):
    assert search(case, artifact_kind="repository").json()["count"] == 1
    assert search(case, artifact_kind="document").json()["count"] == 0
    Artifact.objects.create(
        project=case[1],
        kind="image",
        status="rejected",
        visibility="public",
        title="Rejected",
        created_by=case[1].created_by,
    )
    assert search(case, artifact_kind="image").json()["count"] == 0
    repo = case[1].artifacts.get(kind="repository")
    repo.status = ArtifactStatus.UPLOADED
    repo.save()
    assert search(case, artifact_kind="repository").json()["count"] == 0


def test_tags_are_public_normalized_and_all_required(case):
    path = case[4] + f"projects/{case[1].public_id}/tags/"
    response = case[3].put(
        path, {"tags": ["AI", "education", "ai"]}, content_type="application/json"
    )
    assert response.status_code == 200
    assert response.json()["tags"] == ["ai", "education"]
    assert search(case, tags=["AI", "education"]).json()["count"] == 1
    assert search(case, tags=["ai", "missing"]).json()["count"] == 0
    assert AuditEvent.objects.get(action="project.tags_updated").metadata["after"] == [
        "ai",
        "education",
    ]
    assert (
        case[3].put(path, {"tags": ["<script>"]}, content_type="application/json").status_code
        == 400
    )
    assert case[3].put(path, {"tags": []}, content_type="application/json").status_code == 200
    assert search(case, tags=["ai"]).json()["count"] == 0


def test_tags_require_current_project_membership_and_mutable_event(case):
    path = case[4] + f"projects/{case[1].public_id}/tags/"
    other = User.objects.create_user(username="other")
    Membership.objects.create(workspace=case[0].workspace, user=other, role=Role.ORGANIZER)
    client = Client()
    client.cookies["session"] = Session.issue(other).token
    assert client.put(path, {"tags": ["ai"]}, content_type="application/json").status_code == 403
    assert client.get(path).status_code == 403
    case[0].status = EventStatus.ARCHIVED
    case[0].save()
    assert case[3].put(path, {"tags": ["ai"]}, content_type="application/json").status_code == 400
    assert not ProjectSearchTag.objects.exists()


def test_stage_filter_requires_finalized_submission_in_selected_stage(case):
    stage = Stage.objects.create(event=case[0], name="Draft stage", position=1)
    Submission.objects.create(project=case[1], stage=stage, updated_by=case[1].created_by)
    assert search(case, stage=str(stage.public_id)).json()["count"] == 0
    response = Client().get(f"/e/{case[0].public_id}/gallery/", {"stage": str(stage.public_id)})
    assert "Autograder" not in response.content.decode()
    assert search(case, track=str(case[2].public_id)).json()["count"] == 1
    assert search(case, track="00000000-0000-0000-0000-000000000001").json()["count"] == 0


def test_public_search_rechecks_finalization_and_event_visibility(case):
    case[1].submissions.update(status=SubmissionStatus.DRAFT)
    assert search(case).json()["count"] == 0
    case[0].is_public = False
    case[0].save()
    assert search(case).status_code == 404
    case[0].is_public = True
    case[0].status = EventStatus.DRAFT
    case[0].save()
    assert search(case).status_code == 404


@pytest.mark.parametrize(
    "query",
    [
        {"offset": -1},
        {"q": "x" * 201},
        {"q": "word " * 11},
        {"tags": ["ai"] * 11},
        {"artifact_kind": "unknown"},
        {"stage": "invalid"},
        {"private": "yes"},
    ],
)
def test_invalid_search_fails_closed(case, query):
    assert search(case, **query).status_code == 400


def test_saved_view_is_private_and_replays_current_filters(case):
    path = case[4] + "saved-searches/"
    payload = {
        "name": "My repos",
        "filters": {"q": "grades", "artifact_kind": "repository", "track": str(case[2].public_id)},
    }
    response = case[3].post(path, payload, content_type="application/json")
    assert response.status_code == 201
    data = response.json()
    detail = path + data["public_id"] + "/"
    assert case[3].get(path).json() == [data]
    assert case[3].get(detail).json()["count"] == 1
    assert case[3].get(detail, {"q": "changed"}).status_code == 400
    assert case[3].post(path, payload, content_type="application/json").status_code == 400
    case[1].submissions.update(status="draft")
    assert case[3].get(detail).json()["count"] == 0
    other = User.objects.create_user(username="other")
    Membership.objects.create(workspace=case[0].workspace, user=other, role=Role.PARTICIPANT)
    client = Client()
    client.cookies["session"] = Session.issue(other).token
    assert client.get(path).json() == []
    assert client.get(detail).status_code == 404
    assert client.delete(detail).status_code == 404
    case[0].is_public = False
    case[0].save()
    assert case[3].get(detail).status_code == 404
    assert case[3].delete(detail).status_code == 204


def test_saved_views_reject_invalid_filters_and_cap_storage(case):
    path = case[4] + "saved-searches/"
    assert (
        case[3]
        .post(path, {"name": "Bad", "filters": {"sql": "all"}}, content_type="application/json")
        .status_code
        == 400
    )
    SavedPublicSearch.objects.bulk_create(
        [
            SavedPublicSearch(event=case[0], owner=case[1].created_by, name=str(i), filters={})
            for i in range(50)
        ]
    )
    assert (
        case[3]
        .post(path, {"name": "Over limit", "filters": {}}, content_type="application/json")
        .status_code
        == 400
    )
    assert len(case[3].get(path).json()) == 50


def test_search_deduplicates_and_paginates_with_stable_ties(case):
    stage = Stage.objects.create(event=case[0], name="Finals", position=1)
    Submission.objects.create(
        project=case[1], stage=stage, status="finalized", updated_by=case[1].created_by
    )
    assert search(case).json()["count"] == 1
    for _ in range(51):
        project = Project.objects.create(
            event=case[0], name="Autograder", created_by=case[1].created_by
        )
        Submission.objects.create(
            project=project, stage=stage, status="finalized", updated_by=case[1].created_by
        )
    first = search(case).json()
    second = search(case, offset=50).json()
    assert first["count"] == 52 and first["next_offset"] == 50
    assert len(second["items"]) == 2 and second["next_offset"] is None
    assert not {p["public_id"] for p in first["items"]} & {p["public_id"] for p in second["items"]}


def test_tag_audit_failure_rolls_back(case, monkeypatch):
    ProjectSearchTag.objects.create(project=case[1], tag="original")

    def fail(**kwargs):
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr("presentation.search.record_mutation", fail)
    with pytest.raises(RuntimeError, match="audit unavailable"):
        case[3].put(
            case[4] + f"projects/{case[1].public_id}/tags/",
            {"tags": ["replacement"]},
            content_type="application/json",
        )
    assert list(case[1].search_tags.values_list("tag", flat=True)) == ["original"]


def test_search_never_crosses_event_boundary(case):
    other = Event.objects.create(
        workspace=case[0].workspace, name="Other", slug="other", status="open", is_public=True
    )
    assert Client().get(f"/api/v1/events/{other.public_id}/search/").json()["count"] == 0


def test_postgres_search_uses_tokens_and_handles_punctuation(case):
    from django.db import connection

    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL full-text token semantics")
    assert search(case, q="grades!").json()["count"] == 1
    assert search(case, q="grader").json()["count"] == 0


@pytest.mark.django_db(transaction=True)
def test_concurrent_saved_views_cannot_exceed_cap(case):
    import threading
    from concurrent.futures import ThreadPoolExecutor

    from django.db import close_old_connections, connection, connections

    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row locks required")
    SavedPublicSearch.objects.bulk_create(
        [
            SavedPublicSearch(event=case[0], owner=case[1].created_by, name=str(i), filters={})
            for i in range(49)
        ]
    )
    barrier = threading.Barrier(2)
    token = case[3].cookies["session"].value
    path = case[4] + "saved-searches/"

    def save(name):
        close_old_connections()
        try:
            client = Client()
            client.cookies["session"] = token
            barrier.wait(timeout=10)
            return client.post(
                path, {"name": name, "filters": {}}, content_type="application/json"
            ).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(save, ["First", "Second"]))
    assert sorted(results) == [201, 400]
    assert SavedPublicSearch.objects.count() == 50
