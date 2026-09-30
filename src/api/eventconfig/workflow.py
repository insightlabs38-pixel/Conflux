"""Whether an event still follows its format's workflow (PD-F001-B01).

A format preset declares a stage flow, which stages are judged and with which criteria. Nothing is
stored about "custom": the stages, transitions and plans are ordinary rows the organizer can edit
freely, and this compares them with the preset baseline to say what is still the format's and what
has been changed. Editing never resets or blocks anything; it only changes the answer here.
"""

from evaluations.models import EvaluationPlan
from stages.models import Stage, StageTransition

from .models import EventProfile
from .presets import get_preset

SOURCES = ("preset", "custom", "none")


def _criteria_key(criteria):
    return sorted(
        (c.get("id"), c.get("weight"), c.get("min_score"), c.get("max_score")) for c in criteria
    )


def _current(event):
    stages = list(Stage.objects.filter(event=event).order_by("position", "id"))
    by_id = {stage.pk: stage.name for stage in stages}
    transitions = {
        (by_id[t.from_stage_id], by_id[t.to_stage_id])
        for t in StageTransition.objects.filter(from_stage__event=event)
        if t.from_stage_id in by_id and t.to_stage_id in by_id
    }
    plans = {}
    for plan in EvaluationPlan.objects.filter(stage__event=event).select_related("stage"):
        version = plan.current_rubric_version
        plans.setdefault(plan.stage.name, []).append(
            _criteria_key(version.criteria if version else plan.draft_criteria)
        )
    return {
        "stages": [s.name for s in stages],
        "initial": [s.name for s in stages if s.is_initial],
        "transitions": transitions,
        "plans": plans,
    }


def _differences(preset, current):
    baseline_stages = list(preset.stages)
    out = []
    names = current["stages"]
    for name in baseline_stages:
        if name not in names:
            out.append({"code": "stage_removed", "message": f"Stage '{name}' was removed."})
    for name in names:
        if name not in baseline_stages:
            out.append({"code": "stage_added", "message": f"Stage '{name}' was added."})
    shared = [n for n in names if n in baseline_stages]
    if shared != [n for n in baseline_stages if n in names]:
        out.append({"code": "stages_reordered", "message": "The stages were reordered."})
    if set(current["initial"]) != {baseline_stages[0]}:
        out.append(
            {"code": "initial_changed", "message": "The starting stage is not the format's."}
        )
    chain = set(zip(baseline_stages, baseline_stages[1:]))
    if current["transitions"] != chain:
        out.append(
            {
                "code": "transitions_changed",
                "message": "The flow between stages differs from the format's.",
            }
        )
    judged = {
        baseline_stages[i]: [_criteria_key([c.as_json() for c in preset.criteria])]
        for i in preset.judging_stages
    }
    for stage_name in judged:
        if stage_name not in current["plans"]:
            out.append(
                {"code": "plan_removed", "message": f"Judging was removed from '{stage_name}'."}
            )
    for stage_name, plans in current["plans"].items():
        if stage_name not in judged:
            out.append({"code": "plan_added", "message": f"Judging was added to '{stage_name}'."})
        elif plans != judged[stage_name]:
            out.append(
                {
                    "code": "rubric_changed",
                    "message": f"Judging on '{stage_name}' differs from the format's criteria.",
                }
            )
    return out


def workflow_state(event):
    """`source` is preset (unchanged), custom (started from a format, since changed) or none
    (no format: built by hand)."""
    profile = EventProfile.objects.filter(event=event).first()
    preset = get_preset(profile.preset_key) if profile else None
    current = _current(event)
    body = {
        "source": "none",
        "preset": None,
        "stages": current["stages"],
        "differences": [],
    }
    if preset is None:
        return body
    differences = _differences(preset, current)
    body["preset"] = {"key": preset.key, "version": profile.preset_version, "label": preset.label}
    body["source"] = "custom" if differences else "preset"
    body["differences"] = differences
    return body
