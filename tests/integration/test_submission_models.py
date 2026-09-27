import pytest
from accounts.models import User
from django.core.exceptions import ValidationError
from events.models import Event
from projects.models import Submission, SubmissionVersion
from projects.services import create_project
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def setup_submission():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    stage = Stage.objects.create(event=event, name="Build")
    user = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(workspace=workspace, user=user, role=Role.PARTICIPANT)
    project = create_project(event, user, "Project")
    return Submission.objects.create(project=project, stage=stage, updated_by=user), user


def test_draft_and_finalized_snapshot_have_distinct_identity():
    submission, user = setup_submission()
    version = SubmissionVersion.objects.create(
        submission=submission,
        number=1,
        snapshot={"title": "Frozen"},
        digest="a" * 64,
        finalized_by=user,
    )
    submission.current_version = version
    submission.status = "finalized"
    submission.full_clean()
    submission.save()
    assert submission.project.public_id != submission.public_id
    assert version.public_id != submission.public_id
    assert submission.current_version == version
    assert submission.draft_payload == {}


def test_finalized_version_rejects_edits_and_deletion():
    submission, user = setup_submission()
    version = SubmissionVersion.objects.create(
        submission=submission,
        number=1,
        snapshot={"title": "Frozen"},
        digest="a" * 64,
        finalized_by=user,
    )
    version.snapshot = {"title": "Changed"}
    with pytest.raises(ValidationError, match="immutable"):
        version.save()
    with pytest.raises(ValidationError, match="immutable"):
        version.delete()
    assert SubmissionVersion.objects.get(pk=version.pk).snapshot == {"title": "Frozen"}


def test_submission_stage_is_event_scoped():
    submission, user = setup_submission()
    other = Event.objects.create(
        workspace=submission.project.event.workspace, name="Other", slug="other"
    )
    wrong = Stage.objects.create(event=other, name="Wrong")
    submission.stage = wrong
    with pytest.raises(ValidationError, match="project's event"):
        submission.full_clean()
