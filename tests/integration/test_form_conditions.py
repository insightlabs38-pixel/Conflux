import pytest
from accounts.models import Session, User
from django.core.exceptions import ValidationError
from django.test import Client
from events.models import Event
from forms.services import create_form, publish_form, save_draft, save_response
from forms.validation import field_visible
from projects.services import create_project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def setup_form():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    user = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(workspace=workspace, user=user, role=Role.PARTICIPANT)
    return user, create_project(event, user, "Project"), create_form(event, "Application")


def conditional_schema():
    return {
        "fields": [
            {
                "id": "kind",
                "type": "select",
                "label": "Kind",
                "options": ["build", "research"],
                "required": True,
            },
            {
                "id": "demo",
                "type": "url",
                "label": "Demo",
                "visible_if": {"field": "kind", "equals": "build"},
                "required_if": {"field": "kind", "equals": "build"},
            },
            {"id": "judge_note", "type": "text", "label": "Judge note", "visible_to": ["judge"]},
            {
                "id": "public_title",
                "type": "text",
                "label": "Public title",
                "visible_to": ["public"],
            },
        ]
    }


def test_conditional_visibility_and_requiredness_follow_answers():
    user, project, form = setup_form()
    save_draft(form, conditional_schema())
    version = publish_form(form)
    save_response(project, version, user, {"kind": "research"})
    with pytest.raises(ValidationError, match="not visible"):
        save_response(project, version, user, {"kind": "research", "demo": "https://example.com"})
    with pytest.raises(ValidationError, match="required"):
        save_response(project, version, user, {"kind": "build"})
    save_response(project, version, user, {"kind": "build", "demo": "https://example.com"})
    assert field_visible(version.schema["fields"][1], "participant", {"kind": "build"})
    assert not field_visible(version.schema["fields"][1], "participant", {"kind": "research"})


def test_private_fields_cannot_be_written_as_participant():
    user, project, form = setup_form()
    save_draft(form, conditional_schema())
    version = publish_form(form)
    with pytest.raises(ValidationError, match="not visible"):
        save_response(project, version, user, {"kind": "research", "judge_note": "secret"})
    assert field_visible(version.schema["fields"][2], "judge", {})
    assert not field_visible(version.schema["fields"][2], "public", {})
    assert field_visible(version.schema["fields"][3], "public", {})


def test_participant_api_filters_existing_private_answers():
    user, project, form = setup_form()
    save_draft(form, conditional_schema())
    version = publish_form(form)
    save_response(
        project, version, user, {"kind": "research", "judge_note": "private"}, scope="judge"
    )
    event = project.event
    url = (
        f"/api/v1/workspaces/{event.workspace.public_id}/events/{event.public_id}/"
        f"projects/{project.public_id}/forms/{version.public_id}/response/"
    )
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    assert client.get(url).json()["answers"] == {"kind": "research"}
    assert (
        client.put(
            url, {"answers": {"kind": "research"}}, content_type="application/json"
        ).status_code
        == 200
    )
    assert (
        dict(project.form_responses.get(version=version).answers.values_list("field_id", "value"))[
            "judge_note"
        ]
        == "private"
    )


@pytest.mark.parametrize(
    "bad_field",
    [
        {
            "id": "dependent",
            "type": "text",
            "label": "Dependent",
            "visible_if": {"field": "missing", "equals": "A"},
        },
        {
            "id": "dependent",
            "type": "text",
            "label": "Dependent",
            "required_if": {"field": "dependent", "equals": "A"},
        },
        {
            "id": "dependent",
            "type": "text",
            "label": "Dependent",
            "visible_if": {"field": "kind", "equals": "unknown"},
        },
        {
            "id": "dependent",
            "type": "text",
            "label": "Dependent",
            "visible_to": ["public"],
            "visible_if": {"field": "kind", "equals": "build"},
        },
    ],
)
def test_invalid_conditions_fail_at_schema_publish_time(bad_field):
    _, _, form = setup_form()
    schema = {
        "fields": [
            {
                "id": "kind",
                "type": "select",
                "label": "Kind",
                "options": ["build"],
                "visible_to": ["participant"],
            },
            bad_field,
        ]
    }
    with pytest.raises(ValidationError):
        save_draft(form, schema)
