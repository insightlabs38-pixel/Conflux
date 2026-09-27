import pytest
from accounts.models import User
from artifacts.models import Artifact, ArtifactKind, ArtifactStatus, ArtifactVisibility
from django.test import Client
from events.models import Event, EventStatus, Track
from presentation.models import Page, PageBlock
from projects.models import Project, Submission, SubmissionStatus, SubmissionVersion
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def make_public_event_with_finalized_project(*, with_track=True):
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(
        workspace=workspace,
        name="Regionals",
        slug="regionals",
        status=EventStatus.OPEN,
        is_public=True,
        starts_at="2026-01-01T00:00:00Z",
        ends_at="2026-01-02T00:00:00Z",
    )
    track = Track.objects.create(event=event, name="AI", position=0)
    stage = Stage.objects.create(event=event, name="Build", position=0)
    user = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(workspace=workspace, user=user, role=Role.PARTICIPANT)
    project = Project.objects.create(
        event=event,
        name="Autograder",
        description="Grades things.",
        created_by=user,
        track=track if with_track else None,
    )
    submission = Submission.objects.create(project=project, stage=stage, updated_by=user)
    version = SubmissionVersion.objects.create(
        submission=submission, number=1, snapshot={}, digest="a" * 64, finalized_by=user
    )
    submission.status = SubmissionStatus.FINALIZED
    submission.current_version = version
    submission.save()
    Artifact.objects.create(
        project=project,
        kind=ArtifactKind.REPOSITORY,
        visibility=ArtifactVisibility.PUBLIC,
        status=ArtifactStatus.READY,
        title="Source",
        external_url="https://example.com/repo",
        created_by=user,
    )
    Artifact.objects.create(
        project=project,
        kind=ArtifactKind.DOCUMENT,
        visibility=ArtifactVisibility.PARTICIPANT,
        status=ArtifactStatus.READY,
        title="Private notes",
        external_url="https://example.com/private",
        created_by=user,
    )
    return event, project, track


def test_event_landing_renders_hero_and_live_tracks_block_without_js():
    event, _, _ = make_public_event_with_finalized_project()
    page = Page.objects.create(event=event)
    PageBlock.objects.create(
        page=page, kind="hero", position=0, config={"title": "Welcome to Regionals"}
    )
    PageBlock.objects.create(page=page, kind="tracks", position=1, config={})

    response = Client().get(f"/e/{event.public_id}/")
    assert response.status_code == 200
    body = response.content.decode()
    assert "Welcome to Regionals" in body
    assert "AI" in body


def test_event_landing_404s_for_non_public_events():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="Draft", slug="draft")
    assert Client().get(f"/e/{event.public_id}/").status_code == 404


def test_gallery_lists_finalized_projects_and_search_filters_by_name():
    event, project, _ = make_public_event_with_finalized_project()

    body = Client().get(f"/e/{event.public_id}/gallery/").content.decode()
    assert "Autograder" in body

    hit = Client().get(f"/e/{event.public_id}/gallery/", {"q": "autograder"}).content.decode()
    assert "Autograder" in hit

    miss = Client().get(f"/e/{event.public_id}/gallery/", {"q": "nope"}).content.decode()
    assert "Autograder" not in miss


def test_gallery_filters_by_the_real_track_association():
    event, project, ai_track = make_public_event_with_finalized_project()
    user = User.objects.get(username="member")
    other_track = Track.objects.create(event=event, name="Fintech", position=1)
    other_stage = Stage.objects.create(event=event, name="Finals", position=1)
    other_project = Project.objects.create(
        event=event, name="Ledger", track=other_track, created_by=user
    )
    other_submission = Submission.objects.create(
        project=other_project, stage=other_stage, updated_by=user
    )
    other_version = SubmissionVersion.objects.create(
        submission=other_submission, number=1, snapshot={}, digest="b" * 64, finalized_by=user
    )
    other_submission.status = SubmissionStatus.FINALIZED
    other_submission.current_version = other_version
    other_submission.save()

    ai_only = (
        Client()
        .get(f"/e/{event.public_id}/gallery/", {"track": str(ai_track.public_id)})
        .content.decode()
    )
    assert "Autograder" in ai_only
    assert "Ledger" not in ai_only

    fintech_only = (
        Client()
        .get(f"/e/{event.public_id}/gallery/", {"track": str(other_track.public_id)})
        .content.decode()
    )
    assert "Ledger" in fintech_only
    assert "Autograder" not in fintech_only


def test_gallery_and_project_page_handle_a_project_with_no_track():
    event, project, _ = make_public_event_with_finalized_project(with_track=False)
    assert project.track is None

    gallery_body = Client().get(f"/e/{event.public_id}/gallery/").content.decode()
    assert "Autograder" in gallery_body

    detail = Client().get(f"/e/{event.public_id}/projects/{project.public_id}/")
    assert detail.status_code == 200


def test_project_detail_shows_only_public_artifacts():
    event, project, _ = make_public_event_with_finalized_project()
    response = Client().get(f"/e/{event.public_id}/projects/{project.public_id}/")
    assert response.status_code == 200
    body = response.content.decode()
    assert "Source" in body
    assert "Private notes" not in body


def test_project_detail_renders_description_as_safe_technical_content():
    event, project, _ = make_public_event_with_finalized_project()
    project.description = "# How it works\n\n```python\nprint('ok')\n```\n\n<script>bad()</script>"
    project.save(update_fields=["description"])

    response = Client().get(f"/e/{event.public_id}/projects/{project.public_id}/")
    body = response.content.decode()
    assert '<div class="cx-technical-description"><h2>How it works</h2>' in body
    assert '<code class="language-python">' in body
    assert "<script>bad()" not in body
    assert "&lt;script&gt;bad()&lt;/script&gt;" in body


def test_project_detail_404s_for_a_project_without_a_finalized_submission():
    event, _, _ = make_public_event_with_finalized_project()
    user = User.objects.create_user(username="other", password="unused")
    draft_project = Project.objects.create(event=event, name="Unfinished", created_by=user)
    response = Client().get(f"/e/{event.public_id}/projects/{draft_project.public_id}/")
    assert response.status_code == 404
