"""Advancement strategies (EXTENSION_MANIFEST)."""

from core import manifest

from . import features  # noqa: F401 - registers this app's features
from .advancement import REGISTRY

manifest.register_capability(
    manifest.Capability(
        "advancement_strategy",
        "Advancement strategy",
        "How participants are chosen to move to the next stage (`stages.advancement`).",
        lambda: {slug: slug.replace("_", " ").capitalize() for slug in REGISTRY},
    )
)
manifest.register_manifest(
    manifest.Manifest(
        id="stages",
        version="1.0.0",
        label="Stages",
        provides=(("feature", "stage"),)
        + tuple(
            ("advancement_strategy", slug)
            for slug in (
                "everyone",
                "external",
                "manual",
                "pass_fail",
                "percentile",
                "threshold",
                "top_n",
                "top_n_per_track",
            )
        ),
        requires=(("manifest", "core"),),
    )
)
