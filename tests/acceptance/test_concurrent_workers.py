"""FX-005: `import_fixture` deletes and rebuilds every ImportedFixture row
(see its docstring) — a real hazard if two verification workers ever shared
one database, since one worker's re-import would blow away another's rows
mid-test. This pins the actual guarantee that makes `pytest -n auto` safe:
each xdist worker gets a distinctly-named database, so that race can't
happen across workers, and pytest-django's per-test transaction rollback
means it can't happen within a worker either.
"""

from django.db import connection
from integrations.models import ImportedFixture


def test_test_database_is_isolated_per_xdist_worker(imported_fixture, worker_id):
    if worker_id == "master":
        # Not running under xdist (e.g. plain `pytest`, no `-n`): a single
        # worker is trivially "isolated" from workers that don't exist.
        return
    if connection.vendor == "sqlite":
        # An in-memory sqlite database isn't visible outside the process
        # that created it, and each xdist worker is its own process — the
        # isolation holds even though pytest-django can't give each one a
        # distinctly-named file to assert on here.
        return
    db_name = connection.settings_dict["NAME"]
    assert str(db_name).endswith(worker_id), (
        f"expected the per-worker test database name to end with {worker_id!r}, got {db_name!r}"
    )


def test_reimport_in_one_test_does_not_affect_a_fresh_test(imported_fixture):
    # If a prior test in this same worker process leaked its fixture import
    # (no per-test transaction rollback, or a non-transactional import),
    # this fixture would already see a row here before it imports its own.
    assert ImportedFixture.objects.count() == 1
