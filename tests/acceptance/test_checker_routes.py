"""FX-003: exercises the same seven checks run.py makes, directly against
Django's test client, so a regression here is caught before the official
checker would ever see it.
"""

import tomllib
from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

pytestmark = pytest.mark.django_db

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def bootstrapped():
    call_command("import_fixture", "fixtures/fixtures.json")
    call_command("seed_acceptance_identities")
    call_command("link_judge_identities")
    with open(REPO_ROOT / ".dogfood.toml", "rb") as f:
        cfg = tomllib.load(f)
    return cfg


def client_for(header):
    name, _, value = header.partition(":")
    cookie_name, _, token = value.strip().partition("=")
    client = Client()
    client.cookies[cookie_name.strip()] = token.strip()
    return client


# --- T1 -----------------------------------------------------------------


def test_gallery_is_public(bootstrapped):
    response = Client().get(bootstrapped["routes"]["gallery"])
    assert response.status_code == 200


def test_gallery_shows_a_fixture_project(bootstrapped):
    response = Client().get(bootstrapped["routes"]["gallery"])
    assert "glass signal" in response.content.decode().lower()


def test_closed_event_refuses_submission(bootstrapped):
    client = client_for(bootstrapped["auth"]["participant"])
    response = client.post(
        bootstrapped["routes"]["submit"],
        {"title": "late-probe", "summary": "probe"},
        content_type="application/json",
    )
    assert 400 <= response.status_code < 500


# --- T2 -----------------------------------------------------------------


def test_judge_sees_own_scores(bootstrapped):
    client = client_for(bootstrapped["auth"]["judge_a"])
    response = client.get(bootstrapped["routes"]["judge_scores"])
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_judge_cannot_see_peer_scores(bootstrapped):
    client = client_for(bootstrapped["auth"]["judge_b"])
    response = client.get(bootstrapped["routes"]["peer_scores"])
    assert response.status_code in (401, 403)


def test_participant_is_not_a_judge(bootstrapped):
    client = client_for(bootstrapped["auth"]["participant"])
    response = client.get(bootstrapped["routes"]["judge_scores"])
    assert response.status_code in (401, 403)


def test_organizer_can_export_csv(bootstrapped):
    client = client_for(bootstrapped["auth"]["organizer"])
    response = client.get(bootstrapped["routes"]["csv_export"])
    assert response.status_code == 200
    first_line = response.content.decode().splitlines()[0]
    assert "," in first_line


def test_judge_cannot_export_csv(bootstrapped):
    client = client_for(bootstrapped["auth"]["judge_a"])
    response = client.get(bootstrapped["routes"]["csv_export"])
    assert response.status_code in (401, 403)
