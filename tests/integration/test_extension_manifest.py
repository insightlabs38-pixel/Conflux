"""PD-F002-B02-T08: extension manifests checked against live registries, listed read-only."""

import pytest
from accounts.models import Session, User
from artifacts.validators import VALIDATORS
from communications.bulk import ACTIONS as BULK_ACTIONS
from core import (
    approvals,
    entities,
    jobs,
    manifest,
    notifications,
    previews,
    rich,
    threads,
    timeline,
    version_diff,
)
from django.core import checks
from django.core.management import call_command
from django.core.management.base import SystemCheckError
from django.test import Client
from presentation.block_types import BLOCK_TYPES
from stages.advancement import REGISTRY as STRATEGIES
from workspaces.models import Membership, Role, Workspace


def codes(problems, severity=None):
    return sorted(p["code"] for p in problems if severity in (None, p["severity"]))


@pytest.fixture
def isolated(monkeypatch):
    """The real capabilities and manifests, copied so a test can add and break things."""
    monkeypatch.setattr(manifest, "MANIFESTS", dict(manifest.MANIFESTS))
    monkeypatch.setattr(manifest, "CAPABILITIES", dict(manifest.CAPABILITIES))
    return manifest


# --- the real deployment ------------------------------------------------------------------------


def test_the_deployments_manifests_agree_with_the_live_registries():
    assert manifest.check() == []
    call_command("check")  # the startup gate: raises on any error


def test_every_live_entry_is_claimed_by_exactly_one_manifest():
    snapshot = manifest.snapshot()
    owners = {}
    for item in snapshot["manifests"]:
        for provided in item["provides"]:
            key = (provided["kind"], provided["id"])
            assert key not in owners, f"{key} is claimed twice"
            owners[key] = item["id"]
            assert provided["state"] in ("live", "declared")  # nothing declared is missing
    live_total = 0
    for capability in snapshot["capabilities"]:
        for entry in capability["entries"]:
            live_total += 1
            assert entry["manifest"] == owners[(capability["kind"], entry["id"])]
    declared = sum(c["declared_only"] for c in snapshot["capabilities"])
    exporters = next(c for c in snapshot["capabilities"] if c["kind"] == "archive_exporter")
    assert [e["id"] for e in exporters["entries"]] == ["config", "final", "full"]  # as declared
    assert declared == 4 and live_total > 50 and snapshot["ok"] is True


def test_the_inventory_reads_the_registries_that_exist_today():
    by_kind = {
        c["kind"]: {e["id"] for e in c["entries"]} for c in manifest.snapshot()["capabilities"]
    }
    assert by_kind["page_block"] == set(BLOCK_TYPES)
    assert by_kind["artifact_validator"] == {str(k) for k in VALIDATORS}
    assert by_kind["advancement_strategy"] == set(STRATEGIES)
    assert by_kind["bulk_action"] == set(BULK_ACTIONS)
    assert by_kind["job_kind"] == set(jobs.KINDS)
    assert by_kind["approval_policy"] == set(approvals.POLICIES)
    assert by_kind["thread_subject"] == set(threads.SUBJECTS)
    assert by_kind["timeline_provider"] == set(timeline.PROVIDERS)
    assert by_kind["entity"] == set(entities.entities())
    assert by_kind["preview_source"] == set(previews.SOURCES)
    assert by_kind["version_source"] == set(version_diff.SOURCES)
    assert by_kind["notification_category"] == set(notifications.CATEGORIES)
    assert by_kind["rich_profile"] == set(rich.PROFILES)


def test_the_six_sdk_families_and_the_archive_formats_are_all_described():
    snapshot = manifest.snapshot()
    kinds = {c["kind"]: c for c in snapshot["capabilities"]}
    # The six families of the internal SDK (docs/architecture/EXTENSION_SDK.md).
    families = {
        "artifact_validator": False,
        "advancement_strategy": False,
        "assignment_strategy": True,
        "page_block": False,
        "archive_converter": True,
        "archive_exporter": True,
        "archive_importer": True,
    }
    assert {k: kinds[k]["declared_only"] for k in families} == families
    ids = {m["id"] for m in snapshot["manifests"]}
    assert {"core", "presentation", "artifacts", "stages", "communications", "integrations",
            "evaluations", "forms", "events", "projects", "eventconfig"} <= ids  # fmt: skip
    for item in snapshot["manifests"]:
        assert item["api_version"] == manifest.API_VERSION and item["version"] and item["label"]
        if item["id"] != "core":
            assert {"kind": "manifest", "id": "core"} in item["requires"]


# --- what the check catches ---------------------------------------------------------------------


def test_each_kind_of_disagreement_is_reported_with_a_code_and_the_manifest(isolated):
    manifest.register_manifest(manifest.Manifest("bad", "1.0.0", "Bad", api_version=99))
    manifest.register_manifest(
        manifest.Manifest(
            "claims", "1.0.0", "Claims",
            provides=(("page_block", "ghost"), ("nope", "x"), ("job_kind", "archive_export")),
            requires=(("page_block", "missing"), ("manifest", "absent"), ("page_block", "hero")),
        )
    )  # fmt: skip
    found = manifest.check()
    by_code = {}
    for item in found:
        by_code.setdefault(item["code"], []).append(item)
    assert set(by_code) == {
        "unsupported_api_version", "not_registered", "unknown_capability",
        "duplicate_claim", "unresolved_requirement",
    }  # fmt: skip
    assert by_code["unsupported_api_version"][0]["manifest"] == "bad"
    assert "99" in by_code["unsupported_api_version"][0]["message"]
    assert "page_block:ghost" in by_code["not_registered"][0]["message"]
    assert "'nope'" in by_code["unknown_capability"][0]["message"]
    assert "integrations" in by_code["duplicate_claim"][0]["message"]
    assert {i["message"] for i in by_code["unresolved_requirement"]} == {
        "Requires 'page_block:missing', which nothing provides.",
        "Requires 'manifest:absent', which nothing provides.",
    }
    assert all(i["severity"] == "error" for i in found)
    assert codes(found).count("unresolved_requirement") == 2  # `page_block:hero` resolves


def test_an_incomplete_manifest_is_reported(isolated):
    manifest.register_manifest(manifest.Manifest("", "", ""))
    assert "incomplete" in codes(manifest.check())


def test_a_registered_entry_nobody_declares_is_a_warning_not_an_error(isolated):
    BLOCK_TYPES["test_unclaimed"] = {"title": "Unclaimed", "schema": {"type": "object"}}
    try:
        found = manifest.check()
        assert [(p["code"], p["severity"]) for p in found] == [("unclaimed", "warning")]
        assert "page_block:test_unclaimed" in found[0]["message"]
        assert manifest.snapshot()["ok"] is True  # warnings do not fail the deployment
        call_command("check")
    finally:
        del BLOCK_TYPES["test_unclaimed"]


def test_a_new_deployment_source_declares_itself_without_touching_the_platform(isolated):
    """An independent source: one registry entry and one manifest, no private coupling."""
    BLOCK_TYPES["acme_banner"] = {"title": "Acme banner", "schema": {"type": "object"}}
    try:
        manifest.register_manifest(
            manifest.Manifest(
                id="acme", version="0.1.0", label="Acme extras",
                provides=(("page_block", "acme_banner"),),
                requires=(("manifest", "presentation"), ("page_block", "hero")),
            )
        )  # fmt: skip
        assert manifest.check() == []
        item = next(m for m in manifest.snapshot()["manifests"] if m["id"] == "acme")
        assert item["provides"] == [
            {"kind": "page_block", "id": "acme_banner", "label": "Acme banner", "state": "live"}
        ]
        entry = next(
            e for c in manifest.snapshot()["capabilities"] if c["kind"] == "page_block"
            for e in c["entries"] if e["id"] == "acme_banner"
        )  # fmt: skip
        assert entry["manifest"] == "acme"
    finally:
        del BLOCK_TYPES["acme_banner"]


def test_registration_is_idempotent_and_never_silently_replaced(isolated):
    same = manifest.Manifest("twice", "1.0.0", "Twice")
    manifest.register_manifest(same)
    manifest.register_manifest(same)
    with pytest.raises(ValueError):
        manifest.register_manifest(manifest.Manifest("twice", "2.0.0", "Twice"))
    capability = manifest.Capability("test_kind", "Test", "A test kind.")
    manifest.register_capability(capability)
    manifest.register_capability(capability)
    with pytest.raises(ValueError):
        manifest.register_capability(manifest.Capability("test_kind", "Other", "x"))


def test_a_declared_only_capability_resolves_requirements_but_cannot_be_verified(isolated):
    manifest.register_capability(manifest.Capability("test_kind", "Test", "A test kind."))
    manifest.register_manifest(manifest.Manifest("t", "1.0.0", "T", provides=(("test_kind", "a"),)))
    manifest.register_manifest(
        manifest.Manifest("u", "1.0.0", "U", requires=(("test_kind", "a"), ("test_kind", "b")))
    )
    problems = manifest.check()
    assert [(p["code"], p["manifest"]) for p in problems] == [("unresolved_requirement", "u")]
    assert "test_kind:b" in problems[0]["message"]


# --- the startup gate ---------------------------------------------------------------------------


def test_the_django_system_check_turns_errors_into_a_startup_failure(isolated):
    manifest.register_manifest(manifest.Manifest("bad", "1.0.0", "Bad", api_version=99))
    from core.checks import extension_manifests

    found = extension_manifests(None)
    assert [type(f) for f in found] == [checks.Error]
    assert found[0].id == "core.manifest.unsupported_api_version" and "[bad]" in found[0].msg
    with pytest.raises(SystemCheckError):
        call_command("check")


def test_unclaimed_entries_surface_as_system_check_warnings(isolated):
    BLOCK_TYPES["test_unclaimed"] = {"title": "Unclaimed", "schema": {"type": "object"}}
    try:
        from core.checks import extension_manifests

        found = extension_manifests(None)
        assert [(type(f), f.id) for f in found] == [(checks.Warning, "core.manifest.unclaimed")]
    finally:
        del BLOCK_TYPES["test_unclaimed"]


# --- the read-only endpoint ---------------------------------------------------------------------


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


@pytest.fixture
def world(db):
    workspace = Workspace.objects.create(name="W", slug="w")
    foreign = Workspace.objects.create(name="F", slug="f")
    people = {}
    for name, role in (("org", Role.ORGANIZER), ("admin", Role.ADMIN), ("par", Role.PARTICIPANT)):
        user = User.objects.create_user(username=name, password="unused")
        Membership.objects.create(user=user, workspace=workspace, role=role)
        people[name] = user
    stranger = User.objects.create_user(username="stranger", password="unused")
    Membership.objects.create(user=stranger, workspace=foreign, role=Role.ORGANIZER)
    people["stranger"] = stranger
    return {"url": f"/api/v1/workspaces/{workspace.public_id}/extensions/", "people": people}


@pytest.mark.parametrize("who", ["org", "admin"])
def test_organizers_and_admins_read_the_inventory(world, who):
    response = client_for(world["people"][who]).get(world["url"])
    assert response.status_code == 200 and response["Cache-Control"] == "private, no-store"
    body = response.json()
    assert body["ok"] is True and body["problems"] == [] and body["api_version"] == 1
    assert body["supported_api_versions"] == [1]
    assert {m["id"] for m in body["manifests"]} >= {"core", "presentation", "communications"}
    blocks = next(c for c in body["capabilities"] if c["kind"] == "page_block")
    assert len(blocks["entries"]) == len(BLOCK_TYPES) and blocks["declared_only"] is False
    hero = next(e for e in blocks["entries"] if e["id"] == "hero")
    assert hero == {"id": "hero", "label": BLOCK_TYPES["hero"]["title"], "manifest": "presentation"}


def test_nobody_else_reads_it_and_nobody_writes_it(world):
    assert client_for(world["people"]["par"]).get(world["url"]).status_code == 403
    assert client_for(world["people"]["stranger"]).get(world["url"]).status_code == 403
    assert Client().get(world["url"]).status_code in (401, 403)
    org = client_for(world["people"]["org"])
    for method in ("post", "put", "patch", "delete"):
        assert getattr(org, method)(world["url"]).status_code == 405


def test_the_endpoint_reports_a_broken_deployment_instead_of_hiding_it(world, isolated):
    manifest.register_manifest(manifest.Manifest("bad", "1.0.0", "Bad", api_version=99))
    body = client_for(world["people"]["org"]).get(world["url"]).json()
    assert body["ok"] is False
    assert [p["code"] for p in body["problems"]] == ["unsupported_api_version"]
    assert body["problems"][0] == {
        "code": "unsupported_api_version", "severity": "error", "manifest": "bad",
        "message": body["problems"][0]["message"],
    }  # fmt: skip
