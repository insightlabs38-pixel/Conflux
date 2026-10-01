"""PD-F002-B02-T03: safe previews of files and links through one pipeline and two sources."""

import io
import zipfile

import pytest
from accounts.models import Session, User
from artifacts.inspector import inspect_bytes
from artifacts.models import Artifact, ArtifactInspection
from audit.models import AuditEvent
from core import previews
from core.models import JobArtifact
from django.test import Client
from events.models import Event
from test_artifact_inspector import FakeStorage, artifact, base, png, world
from test_sponsor_portal import client_for
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def subject_for(data, name="file", kind="file", **extra):
    report = inspect_bytes(data, filename=name, kind=kind)
    return previews.Subject(name=name, size=len(data), inspection=report.as_dict(), **extra)


def build(data, name="file", **extra):
    return previews.descriptor("test", {}, subject_for(data, name, **extra))


# --- the pure pipeline, on what the real inspector reports ----------------------------------


def test_text_and_data_show_a_bounded_redacted_excerpt():
    secret = b"token = AKIAABCDEFGHIJKLMNOP\n" + b"line\n" * 2000
    shown = build(secret, "notes.txt")
    assert shown["kind"] == "text" and shown["state"] == "ready"
    assert "AKIAABCDEFGHIJKLMNOP" not in shown["text"] and "[redacted]" in shown["text"]
    assert len(shown["text"]) <= previews.MAX_TEXT
    assert any(
        f["code"] == "possible_secret" and f["level"] == "warning" for f in shown["findings"]
    )
    assert build(b"a,b\n1,2\n", "results.csv")["kind"] == "data"
    assert build(b"{}", "x.json")["kind"] == "data"
    assert build(b"a,b\n", "x", kind_hint="dataset")["kind"] == "data"


def test_images_video_and_documents_carry_facts_and_the_existing_download():
    shown = build(png(640, 480), "shot.png", download_url="https://store/shot")
    assert shown["kind"] == "image" and shown["facts"]["width"] == 640
    assert shown["media"] == {"url": "https://store/shot", "filename": "shot.png"}
    assert shown["text"] == "" and shown["entries"] == []
    video = build(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 16, "demo.mp4")
    assert video["kind"] == "video" and video["media"] is None
    pdf = build(b"%PDF-1.4 /Type /Page /JavaScript", "paper.pdf")
    assert pdf["kind"] == "document" and pdf["facts"]["pages"] == 1
    assert [f["code"] for f in pdf["findings"]] == ["pdf_active_content"]


def test_an_archive_lists_its_entries_up_to_the_cap():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for index in range(80):
            archive.writestr(f"src/file{index}.py", "x = 1\n")
    shown = build(buffer.getvalue(), "code.zip")
    assert shown["kind"] == "archive" and shown["entries_total"] == 80
    assert len(shown["entries"]) == previews.MAX_ENTRIES
    assert shown["entries"][0] == {"name": "src/file0.py", "size": 6}
    assert "listing" not in shown["facts"] and shown["facts"]["entries"] == 80


@pytest.mark.parametrize(
    "data, name",
    [
        (b"<html><script>alert(1)</script>", "page.pdf"),
        (b"<svg onload='x'/>", "logo.svg"),
        (b"\x7fELF\x02\x01\x01", "tool"),
        (b"MZ\x90\x00", "setup.exe"),
    ],
)
def test_content_that_can_run_is_withheld_with_a_reason_and_no_download(data, name):
    shown = build(data, name, download_url="https://store/x")
    assert shown["kind"] == "unavailable" and shown["state"] == "unavailable"
    assert shown["media"] is None and shown["text"] == "" and shown["entries"] == []
    assert shown["reason"]["message"].startswith("Withheld from preview: ")
    assert shown["reason"]["code"] in {"active_content", "executable"}


def test_a_failed_checksum_is_withheld_too():
    report = inspect_bytes(b"data", expected_sha256="0" * 64).as_dict()
    shown = previews.descriptor("t", {}, previews.Subject(name="d", inspection=report))
    assert shown["state"] == "unavailable" and shown["reason"]["code"] == "digest_mismatch"


def test_an_unrecognised_file_has_no_preview_but_can_be_downloaded():
    shown = build(b"\xff\xfe\x00\x01\x02", "blob.bin", download_url="https://store/blob")
    assert shown["state"] == "unavailable" and shown["reason"]["code"] == "no_preview"
    assert shown["media"]["url"] == "https://store/blob"


def test_a_source_can_refuse_and_an_uninspected_thing_is_pending():
    gone = previews.descriptor(
        "t", {}, previews.Subject(name="a", unavailable=("purged", "Purged by policy."))
    )
    assert gone["state"] == "unavailable" and gone["reason"]["code"] == "purged"
    assert gone["media"] is None
    pending = previews.descriptor("t", {}, previews.Subject(name="a", size=3))
    assert pending["state"] == "pending" and pending["reason"]["code"] == "not_inspected"
    waiting_link = previews.descriptor(
        "t", {}, previews.Subject(name="Demo", external_url="https://demo.example/")
    )
    assert waiting_link["kind"] == "link" and waiting_link["link"] == "https://demo.example/"


def test_links_are_shown_only_on_the_web():
    inspection = {
        "verdict": "clean",
        "detected_type": "",
        "subject": "link",
        "facts": {"status": 200},
    }
    web = previews.descriptor(
        "t",
        {},
        previews.Subject(name="Demo", external_url="https://x.example/", inspection=inspection),
    )
    assert web["kind"] == "link" and web["state"] == "ready" and web["facts"] == {"status": 200}
    odd = previews.descriptor(
        "t",
        {},
        previews.Subject(name="Demo", external_url="javascript:alert(1)", inspection=inspection),
    )
    assert odd["state"] == "unavailable" and odd["link"] is None
    assert odd["reason"]["code"] == "unsafe_link"


def test_everything_in_a_descriptor_is_bounded_scalar_text():
    inspection = {
        "verdict": "warnings",
        "detected_type": "text",
        "findings": [
            {"severity": "warning", "code": f"c{i}", "detail": "d" * 900} for i in range(40)
        ],
        "facts": {
            "nested": {"a": [1, 2]},
            "long": "x" * 1000,
            "ctl": "a\x00b\x1b[31m",
            "ok": 3,
            **{f"k{i}": i for i in range(60)},
        },
        "preview": "p" * 9000,
    }
    shown = previews.descriptor("t", {}, previews.Subject(name="n" * 500, inspection=inspection))
    assert len(shown["findings"]) == previews.MAX_FINDINGS and shown["findings_total"] == 40
    assert all(len(f["message"]) <= 500 for f in shown["findings"])
    assert len(shown["facts"]) == previews.MAX_FACTS and shown["facts"]["ok"] == 3
    assert shown["facts"]["nested"] == '{"a": [1, 2]}'
    assert len(shown["facts"]["long"]) == previews.MAX_FACT_TEXT
    assert "\x00" not in shown["facts"]["ctl"] and "\x1b" not in shown["facts"]["ctl"]
    assert len(shown["text"]) == previews.MAX_TEXT and len(shown["name"]) == 200


def test_a_finding_without_a_known_level_is_only_information():
    inspection = {
        "verdict": "clean",
        "detected_type": "text",
        "findings": [{"severity": "wild", "code": "x"}],
    }
    shown = previews.descriptor("t", {}, previews.Subject(name="n", inspection=inspection))
    assert shown["findings"] == [{"level": "info", "code": "x", "message": "x"}]


def test_the_same_subject_always_gives_the_same_descriptor():
    data = b"hello\nworld\n"
    assert build(data, "a.txt") == build(data, "a.txt")


# --- a project artifact: the same eyes as the reviewer endpoints ----------------------------


def previews_url(workspace, source, **query):
    from urllib.parse import urlencode

    return f"/api/v1/workspaces/{workspace.public_id}/previews/{source}/?{urlencode(query)}"


def artifact_url(event, project, row):
    return previews_url(
        event.workspace,
        "project_artifact",
        event=event.public_id,
        project=project.public_id,
        artifact=row.public_id,
    )


@pytest.fixture
def storage(monkeypatch):
    fake = FakeStorage({})
    monkeypatch.setattr("artifacts.services.S3Storage", lambda: fake)
    monkeypatch.setattr("artifacts.previews.S3Storage", lambda: fake)
    return fake


def test_a_project_artifact_is_pending_until_inspected_then_ready(storage):
    event, project, users = world(201)
    body = b"%PDF-1.4 /Type /Page"
    row = artifact(project, users["part"], key="k/doc", body=body)
    storage.objects["k/doc"] = body
    org = client_for(users["org"])
    pending = org.get(artifact_url(event, project, row)).json()
    assert pending["state"] == "pending" and pending["reason"]["code"] == "not_inspected"
    assert pending["media"]["url"].startswith("https://storage.test/k/doc")
    assert (
        org.post(base(event, project) + f"artifacts/{row.public_id}/inspection/").status_code == 200
    )
    ready = org.get(artifact_url(event, project, row)).json()
    assert ready["kind"] == "document" and ready["state"] == "ready"
    assert ready["facts"]["pages"] == 1 and ready["inspected_at"]
    assert ready["source"] == "project_artifact" and ready["ref"]["artifact"] == str(row.public_id)


def test_a_preview_never_inspects_stores_audits_or_fetches(storage, monkeypatch):
    event, project, users = world(202)
    row = artifact(project, users["part"], key="k/doc")
    link = Artifact.objects.create(
        project=project, kind="live_url", visibility="public", title="Demo",
        external_url="https://demo.example/", status="ready", created_by=users["part"],
    )  # fmt: skip
    monkeypatch.setattr(
        "artifacts.url_inspector.pinned_fetch", lambda *a, **k: pytest.fail("fetched a link")
    )
    org = client_for(users["org"])
    audits, inspections, reads = (
        AuditEvent.objects.count(),
        ArtifactInspection.objects.count(),
        storage.reads,
    )
    for item in (row, link):
        response = org.get(artifact_url(event, project, item))
        assert response.status_code == 200 and response["Cache-Control"] == "private, no-store"
        assert response.json()["state"] == "pending"
    assert AuditEvent.objects.count() == audits
    assert ArtifactInspection.objects.count() == inspections and storage.reads == reads


def test_who_may_preview_follows_the_reviewer_rules(storage):
    event, project, users = world(203)
    body = b"%PDF-1.4 /Type /Page"
    judge_row = artifact(project, users["part"], visibility="judge", key="k/j", body=body)
    org_row = artifact(project, users["part"], visibility="organizer", key="k/o", body=body)
    judge, org = client_for(users["judge"]), client_for(users["org"])
    member, other = client_for(users["part"]), client_for(users["other"])
    assert judge.get(artifact_url(event, project, judge_row)).status_code == 200
    assert judge.get(artifact_url(event, project, org_row)).status_code == 404
    assert org.get(artifact_url(event, project, org_row)).status_code == 200
    assert member.get(artifact_url(event, project, org_row)).status_code == 200
    assert other.get(artifact_url(event, project, judge_row)).status_code == 404
    assert Client().get(artifact_url(event, project, judge_row)).status_code in (401, 403)
    stranger = User.objects.create_user(username="stranger", password="unused")
    foreign = Workspace.objects.create(name="F", slug="f")
    Membership.objects.create(user=stranger, workspace=foreign, role=Role.ORGANIZER)
    assert client_for(stranger).get(artifact_url(event, project, judge_row)).status_code == 403


def test_blocked_and_purged_artifacts_get_no_download(storage):
    event, project, users = world(204)
    bad = b"<html><script>alert(1)</script>"
    row = artifact(project, users["part"], key="k/bad", body=bad)
    storage.objects["k/bad"] = bad
    org = client_for(users["org"])
    org.post(base(event, project) + f"artifacts/{row.public_id}/inspection/")
    shown = org.get(artifact_url(event, project, row)).json()
    assert shown["state"] == "unavailable" and shown["media"] is None
    assert shown["reason"]["code"] == "active_content"
    gone = artifact(project, users["part"], key="k/gone")
    Artifact.objects.filter(pk=gone.pk).update(status="purged")
    purged = org.get(artifact_url(event, project, gone)).json()
    assert purged["reason"]["code"] == "purged" and purged["media"] is None


def test_a_link_artifact_shows_the_inspection_the_reviewers_see(storage):
    from artifacts.services import run_inspection
    from test_artifact_inspector import Response, public, scripted

    event, project, users = world(205)
    link = Artifact.objects.create(
        project=project, kind="live_url", visibility="public", title="Demo",
        external_url="https://demo.example/", status="ready", created_by=users["part"],
    )  # fmt: skip
    ok = Response(200, {"Content-Type": "text/html"}, b"<title>Hi</title>")
    run_inspection(link, users["org"], fetcher=scripted(ok), validator=public)
    shown = client_for(users["org"]).get(artifact_url(event, project, link)).json()
    assert shown["kind"] == "link" and shown["state"] == "ready"
    assert shown["link"] == "https://demo.example/" and shown["facts"]["title"] == "Hi"
    assert shown["media"] is None


def test_a_bad_request_names_what_is_missing(storage):
    event, project, users = world(206)
    org = client_for(users["org"])
    url = f"/api/v1/workspaces/{event.workspace.public_id}/previews/project_artifact/"
    missing = org.get(url + f"?event={event.public_id}")
    assert missing.status_code == 400 and set(missing.json()) == {"project", "artifact"}
    row = artifact(project, users["part"], key="k/x")
    junk = previews_url(
        event.workspace, "project_artifact", event="nope", project="x", artifact="y"
    )
    assert org.get(junk).status_code == 404
    assert org.get(previews_url(event.workspace, "wiki", a="b")).status_code == 404
    other_event = Event.objects.create(workspace=event.workspace, name="E2", slug="e2")
    wrong = previews_url(
        event.workspace, "project_artifact",
        event=other_event.public_id, project=project.public_id, artifact=row.public_id,
    )  # fmt: skip
    assert org.get(wrong).status_code == 404


# --- a job output: inspected on the fly, visible as the job is ------------------------------


@pytest.fixture
def output_world():
    workspace = Workspace.objects.create(name="W", slug="w")
    people = {}
    for name, role in (
        ("org", Role.ORGANIZER),
        ("org2", Role.ORGANIZER),
        ("par", Role.PARTICIPANT),
    ):
        user = User.objects.create_user(username=name, password="unused")
        Membership.objects.create(user=user, workspace=workspace, role=role)
        people[name] = user
    people["out"] = User.objects.create_user(username="out", password="unused")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    from core.models import Job

    row = Job.objects.create(
        workspace=workspace, event=event, kind="test_export", requested_by=people["org"], params={}
    )
    return {"workspace": workspace, "people": people, "job": row}


def output(world_, name, content_type, body):
    return JobArtifact.objects.create(
        job=world_["job"], name=name, content_type=content_type, size=len(body), body=body
    )


def output_url(world_, name):
    return previews_url(world_["workspace"], "job_output", job=world_["job"].public_id, name=name)


def test_a_job_output_is_inspected_on_the_fly_and_never_stored(output_world):
    output(output_world, "people.csv", "text/csv", b"name,score\nada,9\n")
    org = client_for(output_world["people"]["org"])
    audits = AuditEvent.objects.count()
    shown = org.get(output_url(output_world, "people.csv")).json()
    assert shown["kind"] == "data" and shown["state"] == "ready"
    assert shown["text"] == "name,score\nada,9\n" and shown["inspected_at"] is None
    expected = (
        f"/api/v1/workspaces/{output_world['workspace'].public_id}"
        f"/jobs/{output_world['job'].public_id}/artifacts/people.csv/"
    )
    assert shown["media"] == {"url": expected, "filename": "people.csv"}
    download = org.get(expected)
    assert download.status_code == 200 and "attachment" in download["Content-Disposition"]
    assert AuditEvent.objects.count() == audits and ArtifactInspection.objects.count() == 0


def test_job_output_visibility_is_the_jobs(output_world):
    output(output_world, "a.txt", "text/plain", b"hi")
    people = output_world["people"]
    assert client_for(people["org"]).get(output_url(output_world, "a.txt")).status_code == 200
    assert client_for(people["org2"]).get(output_url(output_world, "a.txt")).status_code == 200
    assert client_for(people["par"]).get(output_url(output_world, "a.txt")).status_code == 404
    assert client_for(people["out"]).get(output_url(output_world, "a.txt")).status_code == 403
    assert client_for(people["org"]).get(output_url(output_world, "nope.txt")).status_code == 404
    assert client_for(people["org"]).get(output_url(output_world, "")).status_code == 400


def test_a_job_output_with_active_content_is_withheld(output_world):
    output(output_world, "report.html", "text/html", b"<html><script>alert(1)</script></html>")
    shown = (
        client_for(output_world["people"]["org"])
        .get(output_url(output_world, "report.html"))
        .json()
    )
    assert shown["state"] == "unavailable" and shown["media"] is None and shown["text"] == ""
    assert shown["reason"]["message"].startswith("Withheld from preview")


def test_a_job_output_archive_lists_its_files(output_world):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("a.json", "{}")
        archive.writestr("b.csv", "x\n")
    output(output_world, "export.zip", "application/zip", buffer.getvalue())
    shown = (
        client_for(output_world["people"]["org"]).get(output_url(output_world, "export.zip")).json()
    )
    assert shown["kind"] == "archive" and [e["name"] for e in shown["entries"]] == [
        "a.json",
        "b.csv",
    ]


# --- an independent consumer registers a source with no private coupling --------------------


def test_a_feature_registers_its_own_source():
    seen = {}

    def resolve(user, workspace, ref):
        seen["ref"] = ref
        if ref["id"] != "1":
            return None
        return previews.Subject(
            name="Brief.txt", inspection=inspect_bytes(b"hello", filename="Brief.txt").as_dict()
        )

    source = previews.PreviewSource("test_toy", "Toy", ("id",), resolve)
    previews.register_source(source)
    try:
        previews.register_source(source)  # idempotent for the same object
        with pytest.raises(ValueError):
            previews.register_source(previews.PreviewSource("test_toy", "Other", ("id",), resolve))
        workspace = Workspace.objects.create(name="W", slug="w")
        user = User.objects.create_user(username="u", password="unused")
        Membership.objects.create(user=user, workspace=workspace, role=Role.PARTICIPANT)
        client = Client()
        client.cookies["session"] = Session.issue(user).token
        found = client.get(previews_url(workspace, "test_toy", id="1"))
        assert found.status_code == 200 and found.json()["text"] == "hello"
        assert seen["ref"] == {"id": "1"}
        assert client.get(previews_url(workspace, "test_toy", id="2")).status_code == 404
    finally:
        previews.SOURCES.pop("test_toy", None)
