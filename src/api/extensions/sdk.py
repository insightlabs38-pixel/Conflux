from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypedDict

from artifacts.validators import ValidationResult, inspect_artifact, validate_artifact
from evaluations.assignment import Pairing
from integrations.archive import build_archive, import_archive
from integrations.migration_preview import preview_archive_import
from presentation.block_types import normalize_config
from presentation.blocks import clean_config
from stages.advancement import AdvancementStrategy, Candidate, advance_stage

if TYPE_CHECKING:
    from artifacts.models import Artifact
    from artifacts.storage import S3Storage
    from evaluations.models import EvaluationPlan
    from events.models import Event
    from workspaces.models import Workspace

SDK_VERSION = 1


class ArtifactValidator(Protocol):
    def __call__(self, artifact: Artifact, storage: S3Storage | None) -> ValidationResult: ...


class AssignmentStrategy(Protocol):
    def __call__(self, plan: EvaluationPlan, *, coverage: int = 3) -> list[Pairing]: ...


class PageBlockType(TypedDict):
    title: str
    schema: dict


class ArchiveImporter(Protocol):
    def __call__(self, *, workspace: Workspace, archive: dict, name: str, slug: str) -> Event: ...


class ArchiveConverter(Protocol):
    def __call__(self, archive: dict, csv_text: str, mapping: dict[str, str]) -> dict: ...


class ArchiveExporter(Protocol):
    def __call__(
        self, event: Event, mode: str = "config", sections: list[str] | None = None
    ) -> dict: ...


__all__ = [
    "SDK_VERSION",
    "AdvancementStrategy",
    "Candidate",
    "advance_stage",
    "ArtifactValidator",
    "ValidationResult",
    "inspect_artifact",
    "validate_artifact",
    "AssignmentStrategy",
    "Pairing",
    "PageBlockType",
    "normalize_config",
    "clean_config",
    "ArchiveImporter",
    "ArchiveConverter",
    "ArchiveExporter",
    "build_archive",
    "import_archive",
    "preview_archive_import",
]
