"""S19: the public site stays readable after an event closes/archives, and
the page-builder "results" block renders real published award winners
instead of its static placeholder.
"""

import pytest
from accounts.models import User
from awards.models import Award, AwardWinner
from django.test import Client
from events.models import Event, EventStatus, Track
from presentation.models import Page, PageBlock
from projects.models import Project, Submission, SubmissionStatus, SubmissionVersion
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def make_event_with_finalized_project():
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
    organizer = User.objects.create_user(username="organizer", password="unused")
    Membership.objects.create(workspace=workspace, user=organizer, role=Role.ORGANIZER)
    project = Project.objects.create(
        event=event, name="Autograder", created_by=organizer, track=track
    )
    submission = Submission.objects.create(project=project, stage=stage, updated_by=organizer)
    version = SubmissionVersion.objects.create(
        submission=submission, number=1, snapshot={}, digest="a" * 64, finalized_by=organizer
    )
    submission.status = SubmissionStatus.FINALIZED
    submission.current_version = version
    submission.save()
    return event, project, organizer


@pytest.mark.parametrize("status", [EventStatus.CLOSED, EventStatus.ARCHIVED])
def test_gallery_and_project_pages_stay_readable_after_closing_and_archiving(status):
    event, project, _ = make_event_with_finalized_project()
    event.status = status
    event.save(update_fields=["status"])
    client = Client()

    assert client.get(f"/e/{event.public_id}/").status_code == 200
    gallery = client.get(f"/e/{event.public_id}/gallery/")
    assert gallery.status_code == 200
    assert "Autograder" in gallery.content.decode()
    assert client.get(f"/e/{event.public_id}/projects/{project.public_id}/").status_code == 200


def test_draft_events_stay_hidden_regardless_of_is_public():
    workspace = Workspace.objects.create(name="W", slug="w")
    draft = Event.objects.create(workspace=workspace, name="Draft", slug="draft", is_public=True)
    assert Client().get(f"/e/{draft.public_id}/").status_code == 404


def test_results_block_renders_published_award_winners():
    event, project, organizer = make_event_with_finalized_project()
    award = Award.objects.create(
        event=event, name="Best in Show", published_at="2026-01-03T00:00:00Z"
    )
    AwardWinner.objects.create(award=award, project=project, selected_by=organizer, source="manual")
    page = Page.objects.create(event=event)
    PageBlock.objects.create(page=page, kind="results", position=0, config={})

    body = Client().get(f"/e/{event.public_id}/").content.decode()
    assert "Best in Show" in body
    assert "Autograder" in body
    assert "Results will be announced" not in body


def test_results_block_falls_back_to_placeholder_before_anything_is_published():
    event, _, _ = make_event_with_finalized_project()
    page = Page.objects.create(event=event)
    PageBlock.objects.create(page=page, kind="results", position=0, config={})

    body = Client().get(f"/e/{event.public_id}/").content.decode()
    assert "Results will be announced after judging." in body


def test_results_block_omits_an_unpublished_award():
    event, project, organizer = make_event_with_finalized_project()
    award = Award.objects.create(event=event, name="Draft Award")
    AwardWinner.objects.create(award=award, project=project, selected_by=organizer, source="manual")
    page = Page.objects.create(event=event)
    PageBlock.objects.create(page=page, kind="results", position=0, config={})

    body = Client().get(f"/e/{event.public_id}/").content.decode()
    assert "Draft Award" not in body
    assert "Results will be announced after judging." in body
