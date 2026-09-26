"""FX-003: exercises the same seven checks run.py makes, directly against
Django's test client, so a regression here is caught before the official
checker would ever see it.
"""

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db


def client_for(header):
    name, _, value = header.partition(":")
    cookie_name, _, token = value.strip().partition("=")
    client = Client()
    client.cookies[cookie_name.strip()] = token.strip()
    return client


# --- T1 -----------------------------------------------------------------


def test_gallery_is_public(acceptance_bootstrap, dogfood_config):
    response = Client().get(dogfood_config["routes"]["gallery"])
    assert response.status_code == 200


def test_gallery_shows_a_fixture_project(acceptance_bootstrap, dogfood_config):
    response = Client().get(dogfood_config["routes"]["gallery"])
    assert "glass signal" in response.content.decode().lower()


def test_closed_event_refuses_submission(acceptance_bootstrap, dogfood_config):
    client = client_for(dogfood_config["auth"]["participant"])
    response = client.post(
        dogfood_config["routes"]["submit"],
        {"title": "late-probe", "summary": "probe"},
        content_type="application/json",
    )
    assert 400 <= response.status_code < 500


# --- T2 -----------------------------------------------------------------


def test_judge_sees_own_scores(acceptance_bootstrap, dogfood_config):
    client = client_for(dogfood_config["auth"]["judge_a"])
    response = client.get(dogfood_config["routes"]["judge_scores"])
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_judge_cannot_see_peer_scores(acceptance_bootstrap, dogfood_config):
    client = client_for(dogfood_config["auth"]["judge_b"])
    response = client.get(dogfood_config["routes"]["peer_scores"])
    assert response.status_code in (401, 403)


def test_participant_is_not_a_judge(acceptance_bootstrap, dogfood_config):
    client = client_for(dogfood_config["auth"]["participant"])
    response = client.get(dogfood_config["routes"]["judge_scores"])
    assert response.status_code in (401, 403)


def test_organizer_can_export_csv(acceptance_bootstrap, dogfood_config):
    client = client_for(dogfood_config["auth"]["organizer"])
    response = client.get(dogfood_config["routes"]["csv_export"])
    assert response.status_code == 200
    first_line = response.content.decode().splitlines()[0]
    assert "," in first_line


def test_judge_cannot_export_csv(acceptance_bootstrap, dogfood_config):
    client = client_for(dogfood_config["auth"]["judge_a"])
    response = client.get(dogfood_config["routes"]["csv_export"])
    assert response.status_code in (401, 403)
