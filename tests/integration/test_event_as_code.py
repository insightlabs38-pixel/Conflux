import copy

import pytest
from audit.models import AuditEvent
from awards.models import Award
from events.models import Event, Track
from integrations import eventascode
from integrations.demo_scenarios import generate_demo_event
from projects.models import Project
from test_sponsor_portal import client_for
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db
JSON = "application/json"


def world():
    event = generate_demo_event(seed=51, participants=4, judges=2)
    organizer = event.workspace.memberships.get(role="organizer").user
    return event, organizer


def url(event, suffix=""):
    return (
        f"/api/v1/workspaces/{event.workspace.public_id}/events/{event.public_id}/as-code/{suffix}"
    )


def call(client, event, suffix, **body):
    return client.post(url(event, suffix), body, content_type=JSON)


def doc_of(event):
    return eventascode.export_document(event)


def test_export_is_deterministic_portable_and_a_fixed_point_of_plan():
    event, organizer = world()
    client = client_for(organizer)
    first = client.get(url(event)).json()
    assert first["document"] == client.get(url(event)).json()["document"] == doc_of(event)
    assert first["digest"] == eventascode.digest(event)
    text = str(first["document"])
    assert str(event.public_id) not in text and "public_id" not in text
    plan = call(client, event, "plan/", document=first["document"]).json()
    assert plan["ok"] and plan["changes"] == [] and plan["summary"] == {}


def test_plan_previews_exactly_what_apply_does_and_reapply_is_a_no_op():
    event, organizer = world()
    client = client_for(organizer)
    document = doc_of(event)
    document["event"]["description"] = "Rewritten"
    document["tracks"].append({"name": "Climate", "description": "New", "position": 9})
    document["tracks"][0]["description"] = "Changed"
    document["base_prizes"] = [
        {"name": "Swag", "kind": "swag", "track": "Climate", "description": "", "position": 0,
         "amount": None, "currency": ""}
    ]  # fmt: skip
    document["policies"] = [
        {"name": "Open", "ast": {"op": "true"}},
    ]
    document["page"]["blocks"].append(
        {"kind": "rich_text", "position": 5, "config": {"html": "<p>x</p>"}}
    )
    before_digest = eventascode.digest(event)
    plan = call(client, event, "plan/", document=document).json()
    assert plan["ok"], plan
    assert (
        eventascode.digest(event) == before_digest
        and not Track.objects.filter(name="Climate").exists()
    )
    applied = call(client, event, "apply/", document=document, expected_digest=before_digest)
    assert applied.status_code == 200, applied.content
    assert applied.json()["changes"] == plan["changes"]
    assert Track.objects.filter(event=event, name="Climate").exists()
    event.refresh_from_db()
    assert event.description == "Rewritten"
    again = call(client, event, "plan/", document=document).json()
    assert again["changes"] == [] and again["digest"] == applied.json()["digest"]
    audit = AuditEvent.objects.get(action="event.config_applied")
    assert (
        audit.metadata["before_digest"] == before_digest
        and audit.metadata["summary"]["create"] >= 3
    )


def test_stale_plans_are_rejected_and_do_not_change_anything():
    event, organizer = world()
    client = client_for(organizer)
    document = doc_of(event)
    document["event"]["description"] = "Mine"
    stale = eventascode.digest(event)
    Event.objects.filter(pk=event.pk).update(description="Someone else")
    response = call(client, event, "apply/", document=document, expected_digest=stale)
    assert response.status_code == 409 and response.json()["current_digest"] != stale
    event.refresh_from_db()
    assert event.description == "Someone else"
    assert (
        call(client, event, "apply/", document=document, expected_digest="x" * 10).status_code
        == 400
    )


@pytest.mark.parametrize(
    ("mutate", "section"),
    [
        (lambda d: d.update(bogus=[]), "bogus"),
        (lambda d: d.update(eventascode=2), "document"),
        (lambda d: d["tracks"].append({"name": d["tracks"][0]["name"]}), "tracks"),
        (lambda d: d["tracks"].append({"description": "no name"}), "tracks"),
        (lambda d: d["tracks"].append({"name": "X", "surprise": 1}), "tracks"),
        (lambda d: d["awards"][0].update(eligibility_track="Nope"), "awards"),
        (lambda d: d["stages"].append({"name": "S", "participation_mode": "wat"}), "stages"),
        (lambda d: d["event"].update(name="Renamed"), "event"),
        (lambda d: d["event"].update(starts_at="2026-01-01T00:00:00"), "event"),
        (lambda d: d.update(page={"theme": "x", "blocks": "no"}), "page"),
    ],
)
def test_invalid_documents_report_precise_errors_and_change_nothing(mutate, section):
    event, organizer = world()
    client = client_for(organizer)
    document = doc_of(event)
    mutate(document)
    digest = eventascode.digest(event)
    checked = call(client, event, "validate/", document=document).json()
    assert checked["valid"] is False and section in {e["section"] for e in checked["errors"]}
    plan = call(client, event, "plan/", document=document).json()
    assert plan["ok"] is False
    applied = call(client, event, "apply/", document=document, expected_digest=digest)
    assert applied.status_code == 400 and eventascode.digest(event) == digest


def test_immutable_evidence_and_referenced_resources_are_protected():
    event, organizer = world()
    client = client_for(organizer)
    digest = eventascode.digest(event)
    document = doc_of(event)
    document["awards"][0]["description"] = "Edited after publication"
    plan = call(client, event, "plan/", document=document).json()
    assert [e["message"] for e in plan["errors"]] == ["A published award cannot be changed."]
    document = doc_of(event)
    document["evaluation_plans"][0]["rubric_versions"][0]["criteria"][0]["weight"] = 9
    plan = call(client, event, "plan/", document=document).json()
    assert "immutable" in plan["errors"][0]["message"]
    document = doc_of(event)
    document["evaluation_plans"][0]["rubric_versions"].append(
        {"number": 1, "criteria": document["evaluation_plans"][0]["rubric_versions"][0]["criteria"]}
    )
    document["tracks"] = document["tracks"][:-1]
    document["awards"] = [a for a in document["awards"] if a["name"] != "Grand Prize"]
    plan = call(client, event, "plan/", document=document, prune=True).json()
    messages = " ".join(e["message"] for e in plan["errors"])
    assert "cannot be removed" in messages and "assigned to this track" in messages
    applied = call(client, event, "apply/", document=document, prune=True, expected_digest=digest)
    assert applied.status_code == 400 and eventascode.digest(event) == digest
    assert Award.objects.filter(event=event).count() == 4


def test_prune_is_opt_in_and_new_rubric_versions_append():
    event, organizer = world()
    client = client_for(organizer)
    Track.objects.create(event=event, name="Spare", position=9)
    document = doc_of(event)
    document["tracks"] = [t for t in document["tracks"] if t["name"] != "Spare"]
    plan = call(client, event, "plan/", document=document).json()
    assert plan["changes"] == [] and plan["unmanaged"] == {"tracks": ["Spare"]}
    digest = eventascode.digest(event)
    pruned = call(client, event, "apply/", document=document, prune=True, expected_digest=digest)
    assert pruned.status_code == 200 and pruned.json()["summary"] == {"delete": 1}
    assert not Track.objects.filter(name="Spare").exists()
    document["evaluation_plans"][0]["rubric_versions"].append(
        {
            "number": 2,
            "criteria": [{"id": "x", "name": "X", "weight": 1, "min_score": 1, "max_score": 5}],
        }
    )
    applied = call(
        client, event, "apply/", document=document, expected_digest=pruned.json()["digest"]
    )
    assert applied.status_code == 200, applied.content
    assert applied.json()["changes"][0]["key"].endswith("#2")
    document["evaluation_plans"][0]["rubric_versions"].append({"number": 1, "criteria": []})
    stale_number = call(client, event, "plan/", document=document).json()
    assert stale_number["ok"] is False


def test_document_applies_to_an_empty_event_and_reproduces_the_source():
    source, organizer = world()
    target = Event.objects.create(workspace=source.workspace, name="Blank", slug="blank")
    client = client_for(organizer)
    document = doc_of(source)
    digest = eventascode.digest(target)
    applied = call(client, target, "apply/", document=document, expected_digest=digest)
    assert applied.status_code == 200, applied.content
    target.refresh_from_db()
    result = doc_of(target)
    for section in eventascode.SECTIONS:
        assert result[section] == document[section], section
    assert result["event"]["description"] == document["event"]["description"]
    assert call(client, target, "plan/", document=document).json()["changes"] == []


def test_only_organizers_of_the_workspace_and_never_archived_or_foreign_events():
    event, organizer = world()
    participant = event.workspace.memberships.filter(role="participant").first().user
    document = doc_of(event)
    for user in (participant,):
        assert client_for(user).get(url(event)).status_code == 403
        assert call(client_for(user), event, "plan/", document=document).status_code == 403
    other = Workspace.objects.create(name="Other", slug="other-ws")
    foreign = Event.objects.create(workspace=other, name="F", slug="f")
    assert client_for(organizer).get(url(foreign)).status_code in (403, 404)
    Event.objects.filter(pk=event.pk).update(status="archived")
    plan = call(client_for(organizer), event, "plan/", document=copy.deepcopy(document)).json()
    assert plan["ok"] is False and "Archived" in plan["errors"][0]["message"]
    assert Project.objects.filter(event=event).count() == 4


def test_command_round_trips_yaml_and_needs_explicit_approval(tmp_path, capsys):
    import json

    import yaml
    from django.core.management import CommandError, call_command

    event, _ = world()
    call_command("eventascode", "export", str(event.public_id))
    exported = yaml.safe_load(capsys.readouterr().out)
    assert exported == doc_of(event)
    exported["event"]["description"] = "From YAML"
    path = tmp_path / "event.yaml"
    path.write_text(yaml.safe_dump(exported))
    call_command("eventascode", "validate", str(event.public_id), str(path))
    assert json.loads(capsys.readouterr().out)["valid"] is True
    call_command("eventascode", "plan", str(event.public_id), str(path))
    plan = json.loads(capsys.readouterr().out)
    with pytest.raises(CommandError, match="--digest"):
        call_command("eventascode", "apply", str(event.public_id), str(path))
    call_command(
        "eventascode", "apply", str(event.public_id), str(path), "--digest", plan["digest"]
    )
    event.refresh_from_db()
    assert event.description == "From YAML"
    with pytest.raises(CommandError, match="Current digest"):
        call_command(
            "eventascode", "apply", str(event.public_id), str(path), "--digest", plan["digest"]
        )
    path.write_text("tracks: [")
    with pytest.raises(CommandError, match="Not valid"):
        call_command("eventascode", "plan", str(event.public_id), str(path))
