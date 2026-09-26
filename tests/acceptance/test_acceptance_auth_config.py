"""FX-002: .dogfood.toml's [auth] section must actually authenticate as the
role it claims. The checker never logs in — it just attaches these headers
verbatim — so a header that stops matching a seeded token would fail silently
in `.dogfood.toml` and loudly in every T1/T2 check at once.
"""

import tomllib
from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client
from workspaces.models import Role

pytestmark = pytest.mark.django_db

REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_ROLES = {
    "organizer": Role.ORGANIZER,
    "judge_a": Role.JUDGE,
    "judge_b": Role.JUDGE,
    "participant": Role.PARTICIPANT,
}


def load_auth_config():
    with open(REPO_ROOT / ".dogfood.toml", "rb") as f:
        return tomllib.load(f)["auth"]


def request_with_header(header):
    name, _, value = header.partition(":")
    assert name.strip() == "Cookie", f"only cookie auth is wired up so far: {header!r}"
    cookie_name, _, token = value.strip().partition("=")
    client = Client()
    client.cookies[cookie_name.strip()] = token.strip()
    return client.get("/api/v1/accounts/me/")


def test_dogfood_toml_declares_all_four_acceptance_roles():
    auth = load_auth_config()
    assert set(auth) == set(EXPECTED_ROLES)


@pytest.mark.parametrize("identity", ["organizer", "judge_a", "judge_b", "participant"])
def test_configured_header_authenticates_as_the_expected_role(identity):
    call_command("seed_acceptance_identities")
    auth = load_auth_config()

    response = request_with_header(auth[identity])

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == identity
    roles = {m["role"] for m in body["memberships"] if m["workspace_slug"] == "acceptance"}
    assert EXPECTED_ROLES[identity] in roles
