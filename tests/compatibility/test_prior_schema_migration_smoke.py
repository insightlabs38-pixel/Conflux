"""UPG-005: upgrade smoke test from the prior *released* schema.

The frozen release rehearsal (`demo/release-freeze`, taken 2026-09-27 from the released
offline stack) is the prior released schema. This test restores its PostgreSQL dump into a
scratch database, runs a normal `manage.py migrate` with the current code and asserts that the
upgrade applies the newer migrations cleanly and the known rehearsal records read back.

Needs a PostgreSQL `DATABASE_URL` and a `pg_restore` able to read the dump (local, else the
`postgres:17` image through Docker; override with CONFLUX_PG_RESTORE_IMAGE). Without them the
test skips with the reason, like the other PostgreSQL-only suites.
"""

import hashlib
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from urllib.parse import unquote, urlparse

import pytest

ROOT = Path(__file__).resolve().parents[2]
FREEZE = ROOT / "demo" / "release-freeze"
DUMP = FREEZE / "db.dump"
DUMP_SHA256 = "a711b9fb8650b4373c371f6651de28af934cd5fb4a3b2c44ff8d2ef4be516438"

# Records named in demo/release-freeze/MANIFEST.md.
KNOWN_RECORDS = {
    "events_event": "f73490c0-f2d8-40bd-b058-d0a883fa9243",
    "projects_project": "a68c4383-3153-4e24-b7b5-728bd1638b60",
    "projects_submissionversion": "0620900e-c56e-4259-b550-7549064e94e3",
    "evaluations_ballot": "d90102ce-9591-4eac-a561-7a07401e0b92",
    "awards_award": "7e951ed4-65ed-4371-b98f-c39a38106704",
}


def _pg_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if urlparse(url).scheme not in {"postgres", "postgresql"}:
        pytest.skip("Needs a PostgreSQL DATABASE_URL to restore the prior release dump.")
    return url


def _restore_command(url, dbname: str) -> list[str]:
    target = [
        "-h", url.hostname or "localhost", "-p", str(url.port or 5432),
        "-U", unquote(url.username or "postgres"), "-d", dbname,
        "--no-owner",
    ]  # fmt: skip
    local = shutil.which("pg_restore")
    if local and subprocess.run([local, "-l", str(DUMP)], capture_output=True).returncode == 0:
        return [local, *target]
    docker = shutil.which("docker")
    image = os.environ.get("CONFLUX_PG_RESTORE_IMAGE", "postgres:17")
    if (
        docker
        and subprocess.run([docker, "image", "inspect", image], capture_output=True).returncode == 0
    ):
        return [
            docker, "run", "--rm", "-i", "--network", "host",
            "-e", "PGPASSWORD", image, "pg_restore", *target,
        ]  # fmt: skip
    pytest.skip(
        "No pg_restore that can read the PostgreSQL 17 dump (install matching client tools "
        "or provide the postgres:17 image via Docker)."
    )


def test_release_freeze_fixture_is_the_recorded_prior_release():
    assert hashlib.sha256(DUMP.read_bytes()).hexdigest() == DUMP_SHA256, (
        "demo/release-freeze/db.dump changed; it is the prior-release upgrade fixture. "
        "Re-record it deliberately (MANIFEST.md and this hash) or restore the original."
    )


def test_upgrading_from_the_prior_released_schema_preserves_known_records():
    import psycopg

    base = _pg_url()
    url = urlparse(base)
    scratch = f"conflux_upgrade_smoke_{uuid.uuid4().hex[:10]}"
    admin_dsn = (
        f"host={url.hostname} port={url.port or 5432} user={unquote(url.username or '')} "
        f"password={unquote(url.password or '')} dbname=postgres"
    )
    scratch_url = url._replace(path=f"/{scratch}").geturl()
    env = {**os.environ, "DATABASE_URL": scratch_url, "PGPASSWORD": unquote(url.password or "")}
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute(f'create database "{scratch}"')
    try:
        with DUMP.open("rb") as dump:
            restored = subprocess.run(
                _restore_command(url, scratch),
                stdin=dump, capture_output=True, env=env,
            )  # fmt: skip
        assert restored.returncode == 0, restored.stderr.decode()[-800:]

        scratch_dsn = admin_dsn.replace("dbname=postgres", f"dbname={scratch}")
        with psycopg.connect(scratch_dsn) as conn:
            before = conn.execute("select count(*) from django_migrations").fetchone()[0]

        manage = [sys.executable, str(ROOT / "src/api/manage.py")]
        upgraded = subprocess.run(
            [*manage, "migrate", "--noinput"], capture_output=True, env=env, cwd=ROOT
        )
        assert upgraded.returncode == 0, upgraded.stderr.decode()[-1200:]
        pending = subprocess.run(
            [*manage, "migrate", "--check"], capture_output=True, env=env, cwd=ROOT
        )
        assert pending.returncode == 0, "migrations still pending after upgrade"

        with psycopg.connect(scratch_dsn) as conn:
            after = conn.execute("select count(*) from django_migrations").fetchone()[0]
            assert after > before, (
                "the upgrade applied no migrations; fixture is not a prior schema"
            )
            for table, public_id in KNOWN_RECORDS.items():
                count = conn.execute(
                    f"select count(*) from {table} where public_id = %s", (public_id,)
                ).fetchone()[0]
                assert count == 1, f"{table} {public_id} lost or duplicated by the upgrade"
    finally:
        with psycopg.connect(admin_dsn, autocommit=True) as admin:
            admin.execute(f'drop database if exists "{scratch}" with (force)')
