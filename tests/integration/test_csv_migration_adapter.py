import json
import subprocess
import sys
from pathlib import Path

import pytest
from accounts.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from events.models import Event, Track
from integrations.archive import build_archive, import_archive
from projects.models import Project
from workspaces.models import Workspace

from scripts.convert_project_csv import ConversionError, convert

pytestmark = pytest.mark.django_db
ROOT = Path(__file__).resolve().parents[2]


def setup_case():
    actor = User.objects.create_user(username="existing-owner", password="unused")
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="Source", slug="source")
    Track.objects.create(event=event, name="Hardware")
    return actor, workspace, build_archive(event, mode="config")


def test_generic_csv_adapts_to_canonical_import_without_inventing_users():
    actor, workspace, config = setup_case()
    mapping = {
        "external_id": "submission_id",
        "name": "project_title",
        "description": "tagline",
        "track": "category",
        "created_by_username": "owner_username",
    }
    csv_text = (
        "submission_id,project_title,tagline,category,owner_username\n"
        "d-1,Device,Accessible hardware,Hardware,existing-owner\n"
        "d-2,Open project,No track,,existing-owner\n"
    )
    full = convert(config, csv_text, mapping)
    assert config["mode"] == "config"
    assert "projects" not in config
    assert full["mode"] == "full"
    assert len(full["projects"]) == 2
    assert full["projects"][0]["track_ref"] == config["tracks"][0]["ref"]
    assert convert(config, csv_text, mapping) == full
    with transaction.atomic():
        imported = import_archive(
            workspace=workspace, archive=full, name="Imported", slug="imported"
        )
    assert imported.is_public is False
    assert list(
        Project.objects.filter(event=imported).order_by("name").values_list("name", flat=True)
    ) == [
        "Device",
        "Open project",
    ]
    assert Project.objects.get(event=imported, name="Device").created_by == actor


def test_csv_rejects_ambiguous_rows_and_unknown_tracks():
    _, _, config = setup_case()
    mapping = {
        "external_id": "id",
        "name": "title",
        "created_by_username": "owner",
        "track": "track",
    }
    with pytest.raises(ConversionError, match="unknown track"):
        convert(config, "id,title,owner,track\n1,A,existing-owner,Wrong\n", mapping)
    with pytest.raises(ConversionError, match="repeats external ID"):
        convert(config, "id,title,owner,track\n1,A,existing-owner,\n1,B,existing-owner,\n", mapping)
    with pytest.raises(ConversionError, match="wrong number of fields"):
        convert(config, "id,title,owner,track\n1,A,existing-owner\n", mapping)
    with pytest.raises(ConversionError, match="config archive"):
        convert({**config, "mode": "full"}, "id,title,owner,track\n1,A,existing-owner,\n", mapping)


def test_import_fails_closed_for_unknown_creator_and_leaves_no_event():
    _, workspace, config = setup_case()
    full = convert(
        config,
        "title,owner\nExternal,missing-user\n",
        {"name": "title", "created_by_username": "owner"},
    )
    with pytest.raises(ValidationError, match="does not exist"):
        with transaction.atomic():
            import_archive(workspace=workspace, archive=full, name="Imported", slug="imported")
    assert not Event.objects.filter(workspace=workspace, slug="imported").exists()


def test_cli_never_overwrites_output_and_errors_leave_no_file(tmp_path):
    _, _, config = setup_case()
    archive_path = tmp_path / "config.json"
    archive_path.write_text(json.dumps(config))
    csv_path = tmp_path / "projects.csv"
    csv_path.write_text("title,owner\nExternal,existing-owner\n")
    mapping_path = tmp_path / "mapping.json"
    mapping_path.write_text(json.dumps({"name": "title", "created_by_username": "owner"}))
    output_path = tmp_path / "full.json"
    command = [
        sys.executable,
        str(ROOT / "scripts/convert_project_csv.py"),
        "--archive",
        str(archive_path),
        "--csv",
        str(csv_path),
        "--mapping",
        str(mapping_path),
        "--output",
        str(output_path),
    ]
    assert subprocess.run(command, capture_output=True).returncode == 0
    original = output_path.read_bytes()
    assert subprocess.run(command, capture_output=True).returncode != 0
    assert output_path.read_bytes() == original
    csv_path.write_text("title,owner\nExternal,existing-owner,extra\n")
    other = tmp_path / "invalid.json"
    command[-1] = str(other)
    assert subprocess.run(command, capture_output=True).returncode != 0
    assert not other.exists()
