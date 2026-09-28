import importlib.util
import io
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "backup_checkpoint", Path(__file__).resolve().parents[2] / "scripts/backup_checkpoint.py"
)
checkpoint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checkpoint)


def archive(path, *, name="artifacts/file", kind=tarfile.REGTYPE, payload=b"real artifact"):
    with tarfile.open(path, "w:gz") as output:
        root = tarfile.TarInfo(".")
        root.type = tarfile.DIRTYPE
        root.mode = 0o755
        output.addfile(root)
        member = tarfile.TarInfo(name)
        member.type = kind
        member.mode = 0o644
        member.size = len(payload) if kind == tarfile.REGTYPE else 0
        output.addfile(member, io.BytesIO(payload) if member.size else None)


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    volume = tmp_path / "live.tar.gz"
    archive(volume)
    calls = []
    state = {"counts": {"django_migrations": 12, "artifacts_artifact": 1}, "version": "170005"}

    def compose(*args, output=None, source=None):
        calls.append(args)
        if "pg_dump" in args:
            output.write(b"PGDMPsynthetic dump")
        if "pg_restore" in args:
            assert source.read().startswith(b"PGDMP")
        return b""

    def run(args, **kwargs):
        calls.append(tuple(args))
        if args[0] == "git":
            return b"a" * 40
        assert kwargs["source"].read()
        return b""

    monkeypatch.setattr(checkpoint, "running_services", lambda: ["app", "objectstore"])
    monkeypatch.setattr(checkpoint, "image_id", lambda service: ("container", "sha256:" + "b" * 64))
    monkeypatch.setattr(checkpoint, "compose", compose)
    monkeypatch.setattr(checkpoint, "run", run)
    monkeypatch.setattr(
        checkpoint, "volume_archive", lambda container, path: shutil.copyfile(volume, path)
    )
    monkeypatch.setattr(
        checkpoint,
        "query",
        lambda sql: state["version"] if "SHOW" in sql else json.dumps(state["counts"]),
    )
    return tmp_path / "checkpoint", calls, state, volume


def test_create_verify_restore_records_and_checks_both_stores(runtime):
    destination, calls, state, _ = runtime
    created = checkpoint.create(destination)
    assert checkpoint.verify(destination) == created
    assert created["table_counts"] == state["counts"]
    assert created["object_inventory"]["entries"] == 2
    assert calls[0] == ("stop", "app", "objectstore")
    assert calls[-1] == ("start", "app", "objectstore")
    calls.clear()
    restored = checkpoint.restore(destination)
    assert restored["verified"]
    assert restored["checkpoint_completed_at"] == created["completed_at"]
    restore_call = next(args for args in calls if "--clean" in args)
    assert "--single-transaction" in restore_call and "--exit-on-error" in restore_call
    assert "--list" in calls[0]
    assert calls[-1] == ("start", "app", "objectstore")


@pytest.mark.parametrize("filename", checkpoint.FILES)
def test_corruption_fails_before_any_runtime_action(runtime, filename):
    destination, calls, _, _ = runtime
    checkpoint.create(destination)
    calls.clear()
    with (destination / filename).open("ab") as output:
        output.write(b"corruption")
    with pytest.raises(ValueError, match="mismatch"):
        checkpoint.restore(destination)
    assert calls == []


def test_missing_manifest_or_file_never_stops_runtime(runtime):
    destination, calls, _, _ = runtime
    checkpoint.create(destination)
    calls.clear()
    (destination / "manifest.json").unlink()
    with pytest.raises(FileNotFoundError):
        checkpoint.restore(destination)
    assert calls == []


@pytest.mark.parametrize("change", ["format", "inventory", "counts", "timestamp", "files"])
def test_manifest_rejects_invalid_contract(runtime, change):
    destination, calls, _, _ = runtime
    checkpoint.create(destination)
    path = destination / "manifest.json"
    manifest = json.loads(path.read_text())
    if change == "format":
        manifest["format_version"] = True
    elif change == "inventory":
        manifest["object_inventory"]["sha256"] = "0" * 64
    elif change == "counts":
        manifest["table_counts"]["artifacts_artifact"] = True
    elif change == "timestamp":
        manifest["completed_at"] = "2000-01-01T00:00:00"
    else:
        manifest["files"]["../surprise"] = manifest["files"]["db.dump"]
    path.write_text(json.dumps(manifest))
    calls.clear()
    with pytest.raises(ValueError):
        checkpoint.restore(destination)
    assert calls == []


@pytest.mark.parametrize(
    "name,kind",
    [
        ("../escape", tarfile.REGTYPE),
        ("/absolute", tarfile.REGTYPE),
        ("link", tarfile.SYMTYPE),
        ("hardlink", tarfile.LNKTYPE),
        ("device", tarfile.CHRTYPE),
    ],
)
def test_unsafe_archive_is_rejected(tmp_path, name, kind):
    path = tmp_path / "objects.tar.gz"
    archive(path, name=name, kind=kind)
    with pytest.raises(ValueError):
        checkpoint.object_inventory(path)


def test_duplicate_archive_member_is_rejected(tmp_path):
    path = tmp_path / "duplicate.tar.gz"
    with tarfile.open(path, "w:gz") as output:
        output.addfile(tarfile.TarInfo("a"), io.BytesIO(b""))
        output.addfile(tarfile.TarInfo("./a"), io.BytesIO(b""))
    with pytest.raises(ValueError, match="Duplicate"):
        checkpoint.object_inventory(path)


def test_checkpoint_does_not_overwrite_existing_destination(runtime):
    destination, calls, _, _ = runtime
    checkpoint.create(destination)
    calls.clear()
    with pytest.raises(FileExistsError):
        checkpoint.create(destination)
    assert calls == []


def test_failed_backup_resumes_only_originally_running_services(runtime, monkeypatch):
    destination, calls, _, _ = runtime

    def fail(sql):
        raise subprocess.CalledProcessError(1, ["psql"])

    monkeypatch.setattr(checkpoint, "query", fail)
    with pytest.raises(subprocess.CalledProcessError):
        checkpoint.create(destination)
    assert calls == [("stop", "app", "objectstore"), ("start", "app", "objectstore")]
    assert not (destination / "manifest.json").exists()


@pytest.mark.parametrize("mismatch", ["database", "objects", "postgres", "image"])
def test_restore_mismatch_fails_closed(runtime, monkeypatch, mismatch):
    destination, calls, state, volume = runtime
    checkpoint.create(destination)
    calls.clear()
    if mismatch == "database":
        state["counts"]["artifacts_artifact"] = 0
    elif mismatch == "objects":
        archive(volume, payload=b"wrong restored bytes")
    elif mismatch == "postgres":
        state["version"] = "180001"
    else:
        monkeypatch.setattr(
            checkpoint, "image_id", lambda service: ("container", "sha256:" + "c" * 64)
        )
    with pytest.raises(ValueError):
        checkpoint.restore(destination)
    assert not any(args[0] == "start" for args in calls)
    if mismatch in {"postgres", "image"}:
        assert not any(args[0] == "stop" for args in calls)


def test_database_restore_failure_never_restarts_application(runtime, monkeypatch):
    destination, calls, _, _ = runtime
    checkpoint.create(destination)
    original = checkpoint.compose

    def fail_restore(*args, **kwargs):
        if "--clean" in args:
            raise subprocess.CalledProcessError(1, ["pg_restore"])
        return original(*args, **kwargs)

    monkeypatch.setattr(checkpoint, "compose", fail_restore)
    calls.clear()
    with pytest.raises(subprocess.CalledProcessError):
        checkpoint.restore(destination)
    assert calls[-1] == ("stop", "app", "objectstore")


def test_restore_can_retry_while_all_application_services_remain_stopped(runtime, monkeypatch):
    destination, calls, _, _ = runtime
    checkpoint.create(destination)
    monkeypatch.setattr(checkpoint, "running_services", lambda: [])
    calls.clear()
    assert checkpoint.restore(destination)["verified"]
    assert not any(args[0] in {"start", "stop"} for args in calls)
