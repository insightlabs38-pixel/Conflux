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


def make_public_event_with_finalized_project():
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
    Track.objects.create(event=event, name="AI", position=0)
    stage = Stage.objects.create(event=event, name="Build", position=0)
    user = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(workspace=workspace, user=user, role=Role.PARTICIPANT)
    project = Project.objects.create(
        event=event, name="Autograder", description="Grades things.", created_by=user
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
    return event, project


def test_event_landing_renders_hero_and_live_tracks_block_without_js():
    event, _ = make_public_event_with_finalized_project()
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
    event, project = make_public_event_with_finalized_project()

    body = Client().get(f"/e/{event.public_id}/gallery/").content.decode()
    assert "Autograder" in body

    hit = Client().get(f"/e/{event.public_id}/gallery/", {"q": "autograder"}).content.decode()
    assert "Autograder" in hit

    miss = Client().get(f"/e/{event.public_id}/gallery/", {"q": "nope"}).content.decode()
    assert "Autograder" not in miss


def test_project_detail_shows_only_public_artifacts():
    event, project = make_public_event_with_finalized_project()
    response = Client().get(f"/e/{event.public_id}/projects/{project.public_id}/")
    assert response.status_code == 200
    body = response.content.decode()
    assert "Source" in body
    assert "Private notes" not in body


def test_project_detail_404s_for_a_project_without_a_finalized_submission():
    event, _ = make_public_event_with_finalized_project()
    user = User.objects.create_user(username="other", password="unused")
    draft_project = Project.objects.create(event=event, name="Unfinished", created_by=user)
    response = Client().get(f"/e/{event.public_id}/projects/{draft_project.public_id}/")
    assert response.status_code == 404
