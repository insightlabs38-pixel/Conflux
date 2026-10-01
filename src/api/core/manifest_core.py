"""The capabilities backed by registries that live in `core`, and core's own manifest."""

from . import (
    approvals,
    entities,
    features,
    jobs,
    manifest,
    notifications,
    preview_context,
    previews,
    rich,
    threads,
    timeline,
    version_diff,
)


def _labels(registry):
    return lambda: {key: item.label for key, item in registry().items()}


CAPABILITIES = (
    (
        "job_kind",
        "Background job kind",
        "A long-running operation (`core.jobs`).",
        _labels(lambda: jobs.KINDS),
    ),
    (
        "approval_policy",
        "Approval policy",
        "An operation a second person can gate (`core.approvals`).",
        _labels(lambda: approvals.POLICIES),
    ),
    (
        "thread_subject",
        "Thread subject",
        "Something people comment on (`core.threads`).",
        _labels(lambda: threads.SUBJECTS),
    ),
    (
        "timeline_provider",
        "Timeline provider",
        "A source of event timeline items (`core.timeline`).",
        _labels(lambda: timeline.PROVIDERS),
    ),
    (
        "entity",
        "Queryable entity",
        "Rows that can be listed, filtered and saved (`core.entities`).",
        _labels(entities.entities),
    ),
    (
        "preview_source",
        "Preview source",
        "A file or link previewed safely (`core.previews`).",
        _labels(lambda: previews.SOURCES),
    ),
    (
        "version_source",
        "Version source",
        "A resource whose versions compare (`core.version_diff`).",
        _labels(lambda: version_diff.SOURCES),
    ),
    (
        "notification_category",
        "Notification category",
        "A kind of notice people tune (`core.notifications`).",
        _labels(lambda: notifications.CATEGORIES),
    ),
    (
        "feature",
        "Feature",
        "A feature whose completeness across surfaces is stated and checked (`core.features`).",
        _labels(lambda: features.FEATURES),
    ),
    (
        "preview_surface",
        "Preview surface",
        "Something previewed as a role, a time or a version (`core.preview_context`).",
        _labels(lambda: preview_context.SURFACES),
    ),
    (
        "rich_profile",
        "Rich content profile",
        "How a kind of text is read and drawn (`core.rich`).",
        _labels(lambda: rich.PROFILES),
    ),
)

for kind, label, description, live in CAPABILITIES:
    manifest.register_capability(manifest.Capability(kind, label, description, live))

manifest.register_manifest(
    manifest.Manifest(
        id="core",
        version="1.0.0",
        label="Platform core",
        provides=(("rich_profile", "page"), ("rich_profile", "story")),
    )
)
