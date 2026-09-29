"""Server-rendered public views (GAL-001/GAL-002): plain Django templates so
a raw HTTP GET (no JS) already contains real content -- see DECISIONS.md.
"""

from urllib.parse import urlencode

from awards.services import published_awards_for_public_display
from django.contrib.staticfiles import finders
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render

from .models import Page, PageBlockKind
from .public import (
    get_public_event,
    project_finalized_submissions,
    project_public_artifacts,
    public_projects,
)
from .records import RecordVerificationError, verify_record
from .showcase import prepare_showcase
from .technical import render_technical_description


def service_worker(request):
    """Served under `/e/` (not `/static/`) so its default scope covers every
    event page (VS22) -- a service worker can never control paths outside
    the directory it's served from without a `Service-Worker-Allowed`
    header, which plain static-file serving here doesn't set.
    """
    path = finders.find("sw.js")
    if not path:
        return HttpResponseNotFound()
    with open(path, "rb") as handle:
        return HttpResponse(handle.read(), content_type="application/javascript")


def verify(request):
    token = request.GET.get("token", "").strip()
    result = None
    if token:
        try:
            result = {"valid": True, "claims": verify_record(token)}
        except RecordVerificationError as exc:
            result = {"valid": False, "error": str(exc)}
    return render(request, "presentation/verify.html", {"token": token, "result": result})


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
            block.live = prepare_showcase(
                public_projects(event)[: block.config.get("limit", 6)], event
            )
        elif block.kind == PageBlockKind.RESULTS:
            block.live = published_awards_for_public_display(event)
        elif block.kind == PageBlockKind.ANNOUNCEMENTS:
            block.live = list(
                event.announcements.filter(hidden_at=None).select_related("posted_by")[:10]
            )
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
            "has_hero": any(block.kind == PageBlockKind.HERO for block in blocks),
        },
    )


GALLERY_PAGE_SIZE = 24


def gallery(request, event_public_id):
    event = get_public_event(event_public_id)
    q = request.GET.get("q", "").strip()
    stage_id = request.GET.get("stage", "").strip()
    track_id = request.GET.get("track", "").strip()
    projects = public_projects(
        event, q=q or None, stage_public_id=stage_id or None, track_public_id=track_id or None
    )
    page = Page.objects.filter(event=event).first()
    paginator = Paginator(projects, GALLERY_PAGE_SIZE)
    # get_page tolerates junk/out-of-range numbers: page 1 / last page.
    page_obj = paginator.get_page(request.GET.get("page"))
    preserved = {k: v for k, v in (("q", q), ("stage", stage_id), ("track", track_id)) if v}
    return render(
        request,
        "presentation/gallery.html",
        {
            "event": event,
            "theme": page.theme if page else "default",
            "projects": prepare_showcase(page_obj.object_list, event),
            "page_obj": page_obj,
            "total": paginator.count,
            "page_query": urlencode(preserved),
            "stages": event.stages.order_by("position"),
            "tracks": event.tracks.order_by("position"),
            "q": q,
            "selected_stage": stage_id,
            "selected_track": track_id,
        },
    )


def finalists(request, event_public_id):
    from .publication_views import finalist_projects

    event = get_public_event(event_public_id)
    page = Page.objects.filter(event=event).first()
    return render(
        request,
        "presentation/gallery.html",
        {
            "event": event,
            "theme": page.theme if page else "default",
            "projects": prepare_showcase(finalist_projects(event), event),
            "finalists": True,
        },
    )


def project_detail(request, event_public_id, project_public_id):
    event = get_public_event(event_public_id)
    project = get_object_or_404(public_projects(event), public_id=project_public_id)
    prepare_showcase([project], event)
    page = Page.objects.filter(event=event).first()
    return render(
        request,
        "presentation/project_detail.html",
        {
            "event": event,
            "theme": page.theme if page else "default",
            "project": project,
            "description_html": render_technical_description(project.description),
            "artifacts": project_public_artifacts(project),
            "submissions": project_finalized_submissions(project),
        },
    )
