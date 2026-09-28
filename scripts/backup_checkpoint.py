#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import subprocess
import tarfile
import tempfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SERVICES = ("app", "worker", "beat", "objectstore")
FILES = ("db.dump", "objectstore.tar.gz")
COUNTS_SQL = """
CREATE FUNCTION pg_temp.checkpoint_counts() RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE r record; n bigint; counts jsonb := '{}'::jsonb;
BEGIN
  FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename LOOP
    EXECUTE format('SELECT count(*) FROM public.%I', r.tablename) INTO n;
    counts := counts || jsonb_build_object(r.tablename, n);
  END LOOP;
  RETURN counts;
END $$;
SELECT pg_temp.checkpoint_counts();
"""


def run(args, *, output=None, source=None):
    return subprocess.run(
        args, cwd=ROOT, check=True, stdout=output or subprocess.PIPE, stdin=source
    ).stdout


def compose(*args, **kwargs):
    return run(["docker", "compose", *args], **kwargs)


def database_args(command):
    return [
        "exec",
        "-T",
        "db",
        command,
        "-U",
        os.environ.get("POSTGRES_USER", "conflux"),
        "-d",
        os.environ.get("POSTGRES_DB", "conflux"),
    ]


def query(sql):
    return (
        compose(*database_args("psql"), "-X", "-qAt", "-v", "ON_ERROR_STOP=1", "-c", sql)
        .decode()
        .strip()
    )


def digest_file(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def object_inventory(path):
    entries = {}
    with tarfile.open(path, "r|*") as archive:
        for member in archive:
            name = PurePosixPath(member.name)
            if name.is_absolute() or ".." in name.parts:
                raise ValueError("Unsafe object archive path")
            normalized = str(name)
            if normalized in entries:
                raise ValueError("Duplicate object archive entry")
            if member.isdir():
                entries[normalized] = {"kind": "directory", "mode": member.mode}
            elif member.isfile() and normalized != ".":
                with archive.extractfile(member) as stream:
                    digest = hashlib.file_digest(stream, "sha256").hexdigest()
                entries[normalized] = {
                    "kind": "file",
                    "size": member.size,
                    "sha256": digest,
                    "mode": member.mode,
                }
            else:
                raise ValueError("Object archive contains unsupported links or special files")
    serialized = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
    return {"entries": len(entries), "sha256": hashlib.sha256(serialized).hexdigest()}


def image_id(service):
    container = compose("ps", "-aq", service).decode().strip()
    if not container or "\n" in container:
        raise ValueError(f"Expected exactly one {service} container")
    return container, run(
        ["docker", "inspect", "--format", "{{.Image}}", container]
    ).decode().strip()


def volume_archive(container, path):
    with path.open("wb") as output:
        run(
            [
                "docker",
                "run",
                "--rm",
                "--entrypoint",
                "tar",
                "--volumes-from",
                container,
                "conflux-api:latest",
                "czf",
                "-",
                "-C",
                "/data",
                ".",
            ],
            output=output,
        )


def running_services():
    active = compose("ps", "--status", "running", "--services").decode().splitlines()
    if "db" not in active:
        raise ValueError("Database must be running")
    return [service for service in SERVICES if service in active]


def timestamp():
    return datetime.now(UTC).isoformat()


def create(destination):
    destination = Path(destination).absolute()
    destination.mkdir(parents=True, exist_ok=False)
    active = running_services()
    if "objectstore" not in active:
        raise ValueError("Objectstore must be running for checkpoint creation")
    container, storage_image = image_id("objectstore")
    started = timestamp()
    try:
        compose("stop", *active)
        counts = json.loads(query(COUNTS_SQL))
        version = query("SHOW server_version_num")
        with (destination / "db.dump").open("wb") as output:
            compose(*database_args("pg_dump"), "--format=custom", output=output)
        volume_archive(container, destination / "objectstore.tar.gz")
        manifest = {
            "format_version": 1,
            "started_at": started,
            "completed_at": timestamp(),
            "git_revision": run(["git", "rev-parse", "HEAD"]).decode().strip(),
            "postgres_version_num": version,
            "objectstore_image": storage_image,
            "table_counts": counts,
            "object_inventory": object_inventory(destination / "objectstore.tar.gz"),
            "files": {
                name: {
                    "bytes": (destination / name).stat().st_size,
                    "sha256": digest_file(destination / name),
                }
                for name in FILES
            },
        }
        temporary = destination / "manifest.partial"
        temporary.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        temporary.rename(destination / "manifest.json")
        verify(destination)
        return manifest
    finally:
        compose("start", *active)


def valid_digest(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def verify(source):
    source = Path(source)
    manifest_path = source / "manifest.json"
    if manifest_path.is_symlink() or manifest_path.stat().st_size > 1024 * 1024:
        raise ValueError("Invalid manifest file")
    manifest = json.loads(manifest_path.read_text())
    if (
        not isinstance(manifest, dict)
        or type(manifest.get("format_version")) is not int
        or manifest["format_version"] != 1
    ):
        raise ValueError("Unsupported checkpoint format")
    started = datetime.fromisoformat(manifest["started_at"])
    completed = datetime.fromisoformat(manifest["completed_at"])
    if started.tzinfo is None or completed.tzinfo is None or completed < started:
        raise ValueError("Invalid checkpoint time interval")
    if not re.fullmatch(r"[0-9a-f]{40,64}", manifest["git_revision"]):
        raise ValueError("Invalid Git revision")
    if not re.fullmatch(r"[0-9]{6}", manifest["postgres_version_num"]):
        raise ValueError("Invalid PostgreSQL version")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", manifest["objectstore_image"]):
        raise ValueError("Invalid objectstore image")
    counts = manifest["table_counts"]
    if (
        not isinstance(counts, dict)
        or not counts
        or any(
            not re.fullmatch(r"[a-zA-Z_][a-zA-Z_0-9]*", key) or type(value) is not int or value < 0
            for key, value in counts.items()
        )
    ):
        raise ValueError("Invalid table counts")
    files = manifest["files"]
    if not isinstance(files, dict) or set(files) != set(FILES):
        raise ValueError("Checkpoint must contain both authoritative stores")
    for name in FILES:
        path = source / name
        info = files[name]
        if (
            path.is_symlink()
            or not path.is_file()
            or type(info["bytes"]) is not int
            or info["bytes"] <= 0
        ):
            raise ValueError(f"Invalid checkpoint file: {name}")
        if (
            not valid_digest(info["sha256"])
            or path.stat().st_size != info["bytes"]
            or digest_file(path) != info["sha256"]
        ):
            raise ValueError(f"Checksum or size mismatch: {name}")
    with (source / "db.dump").open("rb") as dump:
        if dump.read(5) != b"PGDMP":
            raise ValueError("Expected PostgreSQL custom dump")
    if object_inventory(source / "objectstore.tar.gz") != manifest["object_inventory"]:
        raise ValueError("Object inventory mismatch")
    return manifest


def restore(source):
    source = Path(source).absolute()
    manifest = verify(source)
    active = running_services()
    container, storage_image = image_id("objectstore")
    if storage_image != manifest["objectstore_image"]:
        raise ValueError("Raw volume restore requires the same objectstore image digest")
    if (
        int(query("SHOW server_version_num")) // 10000
        != int(manifest["postgres_version_num"]) // 10000
    ):
        raise ValueError("Restore requires the same PostgreSQL major version")
    with (source / "db.dump").open("rb") as dump:
        compose("exec", "-T", "db", "pg_restore", "--list", source=dump)
    if active:
        compose("stop", *active)
    # Failed restore stays quiesced; restarting would expose unverified state.
    with (source / "db.dump").open("rb") as dump:
        compose(
            *database_args("pg_restore"),
            "--exit-on-error",
            "--single-transaction",
            "--clean",
            "--if-exists",
            "--no-owner",
            source=dump,
        )
    with (source / "objectstore.tar.gz").open("rb") as archive:
        run(
            [
                "docker",
                "run",
                "--rm",
                "-i",
                "--entrypoint",
                "sh",
                "--volumes-from",
                container,
                "conflux-api:latest",
                "-c",
                "find /data -mindepth 1 -delete && tar xzf - -C /data",
            ],
            source=archive,
        )
    if json.loads(query(COUNTS_SQL)) != manifest["table_counts"]:
        raise ValueError("Restored database table counts differ; services remain stopped")
    with tempfile.TemporaryDirectory(prefix="conflux-restore-") as temporary:
        restored_archive = Path(temporary) / "objects.tar.gz"
        volume_archive(container, restored_archive)
        if object_inventory(restored_archive) != manifest["object_inventory"]:
            raise ValueError("Restored object inventory differs; services remain stopped")
    if active:
        compose("start", *active)
    return {
        "verified": True,
        "checkpoint_completed_at": manifest["completed_at"],
        "restored_at": timestamp(),
        "table_counts": manifest["table_counts"],
        "object_inventory": manifest["object_inventory"],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Create, verify or restore a quiesced Conflux backup checkpoint"
    )
    parser.add_argument("action", choices=("create", "verify", "restore"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        result = {"create": create, "verify": verify, "restore": restore}[args.action](
            args.directory
        )
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        tarfile.TarError,
        subprocess.CalledProcessError,
    ) as exc:
        parser.exit(1, f"Checkpoint {args.action} failed: {exc}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
