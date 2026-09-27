import pytest
from accounts.models import User
from artifacts.models import Artifact, ArtifactKind, ArtifactVisibility, can_view_artifact
from django.core.exceptions import ValidationError
from events.models import Event
from projects.services import create_project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def setup_project():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    user = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(workspace=workspace, user=user, role=Role.PARTICIPANT)
    return create_project(event, user, "Project"), user


def test_artifact_kind_registry_and_visibility():
    project, user = setup_project()
    public = Artifact(
        project=project,
        kind=ArtifactKind.REPOSITORY,
        visibility=ArtifactVisibility.PUBLIC,
        title="Repo",
        external_url="https://example.com/repo",
        created_by=user,
    )
    public.full_clean()
    public.save()
    assert can_view_artifact(public)
    private = Artifact(
        project=project,
        kind=ArtifactKind.FILE,
        visibility=ArtifactVisibility.PARTICIPANT,
        title="Draft",
        created_by=user,
    )
    private.full_clean()
    private.save()
    assert can_view_artifact(private, user=user, role="participant")
    assert not can_view_artifact(private, role="participant")
    assert not can_view_artifact(
        private,
        user=User.objects.create_user(username="other", password="unused"),
        role="participant",
    )


def test_secret_and_external_source_rules_fail_closed():
    project, user = setup_project()
    secret = Artifact(
        project=project,
        kind=ArtifactKind.SECRET,
        visibility=ArtifactVisibility.PUBLIC,
        title="Secret",
        created_by=user,
    )
    with pytest.raises(ValidationError, match="Secret evidence"):
        secret.full_clean()
    bad_url = Artifact(
        project=project,
        kind=ArtifactKind.LIVE_URL,
        visibility=ArtifactVisibility.PUBLIC,
        title="Link",
        external_url="javascript:alert(1)",
        created_by=user,
    )
    with pytest.raises(ValidationError):
        bad_url.full_clean()
    stored_with_url = Artifact(
        project=project,
        kind=ArtifactKind.IMAGE,
        visibility=ArtifactVisibility.PUBLIC,
        title="Image",
        external_url="https://example.com/img",
        created_by=user,
    )
    with pytest.raises(ValidationError, match="Stored artifacts"):
        stored_with_url.full_clean()
