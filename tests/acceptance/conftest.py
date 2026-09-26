"""FX-005: shared fixture-bootstrap helpers for the acceptance test suite.

Each fixture is function-scoped, matching pytest-django's per-test
transaction rollback: safe under `pytest -n auto`, where every xdist worker
already gets its own isolated database (see test_concurrent_workers.py),
and safe within a single worker, where each test's DB state disappears at
teardown regardless of `import_fixture`'s own destructive-rebuild import.
"""

import tomllib
from pathlib import Path

import pytest
from django.core.management import call_command

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def imported_fixture(db):
    call_command("import_fixture", "fixtures/fixtures.json")


@pytest.fixture
def acceptance_bootstrap(imported_fixture):
    call_command("seed_acceptance_identities")
    call_command("link_judge_identities")


@pytest.fixture
def dogfood_config():
    with open(REPO_ROOT / ".dogfood.toml", "rb") as f:
        return tomllib.load(f)
