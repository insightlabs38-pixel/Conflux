"""Weighted rubric criteria schema and validation (JDG-002).

A rubric is a flat list of criteria, each independently weighted and
scored on its own [min_score, max_score] range; the overall score is the
weight-normalized average (weights need not sum to 1 -- see `weighted_score`).
"""

from django.core.exceptions import ValidationError

MAX_CRITERIA = 20


def clean_criteria(criteria) -> list[dict]:
    if not isinstance(criteria, list) or not criteria:
        raise ValidationError({"criteria": "At least one criterion is required."})
    if len(criteria) > MAX_CRITERIA:
        raise ValidationError({"criteria": f"At most {MAX_CRITERIA} criteria are allowed."})

    cleaned = []
    seen_ids = set()
    for raw in criteria:
        if not isinstance(raw, dict):
            raise ValidationError({"criteria": "Each criterion must be an object."})
        criterion_id = raw.get("id")
        name = raw.get("name")
        weight = raw.get("weight")
        min_score = raw.get("min_score")
        max_score = raw.get("max_score")
        anchors = raw.get("anchors", {})

        if not isinstance(criterion_id, str) or not criterion_id.strip():
            raise ValidationError({"criteria": "Each criterion needs a non-empty 'id'."})
        if criterion_id in seen_ids:
            raise ValidationError({"criteria": f"Duplicate criterion id: {criterion_id!r}."})
        seen_ids.add(criterion_id)
        if not isinstance(name, str) or not name.strip():
            raise ValidationError({"criteria": f"Criterion {criterion_id!r} needs a 'name'."})
        if not isinstance(weight, (int, float)) or isinstance(weight, bool) or weight <= 0:
            raise ValidationError(
                {"criteria": f"Criterion {criterion_id!r} needs a positive numeric 'weight'."}
            )
        if (
            not isinstance(min_score, (int, float))
            or not isinstance(max_score, (int, float))
            or isinstance(min_score, bool)
            or isinstance(max_score, bool)
            or min_score >= max_score
        ):
            raise ValidationError(
                {"criteria": f"Criterion {criterion_id!r} needs min_score < max_score."}
            )
        if not isinstance(anchors, dict) or any(
            not isinstance(k, str) or not isinstance(v, str) for k, v in anchors.items()
        ):
            raise ValidationError(
                {"criteria": f"Criterion {criterion_id!r} anchors must map text to text."}
            )
        cleaned.append(
            {
                "id": criterion_id,
                "name": name,
                "weight": weight,
                "min_score": min_score,
                "max_score": max_score,
                "anchors": anchors,
            }
        )
    return cleaned


def weighted_score(criteria: list[dict], scores: dict[str, float]) -> float:
    """Weight-normalized average of `scores` (criterion_id -> raw score)."""
    total_weight = sum(c["weight"] for c in criteria)
    return sum(c["weight"] * scores[c["id"]] for c in criteria) / total_weight
