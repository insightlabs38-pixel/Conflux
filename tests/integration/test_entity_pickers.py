"""PD-F004-B05-T05: the records an organizer must choose (a team, a person) are listed by name from
sources that already exist, so no screen needs an id typed in."""

import pytest
from accounts.models import User
from participation.models import Team
from projects.models import Project, ProjectMembership

from tests.integration.test_entity_query import world

pytestmark = pytest.mark.django_db


def test_a_team_is_found_through_its_project_by_name_and_id():
    workspace, event, organizer, client, _, base = world()
    alpha = Team.objects.create(event=event, name="Alpha")
    Project.objects.create(event=event, name="One", created_by=organizer, team=alpha)
    Project.objects.create(event=event, name="Two", created_by=organizer)  # no team
    response = client.get(
        base + "projects/",
        {
            "columns": "team,team_id",
            "sort": "team",
            "filter": '{"field":"team","op":"is_null","value":false}',
        },
    )
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert [(r["team"], r["team_id"]) for r in rows] == [("Alpha", str(alpha.public_id))]


def test_the_team_reference_is_not_offered_as_a_default_column_or_a_filter():
    _, _, _, client, judge, base = world()
    field = next(
        f
        for e in client.get(base).json()
        if e["key"] == "projects"
        for f in e["fields"]
        if f["key"] == "team_id"
    )
    assert field["default"] is False and field["sortable"] is False and field["filterable"] is False
    assert judge.get(base + "projects/").status_code == 403


def test_participants_are_listed_by_username_for_organizers_only():
    workspace, event, organizer, client, judge, _ = world()
    ada = User.objects.create_user(username="ada", password="unused")
    project = Project.objects.create(event=event, name="P", created_by=organizer)
    ProjectMembership.objects.create(project=project, user=ada)
    url = f"/api/v1/workspaces/{workspace.public_id}/portfolio/participants/"
    rows = client.get(url, {"q": "ad", "limit": 100}).json()["results"]
    assert [(r["username"], r["user"]) for r in rows] == [("ada", str(ada.public_id))]
    assert judge.get(url).status_code == 403
