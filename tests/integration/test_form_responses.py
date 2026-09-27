import pytest
from accounts.models import Session, User
from django.core.exceptions import ValidationError
from django.test import Client
from events.models import Event
from forms.models import FormAnswer, FormResponse
from forms.services import create_form, publish_form, save_draft, save_response
from projects.services import create_project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def setup_form():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    user = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(workspace=workspace, user=user, role=Role.PARTICIPANT)
    project = create_project(event, user, "Project")
    form = create_form(event, "Submission")
    return event, user, project, form


def test_typed_answers_are_stored_against_an_exact_published_version():
    _, user, project, form = setup_form()
    fields = [
        {"id": "pitch", "type": "text", "label": "Pitch", "required": True},
        {"id": "details", "type": "rich_text", "label": "Details"},
        {"id": "budget", "type": "number", "label": "Budget"},
        {"id": "track", "type": "select", "label": "Track", "options": ["AI", "Health"]},
        {"id": "tags", "type": "multi_select", "label": "Tags", "options": ["A", "B"]},
        {"id": "ready", "type": "boolean", "label": "Ready"},
        {"id": "site", "type": "url", "label": "Site"},
        {"id": "day", "type": "date", "label": "Day"},
        {"id": "time", "type": "datetime", "label": "Time"},
        {"id": "file", "type": "artifact", "label": "File"},
    ]
    save_draft(form, {"fields": fields})
    version = publish_form(form)
    answers = {
        "pitch": "Hello",
        "details": "**hello**",
        "budget": 10.5,
        "track": "AI",
        "tags": ["A", "B"],
        "ready": False,
        "site": "https://example.com",
        "day": "2026-09-27",
        "time": "2026-09-27T12:00:00Z",
        "file": "00000000-0000-0000-0000-000000000001",
    }
    response = save_response(project, version, user, answers)
    assert FormResponse.objects.get(pk=response.pk).version == version
    assert dict(response.answers.values_list("field_id", "value")) == answers
    answers["pitch"] = "Changed"
    save_response(project, version, user, answers)
    assert FormResponse.objects.count() == 1
    assert FormAnswer.objects.count() == len(fields)
    assert response.answers.get(field_id="pitch").value == "Changed"


@pytest.mark.parametrize(
    "field,value",
    [
        ({"id": "num", "type": "number", "label": "Number"}, True),
        ({"id": "num", "type": "number", "label": "Number"}, "NaN"),
        ({"id": "choice", "type": "select", "label": "Choice", "options": ["A"]}, "B"),
        (
            {"id": "choices", "type": "multi_select", "label": "Choices", "options": ["A"]},
            ["A", "A"],
        ),
        ({"id": "flag", "type": "boolean", "label": "Flag"}, "true"),
        ({"id": "site", "type": "url", "label": "Site"}, "javascript:alert(1)"),
        ({"id": "day", "type": "date", "label": "Day"}, "2026-02-30"),
        ({"id": "file", "type": "artifact", "label": "File"}, "not-an-id"),
    ],
)
def test_invalid_typed_answer_is_rejected_atomically(field, value):
    _, user, project, form = setup_form()
    save_draft(form, {"fields": [field]})
    version = publish_form(form)
    with pytest.raises(ValidationError):
        save_response(project, version, user, {field["id"]: value})
    assert FormResponse.objects.count() == 0


def test_required_unknown_and_outsider_answers_are_rejected():
    event, user, project, form = setup_form()
    save_draft(
        form, {"fields": [{"id": "pitch", "type": "text", "label": "Pitch", "required": True}]}
    )
    version = publish_form(form)
    with pytest.raises(ValidationError, match="required"):
        save_response(project, version, user, {})
    with pytest.raises(ValidationError, match="unknown"):
        save_response(project, version, user, {"pitch": "hi", "other": "x"})
    outsider = User.objects.create_user(username="outsider", password="unused")
    with pytest.raises(ValidationError, match="project members"):
        save_response(project, version, outsider, {"pitch": "hi"})
    other_event = Event.objects.create(workspace=event.workspace, name="Other", slug="other")
    other_form = create_form(other_event, "Other")
    with pytest.raises(ValidationError, match="same event"):
        save_response(project, publish_form(other_form), user, {})


def test_response_api_enforces_project_membership_and_validation():
    event, user, project, form = setup_form()
    save_draft(
        form, {"fields": [{"id": "pitch", "type": "text", "label": "Pitch", "required": True}]}
    )
    version = publish_form(form)
    url = (
        f"/api/v1/workspaces/{event.workspace.public_id}/events/{event.public_id}/"
        f"projects/{project.public_id}/forms/{version.public_id}/response/"
    )
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    assert client.get(url).json()["answers"] == {}
    assert client.put(url, {"answers": {}}, content_type="application/json").status_code == 400
    response = client.put(url, {"answers": {"pitch": "Hello"}}, content_type="application/json")
    assert response.status_code == 200
    assert client.get(url).json()["answers"] == {"pitch": "Hello"}
    outsider = User.objects.create_user(username="other", password="unused")
    Membership.objects.create(workspace=event.workspace, user=outsider, role=Role.PARTICIPANT)
    client.cookies["session"] = Session.issue(outsider).token
    assert client.get(url).status_code == 404
    assert (
        client.put(
            url, {"answers": {"pitch": "Steal"}}, content_type="application/json"
        ).status_code
        == 404
    )


def test_project_form_list_exposes_latest_published_participant_fields_only():
    event, user, project, form = setup_form()
    save_draft(form, {"fields": [{"id": "draft", "type": "text", "label": "Draft"}]})
    save_draft(
        form,
        {
            "fields": [
                {"id": "pitch", "type": "text", "label": "Pitch"},
                {"id": "score", "type": "number", "label": "Score", "visible_to": ["judge"]},
            ]
        },
    )
    publish_form(form)
    save_draft(
        form,
        {
            "fields": [
                {"id": "pitch", "type": "text", "label": "Pitch", "required": True},
                {"id": "private", "type": "text", "label": "Private", "visible_to": ["organizer"]},
            ]
        },
    )
    latest = publish_form(form)
    unpublished = create_form(event, "Unpublished")
    assert unpublished.versions.count() == 0
    url = (
        f"/api/v1/workspaces/{event.workspace.public_id}/events/{event.public_id}/"
        f"projects/{project.public_id}/forms/"
    )
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    response = client.get(url)
    assert response.status_code == 200
    assert response.json() == [
        {
            "public_id": str(latest.public_id),
            "name": "Submission",
            "stage": None,
            "number": 2,
            "schema": {
                "fields": [{"id": "pitch", "type": "text", "label": "Pitch", "required": True}]
            },
        }
    ]
    assert client.put(url, {"answers": {}}, content_type="application/json").status_code == 405
    outsider = User.objects.create_user(username="form-outsider", password="unused")
    Membership.objects.create(workspace=event.workspace, user=outsider, role=Role.PARTICIPANT)
    client.cookies["session"] = Session.issue(outsider).token
    assert client.get(url).status_code == 404
