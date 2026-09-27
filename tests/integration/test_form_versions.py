import pytest
from django.core.exceptions import ValidationError
from events.models import Event
from forms.models import FormVersion
from forms.services import create_form, publish_form, save_draft
from stages.models import Stage
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def event_fixture():
    workspace = Workspace.objects.create(name="W", slug="w")
    return Event.objects.create(workspace=workspace, name="E", slug="e")


def test_publishing_snapshots_draft_and_numbers_versions():
    event = event_fixture()
    form = create_form(event, "Application")
    draft = {"fields": [{"id": "pitch"}]}
    save_draft(form, draft)
    first = publish_form(form)
    draft["fields"][0]["id"] = "tampered"
    save_draft(form, {"fields": [{"id": "pitch"}, {"id": "url"}]})
    second = publish_form(form)
    first.refresh_from_db()
    assert first.number == 1
    assert first.schema == {"fields": [{"id": "pitch"}]}
    assert second.number == 2
    assert len(second.schema["fields"]) == 2


def test_published_version_rejects_update_and_delete():
    version = publish_form(create_form(event_fixture(), "Application"))
    version.schema = {"fields": [{"id": "changed"}]}
    with pytest.raises(ValidationError, match="immutable"):
        version.save()
    with pytest.raises(ValidationError, match="immutable"):
        version.delete()
    assert FormVersion.objects.get(pk=version.pk).schema == {"fields": []}


def test_form_rejects_cross_event_stage_and_duplicate_field_ids():
    event = event_fixture()
    other = Event.objects.create(workspace=event.workspace, name="Other", slug="other")
    stage = Stage.objects.create(event=other, name="Other stage")
    with pytest.raises(ValidationError, match="Stage must belong"):
        create_form(event, "Wrong", stage=stage)
    form = create_form(event, "Valid")
    with pytest.raises(ValidationError, match="unique"):
        save_draft(form, {"fields": [{"id": "same"}, {"id": "same"}]})
