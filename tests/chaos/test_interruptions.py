from datetime import timedelta
from unittest.mock import patch

import pytest
from accounts.models import User
from artifacts.models import Artifact, ArtifactStatus, ArtifactUploadIntent
from artifacts.services import begin_upload, complete_upload
from artifacts.storage import MULTIPART_THRESHOLD
from audit.models import DomainEvent
from botocore.exceptions import ClientError
from django.core.exceptions import ValidationError
from django.db import OperationalError
from events.models import Event
from integrations.models import WebhookDelivery, WebhookSubscription
from integrations.webhooks import deliver_pending, stage_deliveries
from projects.services import create_project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def outbox():
    workspace = Workspace.objects.create(name="Chaos", slug="chaos")
    subscription = WebhookSubscription.objects.create(
        workspace=workspace,
        url="https://receiver.example/hook",
        event_types=["chaos.changed"],
    )
    event = DomainEvent.objects.create(workspace=workspace, event_type="chaos.changed")
    return subscription, event


def test_database_interruption_rolls_back_staging_and_can_resume(outbox):
    subscription, event = outbox
    with patch.object(DomainEvent, "save", side_effect=OperationalError("connection lost")):
        with pytest.raises(OperationalError):
            stage_deliveries()
    event.refresh_from_db()
    assert event.status == DomainEvent.Status.PENDING
    assert event.processed_at is None
    assert not WebhookDelivery.objects.exists()
    assert stage_deliveries() == 1
    assert stage_deliveries() == 0
    assert WebhookDelivery.objects.get().subscription == subscription


def test_worker_dies_after_remote_acceptance_and_retries_same_event(outbox):
    stage_deliveries()
    accepted = []

    def accept_then_die(subscription, event, body, *, headers):
        accepted.append((event.public_id, body))
        raise SystemExit("worker killed before recording acknowledgement")

    with patch("integrations.webhooks.send_delivery", side_effect=accept_then_die):
        with pytest.raises(SystemExit):
            deliver_pending()
    delivery = WebhookDelivery.objects.get()
    assert delivery.status == WebhookDelivery.Status.PENDING
    assert delivery.attempts == 1
    assert delivery.completed_at is None
    assert delivery.history.get().completed_at is None
    with patch("integrations.webhooks.send_delivery") as sender:
        assert deliver_pending() == 0
        sender.assert_not_called()

    def accept(subscription, event, body, *, headers):
        accepted.append((event.public_id, body))
        return 204

    with (
        patch("integrations.webhooks.timezone.now", return_value=delivery.next_attempt_at),
        patch("integrations.webhooks.send_delivery", side_effect=accept),
    ):
        assert deliver_pending() == 1
    delivery.refresh_from_db()
    assert delivery.status == WebhookDelivery.Status.SUCCEEDED
    assert delivery.attempts == 2
    assert accepted[0] == accepted[1]
    assert delivery.history.count() == 2


@pytest.mark.parametrize("failure", [TimeoutError("response lost"), 503])
def test_webhook_outage_preserves_pending_work_until_backoff_expires(outbox, failure):
    stage_deliveries()
    options = (
        {"side_effect": failure} if isinstance(failure, Exception) else {"return_value": failure}
    )
    with patch("integrations.webhooks.send_delivery", **options):
        assert deliver_pending() == 1
    delivery = WebhookDelivery.objects.get()
    assert delivery.status == WebhookDelivery.Status.PENDING
    assert delivery.last_error
    with patch("integrations.webhooks.send_delivery", return_value=204) as sender:
        with patch(
            "integrations.webhooks.timezone.now",
            return_value=delivery.next_attempt_at - timedelta(microseconds=1),
        ):
            assert deliver_pending() == 0
        sender.assert_not_called()
        with patch("integrations.webhooks.timezone.now", return_value=delivery.next_attempt_at):
            assert deliver_pending() == 1
    delivery.refresh_from_db()
    assert delivery.status == WebhookDelivery.Status.SUCCEEDED
    assert delivery.last_error == ""


class InterruptedStorage:
    def __init__(self):
        self.completed = False
        self.fail_head = False

    def ensure_bucket(self):
        pass

    def start_multipart(self, key, content_type, artifact_id, size, expires):
        self.info = {
            "ContentLength": size,
            "ContentType": content_type,
            "Metadata": {"artifact-id": artifact_id},
        }
        return "upload", ["https://storage.example/1", "https://storage.example/2"]

    def complete_multipart(self, key, upload_id, parts):
        if self.completed:
            raise ClientError({"Error": {"Code": "NoSuchUpload"}}, "CompleteMultipartUpload")
        self.completed = True

    def head(self, key):
        if self.fail_head:
            raise TimeoutError("storage unavailable")
        if not self.completed:
            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "HeadObject")
        return self.info


@pytest.fixture
def upload():
    workspace = Workspace.objects.create(name="Uploads", slug="uploads")
    event = Event.objects.create(workspace=workspace, name="Event", slug="event")
    user = User.objects.create_user(username="participant")
    Membership.objects.create(workspace=workspace, user=user, role=Role.PARTICIPANT)
    project = create_project(event, user, "Project")
    storage = InterruptedStorage()
    artifact, intent, _ = begin_upload(
        project,
        user,
        kind="file",
        visibility="participant",
        title="File",
        byte_size=MULTIPART_THRESHOLD,
        content_type="application/pdf",
        storage=storage,
    )
    return artifact, intent, user, storage


PARTS = [{"PartNumber": 1, "ETag": "first"}, {"PartNumber": 2, "ETag": "second"}]


def assert_pending(artifact, intent):
    artifact.refresh_from_db()
    intent.refresh_from_db()
    assert artifact.status == ArtifactStatus.PENDING
    assert artifact.object_key == ""
    assert intent.completed_at is None


def test_object_store_interruption_after_completion_can_resume(upload):
    artifact, intent, user, storage = upload
    storage.fail_head = True
    with pytest.raises(ValidationError, match="not found"):
        complete_upload(intent, user, parts=PARTS, storage=storage)
    assert storage.completed
    assert_pending(artifact, intent)
    storage.fail_head = False
    assert (
        complete_upload(intent, user, parts=PARTS, storage=storage).status
        == ArtifactStatus.UPLOADED
    )
    with pytest.raises(ValidationError, match="already completed"):
        complete_upload(intent, user, parts=PARTS, storage=storage)


def test_database_failure_after_storage_completion_can_resume(upload):
    artifact, intent, user, storage = upload
    with patch.object(ArtifactUploadIntent, "save", side_effect=OperationalError("db lost")):
        with pytest.raises(OperationalError):
            complete_upload(intent, user, parts=PARTS, storage=storage)
    assert_pending(artifact, intent)
    assert (
        complete_upload(intent, user, parts=PARTS, storage=storage).status
        == ArtifactStatus.UPLOADED
    )
    assert Artifact.objects.count() == 1


@pytest.mark.parametrize("field", ["ContentLength", "ContentType", "Metadata"])
def test_recovery_does_not_trust_a_mismatched_completed_object(upload, field):
    artifact, intent, user, storage = upload
    storage.completed = True
    storage.info[field] = {} if field == "Metadata" else "wrong"
    with pytest.raises(ValidationError, match="does not match"):
        complete_upload(intent, user, parts=PARTS, storage=storage)
    assert_pending(artifact, intent)


def test_recovery_does_not_swallow_other_storage_errors(upload):
    artifact, intent, user, storage = upload
    error = ClientError({"Error": {"Code": "AccessDenied"}}, "CompleteMultipartUpload")
    with patch.object(storage, "complete_multipart", side_effect=error):
        with pytest.raises(ClientError):
            complete_upload(intent, user, parts=PARTS, storage=storage)
    assert_pending(artifact, intent)
