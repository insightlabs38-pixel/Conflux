"""Server-rendered public views (GAL-001/GAL-002): plain Django templates so
a raw HTTP GET (no JS) already contains real content -- see DECISIONS.md.
"""

from django.shortcuts import get_object_or_404, render

from .models import Page, PageBlockKind
from .public import (
    get_public_event,
    project_finalized_submissions,
    project_public_artifacts,
    public_projects,
)


def _blocks_with_live_data(event, page):
    blocks = list(page.blocks.select_related("page")) if page else []
    for block in blocks:
        if block.kind == PageBlockKind.TRACKS:
            block.live = list(event.tracks.all())
        elif block.kind == PageBlockKind.PRIZES:
            block.live = list(event.base_prizes.select_related("track").all())
        elif block.kind == PageBlockKind.SCHEDULE:
            block.live = list(event.stages.order_by("position"))
        elif block.kind == PageBlockKind.GALLERY:
            block.live = list(public_projects(event)[: block.config.get("limit", 6)])
    return blocks


def event_landing(request, event_public_id):
    event = get_public_event(event_public_id)
    page = Page.objects.filter(event=event).first()
    blocks = _blocks_with_live_data(event, page)
    return render(
        request,
        "presentation/event_landing.html",
        {
            "event": event,
            "theme": page.theme if page else "default",
            "blocks": blocks,
        },
    )


def gallery(request, event_public_id):
    event = get_public_event(event_public_id)
    q = request.GET.get("q", "").strip()
    stage_id = request.GET.get("stage", "").strip()
    track_id = request.GET.get("track", "").strip()
    projects = public_projects(
        event, q=q or None, stage_public_id=stage_id or None, track_public_id=track_id or None
    )
    page = Page.objects.filter(event=event).first()
    return render(
        request,
        "presentation/gallery.html",
        {
            "event": event,
            "theme": page.theme if page else "default",
            "projects": projects,
            "stages": event.stages.order_by("position"),
            "tracks": event.tracks.order_by("position"),
            "q": q,
            "selected_stage": stage_id,
            "selected_track": track_id,
        },
    )


def project_detail(request, event_public_id, project_public_id):
    event = get_public_event(event_public_id)
    project = get_object_or_404(public_projects(event), public_id=project_public_id)
    page = Page.objects.filter(event=event).first()
    return render(
        request,
        "presentation/project_detail.html",
        {
            "event": event,
            "theme": page.theme if page else "default",
            "project": project,
            "artifacts": project_public_artifacts(project),
            "submissions": project_finalized_submissions(project),
        },
    )
