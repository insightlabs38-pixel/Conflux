import csv
import io

import pytest
from accounts.models import User
from core.csv_safety import safe_cell
from evaluations.models import NormalizationRun
from integrations.demo_scenarios import generate_demo_event
from test_sponsor_portal import client_for

pytestmark = pytest.mark.django_db


def test_only_formula_text_is_neutralized_and_numbers_stay_numeric():
    for text in ("=1+1", "+x", "-x", "@sum", "\tx", "\rx"):
        assert safe_cell(text) == "'" + text
    for untouched in ("safe", "", -1.5, None):
        assert safe_cell(untouched) == untouched


def test_results_csv_neutralizes_project_names():
    event = generate_demo_event(seed=21, participants=3, judges=2)
    event.projects.filter(name=event.projects.order_by("name").first().name).update(
        name="=cmd|' /C calc'!A0"
    )
    plan = NormalizationRun.objects.get(plan__stage__event=event).plan
    organizer = User.objects.get(username="demo-hackathon-21-organizer")
    url = (
        f"/api/v1/workspaces/{event.workspace.public_id}/events/{event.public_id}/stages/"
        f"{plan.stage.public_id}/evaluation-plans/{plan.public_id}/results.csv"
    )
    response = client_for(organizer).get(url)
    assert response.status_code == 200, response.content
    names = [row["project"] for row in csv.DictReader(io.StringIO(response.content.decode()))]
    assert "'=cmd|' /C calc'!A0" in names and not any(n.startswith("=") for n in names)
