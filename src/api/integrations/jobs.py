"""Background kinds owned by the integrations app (PD-F002-B01-T05)."""

import json

from core import jobs
from django.core.exceptions import ValidationError as ModelValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.utils.encoders import JSONEncoder
from workspaces.models import Role

from .archive import build_archive
from .signed_archive import sign_archive


class ArchiveExportParams(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["config", "full", "final"], default="config")
    signed = serializers.BooleanField(default=False)


def export_archive(ctx):
    """Build (and optionally sign) an event archive and keep it as the job's download."""
    mode, signed = ctx.params["mode"], ctx.params["signed"]
    steps = 3 if signed else 2
    ctx.progress(0, steps, f"Building the {mode} archive")
    try:
        archive = build_archive(ctx.event, mode=mode)
    except ModelValidationError as exc:
        raise ValidationError(
            exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        ) from exc
    ctx.checkpoint()
    document = archive
    if signed:
        ctx.progress(1, steps, "Signing the archive")
        document = sign_archive(archive)
        ctx.checkpoint()
    ctx.progress(steps - 1, steps, "Saving the file")
    body = json.dumps(document, cls=JSONEncoder, separators=(",", ":")).encode()
    name = f"{ctx.event.slug}-{mode}{'-signed' if signed else ''}-archive.json"
    ctx.artifact(name, "application/json", body)
    ctx.log(f"Saved {name} ({len(body)} bytes)")
    return {
        "mode": archive.get("mode", mode),
        "format_version": archive.get("format_version"),
        "signed": signed,
        "filename": name,
        "bytes": len(body),
    }


ARCHIVE_EXPORT = jobs.register_kind(
    jobs.JobKind(
        key="archive_export",
        label="Event archive export",
        handler=export_archive,
        roles=(Role.ORGANIZER, Role.ADMIN),
        params=ArchiveExportParams,
        timeout=600,
    )
)
