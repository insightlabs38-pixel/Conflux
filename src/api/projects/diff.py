"""Compare immutable submission evidence by form and artifact identity."""


def _diff_dict(before: dict, after: dict) -> dict:
    added = {k: v for k, v in after.items() if k not in before}
    removed = {k: v for k, v in before.items() if k not in after}
    changed = {
        k: {"before": before[k], "after": after[k]}
        for k in before.keys() & after.keys()
        if before[k] != after[k]
    }
    return {"added": added, "removed": removed, "changed": changed}


def _has_changes(diff: dict) -> bool:
    return bool(diff.get("added") or diff.get("removed") or diff.get("changed"))


def _diff_draft(before: dict, after: dict) -> dict:
    before = dict(before or {})
    after = dict(after or {})
    before_ids = set(before.pop("artifact_ids", []) or [])
    after_ids = set(after.pop("artifact_ids", []) or [])
    result = _diff_dict(before, after)
    if before_ids != after_ids:
        result["artifact_ids"] = {
            "added": sorted(after_ids - before_ids),
            "removed": sorted(before_ids - after_ids),
        }
    return result


def _diff_forms(before: list, after: list) -> list[dict]:
    before_by_form = {entry["form"]: entry for entry in before}
    after_by_form = {entry["form"]: entry for entry in after}
    results = []
    for form_id in sorted(before_by_form.keys() | after_by_form.keys()):
        before_entry = before_by_form.get(form_id)
        after_entry = after_by_form.get(form_id)
        if before_entry is None:
            results.append(
                {
                    "form": form_id,
                    "status": "added",
                    "version": after_entry["version"],
                    "answers": after_entry["answers"],
                }
            )
            continue
        if after_entry is None:
            results.append(
                {
                    "form": form_id,
                    "status": "removed",
                    "version": before_entry["version"],
                    "answers": before_entry["answers"],
                }
            )
            continue
        answers_diff = _diff_dict(before_entry.get("answers", {}), after_entry.get("answers", {}))
        version_changed = before_entry.get("version") != after_entry.get("version")
        if _has_changes(answers_diff) or version_changed:
            change = {
                "form": form_id,
                "status": "changed",
                "version_changed": version_changed,
                "answers": answers_diff,
            }
            if version_changed:
                change["version"] = {
                    "before": before_entry.get("version"),
                    "after": after_entry.get("version"),
                }
            results.append(change)
    return results


def _diff_artifacts(before: list, after: list) -> dict:
    before_by_id = {entry["id"]: entry for entry in before}
    after_by_id = {entry["id"]: entry for entry in after}
    added_ids = sorted(after_by_id.keys() - before_by_id.keys())
    removed_ids = sorted(before_by_id.keys() - after_by_id.keys())
    changed_ids = sorted(
        i for i in before_by_id.keys() & after_by_id.keys() if before_by_id[i] != after_by_id[i]
    )
    return {
        "added": [after_by_id[i] for i in added_ids],
        "removed": [before_by_id[i] for i in removed_ids],
        "changed": {i: _diff_dict(before_by_id[i], after_by_id[i]) for i in changed_ids},
    }


def diff_snapshots(before: dict, after: dict) -> dict:
    """Return changed submission content and preflight evidence."""
    result = {}
    if before.get("project_name") != after.get("project_name"):
        result["project_name"] = {
            "before": before.get("project_name"),
            "after": after.get("project_name"),
        }
    draft_diff = _diff_draft(before.get("draft") or {}, after.get("draft") or {})
    if any(draft_diff.values()):
        result["draft"] = draft_diff
    forms_diff = _diff_forms(before.get("forms") or [], after.get("forms") or [])
    if forms_diff:
        result["forms"] = forms_diff
    artifacts_diff = _diff_artifacts(before.get("artifacts") or [], after.get("artifacts") or [])
    if any(artifacts_diff.values()):
        result["artifacts"] = artifacts_diff
    if before.get("preflight") != after.get("preflight"):
        result["preflight"] = {
            "before": before.get("preflight"),
            "after": after.get("preflight"),
        }
    return result
