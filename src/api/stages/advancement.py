"""AdvancementStrategy registry and core strategies (ST-003).

A strategy decides *which subjects* advance out of a stage; it knows
nothing about how their scores were computed (judging/evaluations land in
a later batch) or about persisting the move (see `advance_stage` below,
which is the one place that actually mutates StageEntry rows and records
the decision as an audited AuditEvent — "decisions are explicit/audited"
per the stage/policy plan doc).
"""

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import ClassVar

from audit.services import record_mutation
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Stage, StageEntry, StageTransition


@dataclass(frozen=True)
class Candidate:
    subject_type: str
    subject_id: str
    score: float | None = None
    track_id: str | None = None


REGISTRY: dict[str, type["AdvancementStrategy"]] = {}


class AdvancementStrategy:
    slug: ClassVar[str]

    def select(self, candidates: list[Candidate], **params) -> set[tuple[str, str]]:
        """Return the (subject_type, subject_id) pairs that advance."""
        raise NotImplementedError

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        REGISTRY[cls.slug] = cls


def _key(candidate):
    return (candidate.subject_type, candidate.subject_id)


class ManualStrategy(AdvancementStrategy):
    """The organizer picks explicitly; no scoring involved."""

    slug = "manual"

    def select(self, candidates, *, selected=(), **params):
        selected_set = set(selected)
        return {_key(c) for c in candidates if _key(c) in selected_set}


class EveryoneStrategy(AdvancementStrategy):
    slug = "everyone"

    def select(self, candidates, **params):
        return {_key(c) for c in candidates}


class TopNStrategy(AdvancementStrategy):
    slug = "top_n"

    def select(self, candidates, *, n, **params):
        ranked = sorted(candidates, key=lambda c: (-(c.score or 0), c.subject_id))
        return {_key(c) for c in ranked[:n]}


class ThresholdStrategy(AdvancementStrategy):
    slug = "threshold"

    def select(self, candidates, *, minimum, **params):
        return {_key(c) for c in candidates if (c.score or 0) >= minimum}


class PercentileStrategy(AdvancementStrategy):
    """`percentile` is the share of candidates kept, by score: percentile=25
    keeps the top 25% (rounded up, so a nonempty field always keeps at
    least one candidate).
    """

    slug = "percentile"

    def select(self, candidates, *, percentile, **params):
        if not candidates:
            return set()
        if not 0 < percentile <= 100:
            raise ValidationError("percentile must be between 0 (exclusive) and 100.")
        keep_count = math.ceil(len(candidates) * percentile / 100)
        ranked = sorted(candidates, key=lambda c: (-(c.score or 0), c.subject_id))
        return {_key(c) for c in ranked[:keep_count]}


class TopNPerTrackStrategy(AdvancementStrategy):
    slug = "top_n_per_track"

    def select(self, candidates, *, n, **params):
        by_track = defaultdict(list)
        for c in candidates:
            by_track[c.track_id].append(c)
        selected = set()
        for track_candidates in by_track.values():
            ranked = sorted(track_candidates, key=lambda c: (-(c.score or 0), c.subject_id))
            selected.update(_key(c) for c in ranked[:n])
        return selected


class PassFailStrategy(AdvancementStrategy):
    """A candidate passes at or above `minimum` — same shape as threshold,
    kept as its own named strategy because "pass/fail" is how organizers
    and the plan doc describe this specific use (e.g. a qualifying round),
    not a percentile or ranked cut.
    """

    slug = "pass_fail"

    def select(self, candidates, *, minimum, **params):
        return {_key(c) for c in candidates if (c.score or 0) >= minimum}


class ExternalResultStrategy(AdvancementStrategy):
    """The advancement decision was made outside this system (an external
    qualifier, a manually-entered result) and is only being recorded here.
    """

    slug = "external"

    def select(self, candidates, *, advancing=(), **params):
        advancing_set = set(advancing)
        return {_key(c) for c in candidates if _key(c) in advancing_set}


def advance_stage(stage: Stage, to_stage: Stage, strategy_slug: str, candidates, *, actor, params):
    """Run a strategy, then persist and audit the result: exit each
    advancing subject's StageEntry in `stage` and open a new one in
    `to_stage`. Subjects not selected are left exactly where they are —
    this only ever moves people forward, never drops them silently.
    """
    if strategy_slug not in REGISTRY:
        raise ValidationError(f"Unknown advancement strategy: {strategy_slug!r}")
    if not StageTransition.objects.filter(from_stage=stage, to_stage=to_stage).exists():
        raise ValidationError("No transition exists from this stage to the requested stage.")

    strategy = REGISTRY[strategy_slug]()
    selected = strategy.select(list(candidates), **params)

    with transaction.atomic():
        now = timezone.now()
        advanced = []
        for subject_type, subject_id in selected:
            entry = StageEntry.objects.filter(
                stage=stage,
                subject_type=subject_type,
                subject_id=subject_id,
                exited_at__isnull=True,
            ).first()
            if entry is None:
                continue
            entry.exited_at = now
            entry.save(update_fields=["exited_at"])
            StageEntry.objects.enter(to_stage, subject_type, subject_id)
            advanced.append({"subject_type": subject_type, "subject_id": subject_id})

        record_mutation(
            actor=actor,
            workspace=stage.event.workspace,
            action="stage.advanced",
            target=stage,
            metadata={
                "strategy": strategy_slug,
                "params": params,
                "to_stage": str(to_stage.public_id),
                "candidate_count": len(candidates),
                "advanced": advanced,
            },
        )

    return advanced
