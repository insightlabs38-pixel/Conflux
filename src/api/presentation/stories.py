import unicodedata

from awards.models import Award, AwardWinner
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

from .models import Page
from .public import get_public_event, public_projects
from .technical import render_technical_description


def visible_awards(event):
    winners = AwardWinner.objects.filter(project__in=public_projects(event)).select_related(
        "project", "project__track"
    )
    return (
        Award.objects.filter(event=event, published_at__isnull=False)
        .prefetch_related(
            Prefetch(
                "winners",
                queryset=winners.order_by("selected_at", "public_id"),
                to_attr="public_winners",
            )
        )
        .order_by("name", "public_id")
    )


def _context(request, event, *, title, description, route, card_route, source_id):
    page = Page.objects.filter(event=event).first()
    path = reverse(route, args=[event.public_id, source_id])
    card_path = reverse(card_route, args=[event.public_id, source_id])
    return {
        "event": event,
        "theme": page.theme if page else "default",
        "story_title": title,
        "story_description": description,
        "story_url": request.build_absolute_uri(path),
        "card_url": request.build_absolute_uri(card_path),
        "card_path": card_path,
    }


@require_safe
@never_cache
def results(request, event_public_id):
    event = get_public_event(event_public_id)
    page = Page.objects.filter(event=event).first()
    try:
        number = int(request.GET.get("page", "1"))
        if number < 1:
            raise ValueError
    except ValueError as exc:
        raise Http404("Invalid results page.") from exc
    paginator = Paginator(visible_awards(event), 50)
    if number > paginator.num_pages:
        raise Http404("Results page does not exist.")
    return render(
        request,
        "presentation/results.html",
        {
            "event": event,
            "theme": page.theme if page else "default",
            "awards_page": paginator.page(number),
        },
    )


@require_safe
@never_cache
def award_story(request, event_public_id, award_public_id):
    event = get_public_event(event_public_id)
    award = get_object_or_404(visible_awards(event), public_id=award_public_id)
    context = _context(
        request,
        event,
        title=award.name,
        description=_plain(award.description)[:200],
        route="site-award-story",
        card_route="site-award-card",
        source_id=award.public_id,
    )
    return render(request, "presentation/award_story.html", {**context, "award": award})


@require_safe
@never_cache
def project_story(request, event_public_id, project_public_id):
    event = get_public_event(event_public_id)
    project = get_object_or_404(public_projects(event), public_id=project_public_id)
    awards = visible_awards(event).filter(winners__project=project).distinct()
    if not awards.exists():
        raise Http404("No published awards for this project.")
    context = _context(
        request,
        event,
        title=project.name,
        description=_plain(project.description)[:200],
        route="site-project-story",
        card_route="site-project-card",
        source_id=project.public_id,
    )
    return render(
        request,
        "presentation/project_story.html",
        {
            **context,
            "project": project,
            "awards": awards,
            "description_html": render_technical_description(project.description),
        },
    )


def _plain(value):
    # XML 1.0 excludes control characters that can be stored in ordinary text fields.
    value = "".join(
        char
        for char in strip_tags(value)
        if ord(char) in (9, 10, 13)
        or 32 <= ord(char) <= 0xD7FF
        or 0xE000 <= ord(char) <= 0xFFFD
        or 0x10000 <= ord(char) <= 0x10FFFF
    )
    return " ".join(value.split())


def _width(value):
    return sum(
        2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1.6 if char in "WMwm@" else 1
        for char in value
    )


def _lines(value, width, limit, start_y, step):
    remaining = _plain(value)
    lines = []
    while remaining and len(lines) < limit:
        end = 0
        while end < len(remaining) and _width(remaining[: end + 1]) <= width:
            end += 1
        if end < len(remaining):
            space = remaining.rfind(" ", 0, end + 1)
            if space > 0:
                end = space
        lines.append(remaining[:end])
        remaining = remaining[end:].lstrip()
    if remaining:
        lines[-1] = lines[-1].rstrip() + "…"
    return [{"text": text, "y": start_y + index * step} for index, text in enumerate(lines)]


def _card(event, title, subtitle, source_id, download):
    context = {
        "event_name": _plain(event.name),
        "title": _plain(title),
        "event_lines": _lines(event.name, 60, 2, 90, 30),
        "title_lines": _lines(title, 26, 3, 220, 72),
        "subtitle_lines": _lines(subtitle, 60, 2, 485, 36),
    }
    response = HttpResponse(
        render_to_string("presentation/result_card.svg", context), content_type="image/svg+xml"
    )
    response["Content-Security-Policy"] = "default-src 'none'; style-src 'none'; sandbox"
    response["X-Content-Type-Options"] = "nosniff"
    if download:
        response["Content-Disposition"] = f'attachment; filename="conflux-result-{source_id}.svg"'
    return response


@require_safe
@never_cache
def award_card(request, event_public_id, award_public_id):
    event = get_public_event(event_public_id)
    award = get_object_or_404(visible_awards(event), public_id=award_public_id)
    names = ", ".join(winner.project.name for winner in award.public_winners)
    return _card(
        event,
        award.name,
        names or "Published award",
        award.public_id,
        request.GET.get("download") == "1",
    )


@require_safe
@never_cache
def project_card(request, event_public_id, project_public_id):
    event = get_public_event(event_public_id)
    project = get_object_or_404(public_projects(event), public_id=project_public_id)
    awards = visible_awards(event).filter(winners__project=project).distinct()
    if not awards.exists():
        raise Http404("No published awards for this project.")
    return _card(
        event,
        project.name,
        ", ".join(award.name for award in awards),
        project.public_id,
        request.GET.get("download") == "1",
    )
