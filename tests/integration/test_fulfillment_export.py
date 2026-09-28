import csv
import io

import pytest
from audit.models import AuditEvent
from awards.models import Award, PrizeFulfillment
from projects.models import ProjectMembership
from test_sponsor_portal import (
    _create_award_with_winner,
    awards_base,
    client_for,
    fixture,
)

pytestmark = pytest.mark.django_db


def setup_case(publish=True):
    workspace, event, project, organizer, sponsor, other_sponsor, participant = fixture()
    project.name = "=HYPERLINK(1)"
    project.save()
    participant.email = "person@example.com"
    participant.save()
    ProjectMembership.objects.create(project=project, user=participant, role="member")
    organizer_client = client_for(organizer)
    award_id = _create_award_with_winner(organizer_client, workspace, event, project)
    base = awards_base(workspace, event)
    organizer_client.put(base + f"{award_id}/sponsors/{sponsor.public_id}/")
    if publish:
        assert organizer_client.post(base + f"{award_id}/publish/").status_code == 200
    PrizeFulfillment.objects.update(note="ship to 1 Main St")
    return workspace, event, project, organizer_client, sponsor, other_sponsor, participant


def url(workspace, event, suffix="fulfillment-export/"):
    return awards_base(workspace, event) + suffix


def test_default_report_is_minimal_and_sponsors_get_no_personal_data():
    workspace, event, _, organizer, sponsor, other, _ = setup_case()
    row = organizer.get(url(workspace, event)).json()["rows"][0]
    assert set(row) == {
        "handoff_reference", "award", "component", "kind", "quantity", "amount",
        "currency", "project", "team", "state", "updated_at",
    }  # fmt: skip
    assert row["amount"] == "100.00" and row["state"] == "pending"
    body = client_for(sponsor).get(url(workspace, event)).content.decode()
    assert "person@example.com" not in body and "ship to" not in body
    assert client_for(other).get(url(workspace, event)).json() == {"rows": []}


def test_only_organizers_can_opt_into_contacts_and_notes():
    workspace, event, _, organizer, sponsor, _, participant = setup_case()
    full = organizer.get(url(workspace, event) + "?include_recipients=true&include_notes=true")
    row = full.json()["rows"][0]
    assert row["note"] == "ship to 1 Main St"
    assert row["recipients"] == [{"username": "participant", "email": "person@example.com"}]
    for option in ("include_recipients", "include_notes"):
        assert client_for(sponsor).get(url(workspace, event) + f"?{option}=true").status_code == 403
    assert client_for(participant).get(url(workspace, event)).status_code == 403
    assert (
        client_for(participant).get(url(workspace, event, "fulfillment-export.csv")).status_code
        == 403
    )


def test_unpublished_awards_are_excluded_and_state_filter_validated():
    workspace, event, _, organizer, _, _, _ = setup_case(publish=False)
    assert organizer.get(url(workspace, event)).json() == {"rows": []}
    assert organizer.get(url(workspace, event) + "?state=bogus").status_code == 400
    Award.objects.update(published_at="2026-01-01T00:00:00Z")
    assert len(organizer.get(url(workspace, event)).json()["rows"]) == 1
    assert organizer.get(url(workspace, event) + "?state=sent").json() == {"rows": []}


def test_csv_neutralizes_formulas_and_matches_json_columns():
    workspace, event, _, organizer, _, _, _ = setup_case()
    response = organizer.get(
        url(workspace, event, "fulfillment-export.csv") + "?include_notes=true"
    )
    assert response["Content-Type"].startswith("text/csv")
    rows = list(csv.DictReader(io.StringIO(response.content.decode())))
    assert rows[0]["project"] == "'=HYPERLINK(1)" and rows[0]["note"] == "ship to 1 Main St"
    assert "recipients" not in rows[0]


def test_every_export_is_audited_with_its_disclosure_options():
    workspace, event, _, organizer, sponsor, _, _ = setup_case()
    organizer.get(url(workspace, event) + "?include_recipients=true")
    client_for(sponsor).get(url(workspace, event))
    logged = list(AuditEvent.objects.filter(action="award.fulfillment_exported").order_by("id"))
    assert [(e.metadata["include_recipients"], e.metadata["rows"]) for e in logged] == [
        (True, 1),
        (False, 1),
    ]
    assert "person@example.com" not in str([e.metadata for e in logged])
