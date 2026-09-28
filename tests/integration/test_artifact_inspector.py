import io
import struct
import zipfile

import pytest
from accounts.models import User
from artifacts.inspector import Inspection, inspect_bytes, sniff
from artifacts.models import Artifact, ArtifactInspection
from artifacts.services import run_inspection
from artifacts.url_inspector import inspect_url
from audit.models import AuditEvent
from django.core.exceptions import ValidationError
from integrations.demo_scenarios import generate_demo_event
from test_sponsor_portal import client_for

pytestmark = pytest.mark.django_db


def codes(report):
    return {f["code"] for f in report.findings}


def png(width=100, height=50):
    return (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", 13)
        + b"IHDR"
        + struct.pack(">II", width, height)
        + b"\x08\x06\x00\x00\x00"
    )


def jpeg_with_exif(width=30, height=20):
    return (
        b"\xff\xd8\xff\xe1\x00\x10Exif\x00\x00" + b"\x00" * 8
        + b"\xff\xc0\x00\x11\x08" + struct.pack(">HH", height, width) + b"\x03" + b"\x00" * 9
    )  # fmt: skip


def zip_bytes(entries, compression=zipfile.ZIP_STORED):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression) as archive:
        for name, content in entries.items():
            archive.writestr(zipfile.ZipInfo(name), content, compress_type=compression)
    return buffer.getvalue()


def test_sniffing_identifies_content_by_bytes_not_names():
    assert sniff(png()) == "png" and sniff(b"%PDF-1.7") == "pdf" and sniff(b"PK\x03\x04") == "zip"
    assert sniff(b"MZ\x90\x00") == "executable" and sniff(b"#!/bin/sh\n") == "executable"
    assert sniff(b"  <!DOCTYPE html><p>") == "html" and sniff(b"<svg xmlns='x'></svg>") == "svg"
    assert sniff(b"hello world\n") == "text" and sniff(b"\xff\xfe\x00\x01") == "binary"


def test_clean_image_reports_dimensions_and_exif_is_flagged():
    clean = inspect_bytes(png(), claimed_type="image/png", kind="image")
    assert clean.verdict == "clean" and clean.facts["width"] == 100 and clean.facts["height"] == 50
    exif = inspect_bytes(jpeg_with_exif(), claimed_type="image/jpeg", kind="image")
    assert exif.verdict == "warnings" and "image_metadata" in codes(exif)
    huge = inspect_bytes(png(60000, 60000), claimed_type="image/png", kind="image")
    assert "image_dimensions" in codes(huge)


def test_active_content_programs_and_disguises_are_blocked():
    assert (
        inspect_bytes(
            b"<html><script>x</script>", claimed_type="application/pdf", kind="document"
        ).verdict
        == "blocked"
    )
    assert "executable" in codes(
        inspect_bytes(b"\x7fELF\x02\x01", claimed_type="image/png", kind="image")
    )
    svg = inspect_bytes(b"<svg onload='x'/>", claimed_type="image/png", kind="image")
    assert "active_content" in codes(svg)
    mismatch = inspect_bytes(b"%PDF-1.4 /Type /Page", claimed_type="image/png", kind="image")
    assert {"type_mismatch", "claimed_type_mismatch"} <= codes(mismatch)
    assert "program_extension" in codes(inspect_bytes(b"text", filename="setup.exe", kind="file"))
    bad = inspect_bytes(b"data", expected_sha256="0" * 64)
    assert "digest_mismatch" in codes(bad) and bad.verdict == "blocked"


def test_pdfs_report_pages_and_active_features():
    plain = inspect_bytes(b"%PDF-1.4 /Type /Page /Type /Page /Type /Pages", kind="document")
    assert plain.facts["pages"] == 2 and plain.verdict == "clean"
    active = inspect_bytes(b"%PDF-1.4 /Type /Page /OpenAction /JavaScript", kind="document")
    assert "pdf_active_content" in codes(active)
    assert "pdf_encrypted" in codes(inspect_bytes(b"%PDF-1.4 /Encrypt", kind="document"))


def test_archives_are_listed_never_extracted_and_hazards_are_reported():
    good = inspect_bytes(zip_bytes({"README.md": b"hi", "src/app.py": b"print(1)"}), kind="file")
    assert good.verdict == "clean" and good.facts["entries"] == 2
    assert [e["name"] for e in good.facts["listing"]] == ["README.md", "src/app.py"]
    slip = inspect_bytes(
        zip_bytes({"../../etc/passwd": b"x", "/abs": b"y", "C:\\w.txt": b"z"}), kind="file"
    )
    assert slip.verdict == "blocked" and "archive_path_traversal" in codes(slip)
    bomb = inspect_bytes(
        zip_bytes({"zeros": b"\0" * 30_000_000}, zipfile.ZIP_DEFLATED), kind="file"
    )
    assert "archive_bomb" in codes(bomb) and bomb.verdict == "blocked"
    mixed = inspect_bytes(
        zip_bytes({"run.exe": b"MZ", ".env": b"K=1", "inner.zip": b"PK"}), kind="file"
    )
    assert {"archive_programs", "archive_secret_files", "archive_nested"} <= codes(mixed)
    assert "archive_unreadable" in codes(inspect_bytes(b"PK\x03\x04garbage", kind="file"))


def test_secrets_are_flagged_without_echoing_them_and_previews_are_safe():
    key = "AKIA" + "ABCDEFGHIJKLMNOP"
    body = f"line one\nAWS={key}\n-----BEGIN RSA PRIVATE KEY-----\n\x1b[31mred\x07".encode()
    report = inspect_bytes(body, kind="document", claimed_type="text/plain")
    assert [f["detail"] for f in report.findings if f["code"] == "possible_secret"] == [
        "A private key block appears near line 3.",
        "A AWS access key appears near line 2.",
    ]
    assert key not in str(report.as_dict())
    assert "\x1b" not in report.preview and "\x07" not in report.preview
    assert len(inspect_bytes(b"a" * 50000, kind="document").preview) == 4000


class Response:
    def __init__(self, status, headers, body=b""):
        self.value = (status, headers, body)


def scripted(*responses):
    calls = iter(responses)
    return lambda host, address, path: next(calls).value


def public(url):
    from urllib.parse import urlsplit

    return urlsplit(url), "93.184.216.34"


def test_links_are_inspected_through_the_guard_with_revalidated_redirects():
    page = Response(
        200,
        {"Content-Type": "text/html; charset=utf-8", "Server": "nginx"},
        b"<html><title> My  Demo </title>",
    )
    report = Inspection()
    inspect_url("https://demo.example/app", report, fetcher=scripted(page), validator=public)
    assert report.verdict == "clean" and report.facts["title"] == "My Demo"
    assert report.facts["embeddable"] is True and report.facts["status"] == 200
    hop = Response(302, {"Location": "https://other.example/x"})
    moved = Inspection()
    inspect_url("https://demo.example/", moved, fetcher=scripted(hop, page), validator=public)
    assert "cross_domain_redirect" in codes(moved) and moved.facts["redirect_chain"] == [
        "demo.example",
        "other.example",
    ]
    loop = Inspection()
    inspect_url(
        "https://a.example/",
        loop,
        fetcher=lambda *a: (302, {"Location": "/again"}, b""),
        validator=public,
    )
    assert "redirect_loop" in codes(loop)


def test_unsafe_targets_and_risky_links_are_reported():
    def refuse(url):
        raise ValueError("Webhook host must resolve only to public addresses.")

    blocked = Inspection()
    inspect_url(
        "https://10.0.0.1/", blocked, fetcher=lambda *a: pytest.fail("no fetch"), validator=refuse
    )
    assert blocked.verdict == "blocked" and {"ip_literal", "unsafe_destination"} <= codes(blocked)
    flags = Inspection()
    ok = Response(200, {"Content-Type": "application/octet-stream", "X-Frame-Options": "DENY"})
    inspect_url("https://xn--pple-43d.example/", flags, fetcher=scripted(ok), validator=public)
    assert {"punycode", "forces_download"} <= codes(flags) and flags.facts["embeddable"] is False
    short = Inspection()
    inspect_url("https://bit.ly/abc", short, fetcher=scripted(Response(404, {})), validator=public)
    assert {"url_shortener", "http_error"} <= codes(short)
    down = Inspection()

    def fail(*args):
        raise OSError("refused")

    inspect_url("https://gone.example/", down, fetcher=fail, validator=public)
    assert "unreachable" in codes(down)


class FakeStorage:
    def __init__(self, objects):
        self.objects = objects
        self.reads = 0

    def get(self, key):
        self.reads += 1
        return {"Body": io.BytesIO(self.objects[key])}

    def presign_get(self, key, expires=300, *, download_filename=None):
        return f"https://storage.test/{key}?attachment={download_filename}"


def world(seed=101):
    event = generate_demo_event(seed=seed, participants=4, judges=2)
    prefix = f"demo-hackathon-{seed}-"
    users = {
        "org": User.objects.get(username=prefix + "organizer"),
        "judge": User.objects.get(username=prefix + "judge-01"),
        "part": User.objects.get(username=prefix + "participant-01"),
        "other": User.objects.get(username=prefix + "participant-02"),
    }
    project = event.projects.get(created_by=users["part"])
    return event, project, users


def artifact(
    project, owner, *, visibility="judge", kind="document", key="k/1", body=b"%PDF-1.4 /Type /Page"
):
    import hashlib

    return Artifact.objects.create(
        project=project,
        kind=kind,
        visibility=visibility,
        title="Notes",
        object_key=key,
        byte_size=len(body),
        content_type="application/pdf",
        sha256=hashlib.sha256(body).hexdigest(),
        status="ready",
        created_by=owner,
    )


def base(event, project):
    return (
        f"/api/v1/workspaces/{event.workspace.public_id}/events/{event.public_id}"
        f"/projects/{project.public_id}/"
    )


def test_inspection_is_persisted_immutable_audited_and_rate_limited():
    event, project, users = world()
    body = b"%PDF-1.4 /Type /Page /JavaScript"
    row = artifact(project, users["part"], body=body)
    storage = FakeStorage({"k/1": body})
    first = run_inspection(row, users["org"], storage=storage)
    assert first.verdict == "warnings" and storage.reads == 1
    assert run_inspection(row, users["org"], storage=storage).pk == first.pk and storage.reads == 1
    with pytest.raises(ValidationError):
        first.verdict = "clean"
        first.save()
    assert AuditEvent.objects.filter(action="artifact.inspected").count() == 1
    assert ArtifactInspection.objects.count() == 1


def test_reviewer_access_follows_role_visibility_and_expected_evaluation(monkeypatch):
    event, project, users = world(102)
    body = b"%PDF-1.4 /Type /Page"
    open_row = artifact(project, users["part"], visibility="judge", key="k/judge", body=body)
    secret_row = artifact(project, users["part"], visibility="organizer", key="k/org", body=body)
    storage = FakeStorage({"k/judge": body, "k/org": body})
    monkeypatch.setattr("artifacts.services.S3Storage", lambda: storage)
    monkeypatch.setattr("artifacts.review_views.S3Storage", lambda: storage)
    listing = base(event, project) + "review-artifacts/"
    judge, org = client_for(users["judge"]), client_for(users["org"])
    assert {a["public_id"] for a in judge.get(listing).json()} == {str(open_row.public_id)}
    assert {a["public_id"] for a in org.get(listing).json()} == {
        str(open_row.public_id),
        str(secret_row.public_id),
    }
    assert judge.get(listing).json()[0]["download_url"].startswith("https://storage.test/k/judge")
    url = base(event, project) + f"review-artifacts/{open_row.public_id}/inspection/"
    assert judge.get(url).status_code == 404
    done = judge.post(url)
    assert done.status_code == 200 and done.json()["verdict"] == "clean"
    assert judge.get(url).json()["public_id"] == done.json()["public_id"]
    hidden = base(event, project) + f"review-artifacts/{secret_row.public_id}/inspection/"
    assert judge.post(hidden).status_code == 404 and org.post(hidden).status_code == 200
    assert client_for(users["other"]).get(listing).status_code == 404
    assert client_for(users["part"]).get(listing).status_code == 404


def test_blocked_content_never_gets_a_download_link_and_members_can_self_check(monkeypatch):
    event, project, users = world(103)
    body = b"<html><script>alert(1)</script>"
    row = artifact(project, users["part"], visibility="judge", key="k/bad", body=body)
    storage = FakeStorage({"k/bad": body})
    monkeypatch.setattr("artifacts.services.S3Storage", lambda: storage)
    monkeypatch.setattr("artifacts.review_views.S3Storage", lambda: storage)
    member = client_for(users["part"])
    mine = base(event, project) + f"artifacts/{row.public_id}/inspection/"
    result = member.post(mine)
    assert result.status_code == 200 and result.json()["verdict"] == "blocked"
    assert client_for(users["other"]).post(mine).status_code == 404
    org = client_for(users["org"])
    listed = org.get(base(event, project) + "review-artifacts/").json()[0]
    assert listed["inspection"]["verdict"] == "blocked" and listed["download_url"] is None


def test_links_and_purged_or_unfinished_artifacts():
    event, project, users = world(104)
    link = Artifact.objects.create(
        project=project, kind="live_url", visibility="public", title="Demo",
        external_url="https://demo.example/", status="ready", created_by=users["part"],
    )  # fmt: skip
    ok = Response(200, {"Content-Type": "text/html"}, b"<title>Hi</title>")
    record = run_inspection(link, users["org"], fetcher=scripted(ok), validator=public)
    assert record.subject == "link" and record.facts["title"] == "Hi"
    pending = artifact(project, users["part"], key="k/p")
    Artifact.objects.filter(pk=pending.pk).update(status="pending")
    with pytest.raises(ValidationError, match="no uploaded content"):
        run_inspection(pending, users["org"], storage=FakeStorage({}))
    Artifact.objects.filter(pk=pending.pk).update(status="purged")
    with pytest.raises(ValidationError, match="purged"):
        run_inspection(pending, users["org"], storage=FakeStorage({}))
