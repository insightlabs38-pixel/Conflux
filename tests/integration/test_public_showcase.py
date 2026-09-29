"""Showcase enrichment must honor the existing public/integrity boundaries."""

import pytest
from accounts.models import UserProfile
from artifacts.models import Artifact
from django.test import Client
from presentation.models import ProjectSearchTag
from presentation.showcase import prepare_showcase
from test_public_site import make_public_event_with_finalized_project

pytestmark = pytest.mark.django_db


def test_gallery_and_detail_expose_only_opted_in_person_identity():
    event, project, _ = make_public_event_with_finalized_project()
    profile = UserProfile.objects.create(
        user=project.created_by, display_name="Private maker", bio="Private biography"
    )
    ProjectSearchTag.objects.create(project=project, tag="Education")
    paths = [
        f"/e/{event.public_id}/gallery/",
        f"/e/{event.public_id}/projects/{project.public_id}/",
    ]
    for path in paths:
        body = Client().get(path).content.decode()
        assert "Education" in body
        assert "Private maker" not in body and "Private biography" not in body
        assert f"person={project.created_by.public_id}" not in body
    profile.visibility, profile.display_name = "public", "Public maker"
    profile.save()
    for path in paths:
        body = Client().get(path).content.decode()
        assert "Public maker" in body
    detail = Client().get(paths[1]).content.decode()
    assert f"person={project.created_by.public_id}" in detail
    assert "Submission evidence" in detail and "Version and integrity reference" in detail
    assert "a" * 64 in detail


def test_preview_whitelist_keeps_active_content_private_and_pending_artifacts_out(monkeypatch):
    event, project, _ = make_public_event_with_finalized_project()
    monkeypatch.setattr(
        "presentation.public.S3Storage.presign_get",
        lambda self, key, **kwargs: f"https://example.com/signed/{key}",
    )
    for title, kind, content_type, visibility, status in [
        ("Screenshot", "image", "image/png", "public", "ready"),
        ("Demo", "video", "video/webm", "public", "ready"),
        ("Active SVG", "image", "image/svg+xml", "public", "ready"),
        ("Document", "document", "text/html", "public", "ready"),
        ("Private image", "image", "image/png", "judge", "ready"),
        ("Pending image", "image", "image/png", "public", "pending"),
    ]:
        Artifact.objects.create(
            project=project,
            created_by=project.created_by,
            title=title,
            kind=kind,
            content_type=content_type,
            visibility=visibility,
            status=status,
            object_key=title,
        )
    enriched = prepare_showcase([project], event)[0].showcase
    assert {item["title"] for item in enriched["media"]} == {"Screenshot", "Demo"}
    assert enriched["cover"]["title"] == "Screenshot"
    assert {item["title"] for item in enriched["artifacts"]} == {
        "Source",
        "Screenshot",
        "Demo",
        "Active SVG",
        "Document",
    }
    body = Client().get(f"/e/{event.public_id}/projects/{project.public_id}/").content.decode()
    assert "<video controls" in body
    assert "<iframe" not in body and "<object" not in body
    assert 'src="https://example.com/signed/Active SVG"' not in body
    assert 'src="https://example.com/signed/Document"' not in body
    assert "Private image" not in body and "Pending image" not in body


def test_showcase_uses_description_not_invented_metadata():
    event, project, _ = make_public_event_with_finalized_project()
    project.description = "# Actual project\n\n**Original story** [safe](https://example.com)."
    project.save()
    enriched = prepare_showcase([project], event)[0].showcase
    assert enriched["summary"] == "Actual project Original story safe."
    assert enriched["initials"] == "A"
    assert enriched["cover"] is None and enriched["tags"] == []
