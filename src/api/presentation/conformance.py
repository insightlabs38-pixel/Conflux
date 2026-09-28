"""Accessibility evidence for the pages a visitor can actually reach (VS47).

Each public page is fetched through the real request stack, so publication
windows and visibility apply exactly as they do for visitors, then checked
against the WCAG criteria that static HTML can settle. The report never
claims conformance: criteria that need a person or assistive technology are
listed as manual review items.
"""

import hashlib
import re
from html.parser import HTMLParser

from django.conf import settings
from django.test import Client
from django.urls import reverse

from .accessibility import VAGUE_LINK_TEXT, audit_theme
from .models import Page
from .public import public_projects
from .stories import visible_awards

SAMPLE_LIMIT = 10
EVIDENCE_LIMIT = 5
VOID = {"img", "input", "meta", "link", "br", "hr", "source", "area", "base", "col", "wbr"}
NAMED = {"a", "button", "label", "title", "th", "h1", "h2", "h3", "h4", "h5", "h6"}
NON_TEXT_INPUTS = {"hidden", "submit", "button", "reset", "image"}

MANUAL_REVIEW = [
    ("1.2.x", "Captions, transcripts and audio description for any embedded media"),
    ("1.4.10", "Reflow at 320 CSS px and 400% zoom"),
    ("1.4.11", "Contrast of component boundaries and focus indicators as rendered"),
    ("2.1.2", "No keyboard traps across the full page flow"),
    ("2.4.7", "Visible keyboard focus on every interactive element"),
    ("3.3.x", "Error identification and suggestions in submitted forms"),
    ("4.1.3", "Status messages announced by assistive technology"),
]

CRITERIA = {
    "language": ("3.1.1", "A", "Document declares its language"),
    "title": ("2.4.2", "A", "Document has a non-empty title"),
    "single-h1": ("1.3.1", "A", "Exactly one h1"),
    "heading-order": ("1.3.1", "A", "Heading levels do not skip"),
    "landmarks": ("2.4.1", "A", "Main landmark and working skip link"),
    "image-alt": ("1.1.1", "A", "Images have text alternatives"),
    "link-name": ("2.4.4", "A", "Links have descriptive accessible names"),
    "control-label": ("3.3.2", "A", "Form controls have labels"),
    "button-name": ("4.1.2", "A", "Buttons have accessible names"),
    "frame-title": ("4.1.2", "A", "Frames have titles"),
    "zoom": ("1.4.4", "AA", "Viewport permits zooming"),
    "tabindex": ("2.4.3", "A", "No positive tabindex"),
    "unique-id": ("4.1.1", "A", "Element ids are unique"),
    "table-headers": ("1.3.1", "A", "Data tables declare header cells"),
}


class _Scan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = None
        self.title = ""
        self.headings = []
        self.images = []
        self.links = []
        self.buttons = []
        self.controls = []
        self.labels = []
        self.frames = []
        self.ids = []
        self.tabindex = []
        self.tables = []
        self.mains = 0
        self.anchors = []
        self.viewport = ""
        self.open = []
        self.first_link = None

    def handle_starttag(self, tag, attrs):
        attrs = {key: value or "" for key, value in attrs}
        if tag == "html":
            self.lang = attrs.get("lang", "").strip()
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if attrs.get("tabindex", "").lstrip("+").isdigit() and int(attrs["tabindex"]) > 0:
            self.tabindex.append(tag)
        if tag == "meta" and attrs.get("name") == "viewport":
            self.viewport = attrs.get("content", "")
        if tag == "main" or attrs.get("role") == "main":
            self.mains += 1
        if tag == "img":
            self.images.append(attrs)
            for entry in self.open:
                entry["text"].append(attrs.get("alt", ""))
        if tag == "iframe":
            self.frames.append(attrs)
        if tag in {"input", "select", "textarea"} and attrs.get("type") not in NON_TEXT_INPUTS:
            self.controls.append(
                {"tag": tag, "attrs": attrs, "wrapped": any(e["tag"] == "label" for e in self.open)}
            )
        if tag == "table":
            self.tables.append({"attrs": attrs, "headers": 0, "cells": 0})
        if tag == "th" and self.tables:
            self.tables[-1]["headers"] += 1
        if tag == "td" and self.tables:
            self.tables[-1]["cells"] += 1
        if tag == "a" and "href" in attrs and self.first_link is None:
            self.first_link = attrs["href"]
        if tag in NAMED:
            self.open.append({"tag": tag, "attrs": attrs, "text": []})

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_data(self, data):
        for entry in self.open:
            entry["text"].append(data)

    def handle_endtag(self, tag):
        if tag not in NAMED:
            return
        for index in range(len(self.open) - 1, -1, -1):
            if self.open[index]["tag"] == tag:
                entry = self.open.pop(index)
                break
        else:
            return
        text = " ".join("".join(entry["text"]).split())
        entry["name"] = text
        if tag == "title":
            self.title = text
        elif tag == "label":
            self.labels.append(entry)
        elif tag == "a" and "href" in entry["attrs"]:
            self.links.append(entry)
        elif tag == "button":
            self.buttons.append(entry)
        elif tag[0] == "h":
            self.headings.append((int(tag[1]), text))


def _named(entry):
    attrs = entry["attrs"]
    return bool(
        attrs.get("aria-label", "").strip() or attrs.get("aria-labelledby") or entry["name"]
    )


def _checks(scan):
    labelled_ids = {label["attrs"].get("for") for label in scan.labels if label["name"]}
    levels = [level for level, _ in scan.headings]
    duplicated = sorted({i for i in scan.ids if scan.ids.count(i) > 1})
    failures = {
        "language": [] if scan.lang else ["<html> has no lang attribute"],
        "title": [] if scan.title else ["<title> is missing or empty"],
        "single-h1": [] if levels.count(1) == 1 else [f"{levels.count(1)} h1 elements"],
        "heading-order": [
            f"h{a} followed by h{b}" for a, b in zip(levels, levels[1:]) if b - a > 1
        ],
        "landmarks": (["no main landmark"] if scan.mains != 1 else [])
        + (
            []
            if scan.first_link
            and scan.first_link.startswith("#")
            and scan.first_link[1:] in scan.ids
            else ["first link is not a working skip link"]
        ),
        "image-alt": [f"img {a.get('src', '')[:60]}" for a in scan.images if "alt" not in a],
        "link-name": [
            f"link {entry['attrs']['href'][:60]!r}: "
            + ("no accessible name" if not _named(entry) else f"vague text {entry['name']!r}")
            for entry in scan.links
            if not _named(entry) or entry["name"].lower() in VAGUE_LINK_TEXT
        ],
        "control-label": [
            f"{c['tag']} name={c['attrs'].get('name', '')!r}"
            for c in scan.controls
            if not (
                c["wrapped"]
                or c["attrs"].get("aria-label", "").strip()
                or c["attrs"].get("aria-labelledby")
                or c["attrs"].get("id") in labelled_ids
            )
        ],
        "button-name": ["button without name" for b in scan.buttons if not _named(b)],
        "frame-title": [
            f"iframe {f.get('src', '')[:60]}" for f in scan.frames if not f.get("title")
        ],
        "zoom": (
            ["viewport disables scaling"]
            if re.search(r"user-scalable\s*=\s*(no|0)|maximum-scale\s*=\s*1(\.0)?\b", scan.viewport)
            else []
        ),
        "tabindex": [f"<{tag}> has positive tabindex" for tag in scan.tabindex],
        "unique-id": [f"duplicate id {i!r}" for i in duplicated],
        "table-headers": [
            "table has cells but no th"
            for table in scan.tables
            if table["cells"]
            and not table["headers"]
            and table["attrs"].get("role") != "presentation"
        ],
    }
    return [
        {
            "check": name,
            "criterion": CRITERIA[name][0],
            "level": CRITERIA[name][1],
            "description": CRITERIA[name][2],
            "outcome": "fail" if found else "pass",
            "evidence": found[:EVIDENCE_LIMIT],
        }
        for name, found in failures.items()
    ]


def _stable(content):
    """Per-response CSRF tokens must not make identical content hash differently."""
    return re.sub(rb'(name="csrfmiddlewaretoken" value=")[^"]*', rb"\1", content)


def audit_html(html):
    scan = _Scan()
    scan.feed(html)
    scan.close()
    return _checks(scan)


def _client():
    hosts = [h for h in settings.ALLOWED_HOSTS if h and not h.startswith((".", "*"))]
    return Client(SERVER_NAME=hosts[0] if hosts else "localhost")


def _targets(event):
    yield "event", reverse("site-event", args=[event.public_id])
    yield "gallery", reverse("site-gallery", args=[event.public_id])
    yield "results", reverse("site-results", args=[event.public_id])
    yield "finalists", reverse("site-finalists", args=[event.public_id])
    projects = list(public_projects(event)[:SAMPLE_LIMIT])
    for project in projects:
        yield "project", reverse("site-project", args=[event.public_id, project.public_id])
    for award in list(visible_awards(event).order_by("pk")[:SAMPLE_LIMIT]):
        yield "award-story", reverse("site-award-story", args=[event.public_id, award.public_id])
    for project in projects:
        yield (
            "project-story",
            reverse("site-project-story", args=[event.public_id, project.public_id]),
        )


def build_conformance_report(event, *, now):
    client = _client()
    secure = bool(getattr(settings, "SECURE_SSL_REDIRECT", False))
    pages = []
    for kind, path in _targets(event):
        response = client.get(path, secure=secure)
        if response.status_code != 200:
            pages.append({"kind": kind, "path": path, "status": response.status_code})
            continue
        body = response.content.decode(response.charset or "utf-8")
        checks = audit_html(body)
        pages.append(
            {
                "kind": kind,
                "path": path,
                "status": 200,
                "sha256": hashlib.sha256(_stable(response.content)).hexdigest(),
                "checks": checks,
                "failed": sum(check["outcome"] == "fail" for check in checks),
            }
        )
    page = Page.objects.filter(event=event).first()
    theme = page.theme if page else "default"
    theme_warnings = audit_theme(theme)
    audited = [p for p in pages if p["status"] == 200]
    failed_pages = [p["path"] for p in audited if p["failed"]]
    return {
        "event": str(event.public_id),
        "generated_at": now.isoformat(),
        "conformance_claimed": False,
        "standard": "WCAG 2.1 (automated static checks only)",
        "theme": {"name": theme, "contrast_warnings": theme_warnings},
        "summary": {
            "pages_audited": len(audited),
            "pages_unavailable": len(pages) - len(audited),
            "pages_with_failures": len(failed_pages),
            "failed_checks": sum(p["failed"] for p in audited) + len(theme_warnings),
        },
        "pages": pages,
        "manual_review": [{"criterion": c, "item": item} for c, item in MANUAL_REVIEW],
    }
