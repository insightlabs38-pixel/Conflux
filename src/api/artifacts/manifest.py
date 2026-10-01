"""Artifact validators and preview sources (EXTENSION_MANIFEST)."""

from core import manifest

from . import features  # noqa: F401 - registers this app's features
from .validators import VALIDATORS

manifest.register_capability(
    manifest.Capability(
        "artifact_validator",
        "Artifact validator",
        "How one kind of submitted artifact is checked (`artifacts.validators`).",
        lambda: {str(kind): str(kind).replace("_", " ").capitalize() for kind in VALIDATORS},
    )
)
manifest.register_manifest(
    manifest.Manifest(
        id="artifacts",
        version="1.0.0",
        label="Submitted artifacts",
        provides=(
            ("feature", "artifact"),
            *(
                ("artifact_validator", kind)
                for kind in (
                    "dataset",
                    "document",
                    "external_video",
                    "file",
                    "image",
                    "live_url",
                    "repository",
                    "secret",
                    "video",
                )
            ),
            ("preview_source", "job_output"),
            ("preview_source", "project_artifact"),
        ),
        requires=(("manifest", "core"),),
    )
)
