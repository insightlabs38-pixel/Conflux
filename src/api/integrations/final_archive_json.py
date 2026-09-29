"""Portable identity paths in frozen evidence; arbitrary answer text stays opaque."""

from copy import deepcopy

from django.core.exceptions import ValidationError


def remap_json(label, field, value, *, pk, public):
    adapted = {
        ("evaluations.evaluationplan", "tie_breaks"),
        ("projects.submission", "draft_payload"),
        ("projects.submissionversion", "snapshot"),
        ("evaluations.normalizationrun", "evidence"),
        ("evaluations.pairwiserun", "evidence"),
        ("evaluations.assignmentversion", "evidence"),
        ("awards.awardwinner", "evidence"),
        ("deliberation.deliberationroom", "finalization"),
    }
    if (label, field) in adapted and not isinstance(value, dict):
        raise ValidationError(f"{label}.{field} must be an object.")
    result = deepcopy(value)
    project = "projects.project"
    user = "accounts.user"
    if label == "evaluations.evaluationplan" and field == "tie_breaks":
        return {str(pk(project, key)): score for key, score in result.items()}
    if label == "projects.submission" and field == "draft_payload":
        if "artifact_ids" in result:
            result["artifact_ids"] = [
                public("artifacts.artifact", ref) for ref in result["artifact_ids"]
            ]
    if label == "projects.submissionversion" and field == "snapshot":
        for key, table in (("project", project), ("stage", "stages.stage")):
            if key in result:
                result[key] = public(table, result[key])
        for entry in result.get("forms", []):
            entry["form"] = public("forms.formdefinition", entry["form"])
            entry["version"] = public("forms.formversion", entry["version"])
        for entry in result.get("artifacts", []):
            entry["id"] = public("artifacts.artifact", entry["id"])
        if "artifact_ids" in result.get("draft", {}):
            result["draft"]["artifact_ids"] = [
                public("artifacts.artifact", ref) for ref in result["draft"]["artifact_ids"]
            ]
    if label in {"evaluations.normalizationrun", "evaluations.pairwiserun"} and field == "evidence":
        for key, table in (
            ("projects", project),
            ("review_counts", project),
            ("judge_effects", user),
        ):
            if key in result:
                result[key] = {str(pk(table, ref)): entry for ref, entry in result[key].items()}
        if "low_information_judges" in result:
            result["low_information_judges"] = [
                str(pk(user, ref)) for ref in result["low_information_judges"]
            ]
        for entry in result.get("ballots", []):
            entry["project_id"] = pk(project, entry["project_id"])
            entry["judge_id"] = pk(user, entry["judge_id"])
            for key, table in (
                ("ballot", "evaluations.ballot"),
                ("judge", user),
                ("rubric_version", "evaluations.rubricversion"),
            ):
                entry[key] = public(table, entry[key])
    if label == "evaluations.assignmentversion" and field == "evidence":
        if "load_by_judge" in result:
            result["load_by_judge"] = {
                str(pk(user, ref)): count for ref, count in result["load_by_judge"].items()
            }
        if "cut_judges" in result.get("connectivity", {}):
            result["connectivity"]["cut_judges"] = [
                pk(user, ref) for ref in result["connectivity"]["cut_judges"]
            ]
    if label == "awards.awardwinner" and field == "evidence":
        for key, table in (
            ("plan", "evaluations.evaluationplan"),
            ("normalization_run", "evaluations.normalizationrun"),
            ("pairwise_run", "evaluations.pairwiserun"),
            ("voting_plan", "community.votingplan"),
        ):
            if key in result:
                result[key] = public(table, result[key])
        if "deliberation" in result:
            result["deliberation"]["room"] = public(
                "deliberation.deliberationroom", result["deliberation"]["room"]
            )
    if label == "deliberation.deliberationroom" and field == "finalization":
        if "winners" in result:
            result["winners"] = [public(project, ref) for ref in result["winners"]]
        for row in result.get("tally", []):
            row["project"] = public(project, row["project"])
    return result
