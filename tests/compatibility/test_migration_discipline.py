"""UPG-003: the application must always start up via a normal, additive
`manage.py migrate` -- never a destructive shortcut (flush, fake, a manual
drop) -- and the migration graph itself must never carry an unmerged
branch a plain `migrate` could apply in an ambiguous order.
"""

from pathlib import Path

from django.db.migrations.loader import MigrationLoader

DOCKERFILE = Path(__file__).resolve().parents[2] / "infra" / "api.Dockerfile"
FORBIDDEN_STARTUP_COMMANDS = (
    "flush",
    "sqlflush",
    "--fake",
    "reset_db",
    "dropdb",
    "drop database",
    "drop schema",
    "truncate",
)


def test_startup_entrypoint_migrates_normally_with_no_destructive_hacks():
    content = DOCKERFILE.read_text()
    assert "manage.py migrate" in content
    lowered = content.lower()
    for command in FORBIDDEN_STARTUP_COMMANDS:
        assert command not in lowered, f"Destructive startup command found: {command!r}"


def test_every_app_migration_graph_has_a_single_leaf():
    loader = MigrationLoader(connection=None, ignore_no_migrations=True)
    leaves_by_app: dict[str, list[str]] = {}
    for app_label, name in loader.graph.leaf_nodes():
        leaves_by_app.setdefault(app_label, []).append(name)
    conflicts = {app: names for app, names in leaves_by_app.items() if len(names) > 1}
    assert not conflicts, f"Unmerged migration branches found: {conflicts}"
