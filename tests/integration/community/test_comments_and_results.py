from datetime import timedelta

import pytest
from accounts.models import Session, User
from community.models import Comment, Vote, VotingPlan
from django.test import Client
from django.utils import timezone
from events.models import Event, EventStatus
from projects.models import Project, Submission, SubmissionStatus, SubmissionVersion
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def cookie_client(token):
    client = Client()
    client.cookies["session"] = token
    return client


def make_fixture():
    organizer = User.objects.create_user(username="organizer", password="unused")
    participant = User.objects.create_user(username="member", password="unused")
    judge = User.objects.create_user(username="judge", password="unused")
    workspace = Workspace.objects.create(name="Dogfood", slug="dogfood")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=participant, workspace=workspace, role=Role.PARTICIPANT)
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
    event = Event.objects.create(
        workspace=workspace, name="Hack", slug="hack", status=EventStatus.OPEN, is_public=True
    )
    stage = Stage.objects.create(event=event, name="Finals")
    project = Project.objects.create(event=event, name="Autograder", created_by=organizer)
    submission = Submission.objects.create(project=project, stage=stage, updated_by=organizer)
    version = SubmissionVersion.objects.create(
        submission=submission, number=1, snapshot={}, digest="a" * 64, finalized_by=organizer
    )
    submission.status = SubmissionStatus.FINALIZED
    submission.current_version = version
    submission.save()
    return workspace, event, project, organizer, participant, judge


def comments_url(workspace, event, project, suffix=""):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        f"/projects/{project.public_id}/comments/{suffix}"
    )


def test_any_workspace_member_can_comment_and_read_comments_by_default():
    workspace, event, project, organizer, participant, judge = make_fixture()
    client = cookie_client(Session.issue(participant).token)
    created = client.post(
        comments_url(workspace, event, project),
        {"body": "Nice work!"},
        content_type="application/json",
    )
    assert created.status_code == 201

    judge_client = cookie_client(Session.issue(judge).token)
    listed = judge_client.get(comments_url(workspace, event, project)).json()
    assert len(listed) == 1
    assert listed[0]["body"] == "Nice work!"


def test_comment_visibility_can_be_restricted_to_organizers_only():
    workspace, event, project, organizer, participant, judge = make_fixture()
    VotingPlan.objects.create(
        event=event,
        opens_at=timezone.now(),
        closes_at=timezone.now() + timedelta(days=1),
        comment_visibility="organizer",
    )
    participant_client = cookie_client(Session.issue(participant).token)
    assert participant_client.get(comments_url(workspace, event, project)).status_code == 403
    assert (
        participant_client.post(
            comments_url(workspace, event, project), {"body": "hi"}, content_type="application/json"
        ).status_code
        == 403
    )

    organizer_client = cookie_client(Session.issue(organizer).token)
    assert organizer_client.get(comments_url(workspace, event, project)).status_code == 200


def test_comments_can_be_disabled_entirely_but_reading_still_works():
    workspace, event, project, organizer, participant, judge = make_fixture()
    VotingPlan.objects.create(
        event=event,
        opens_at=timezone.now(),
        closes_at=timezone.now() + timedelta(days=1),
        allow_comments=False,
    )
    client = cookie_client(Session.issue(participant).token)
    response = client.post(
        comments_url(workspace, event, project), {"body": "hi"}, content_type="application/json"
    )
    assert response.status_code == 400
    assert client.get(comments_url(workspace, event, project)).status_code == 200


def test_organizer_can_hide_a_comment_and_it_disappears_from_the_list():
    workspace, event, project, organizer, participant, judge = make_fixture()
    comment = Comment.objects.create(project=project, author=participant, body="rude comment")
    organizer_client = cookie_client(Session.issue(organizer).token)

    hidden = organizer_client.post(
        comments_url(workspace, event, project, f"{comment.public_id}/hide/")
    )
    assert hidden.status_code == 200

    listing = organizer_client.get(comments_url(workspace, event, project)).json()
    assert listing == []

    participant_client = cookie_client(Session.issue(participant).token)
    assert (
        participant_client.post(
            comments_url(workspace, event, project, f"{comment.public_id}/hide/")
        ).status_code
        == 403
    )


def test_empty_comment_body_is_rejected():
    workspace, event, project, organizer, participant, judge = make_fixture()
    client = cookie_client(Session.issue(participant).token)
    response = client.post(
        comments_url(workspace, event, project), {"body": "   "}, content_type="application/json"
    )
    assert response.status_code == 400


def results_url(workspace, event):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/voting/results/"


def test_results_are_hidden_from_the_public_until_published_and_closed():
    workspace, event, project, organizer, participant, judge = make_fixture()
    plan = VotingPlan.objects.create(
        event=event,
        identity_mode="authenticated",
        opens_at=timezone.now() - timedelta(hours=1),
        closes_at=timezone.now() + timedelta(hours=1),  # still open
    )
    Vote.objects.create(plan=plan, project=project, voter_key=f"user:{participant.public_id}")

    organizer_client = cookie_client(Session.issue(organizer).token)
    participant_client = cookie_client(Session.issue(participant).token)

    # Organizer can always see the tally, even mid-vote and unpublished.
    assert organizer_client.get(results_url(workspace, event)).status_code == 200
    assert participant_client.get(results_url(workspace, event)).status_code == 403

    # Publishing while still open still doesn't leak to the public.
    publish_url = (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
        "/voting-plan/publish-results/"
    )
    organizer_client.post(publish_url)
    assert participant_client.get(results_url(workspace, event)).status_code == 403

    # Once the window has actually closed, publication takes effect.
    plan.refresh_from_db()
    plan.closes_at = timezone.now() - timedelta(seconds=1)
    plan.save()
    response = participant_client.get(results_url(workspace, event))
    assert response.status_code == 200
    assert response.json()[0]["votes"] == 1
