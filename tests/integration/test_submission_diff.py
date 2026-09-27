from projects.diff import diff_snapshots


def snapshot(*, project_name="P", notes="hi", artifact_ids=None, forms=None, artifacts=None):
    return {
        "project_name": project_name,
        "draft": {"notes": notes, "artifact_ids": artifact_ids or []},
        "forms": forms or [],
        "artifacts": artifacts or [],
    }


def test_identical_snapshots_produce_an_empty_diff():
    a = snapshot()
    assert diff_snapshots(a, a) == {}


def test_project_name_change_is_reported():
    before = snapshot(project_name="Old")
    after = snapshot(project_name="New")
    assert diff_snapshots(before, after) == {"project_name": {"before": "Old", "after": "New"}}


def test_draft_field_change_is_reported():
    before = snapshot(notes="draft one")
    after = snapshot(notes="draft two")
    diff = diff_snapshots(before, after)
    assert diff["draft"]["changed"] == {"notes": {"before": "draft one", "after": "draft two"}}


def test_artifact_id_set_change_is_order_independent():
    before = snapshot(artifact_ids=["a", "b"])
    after = snapshot(artifact_ids=["b", "a"])
    assert diff_snapshots(before, after) == {}  # same set, different order -- no real change

    after_added = snapshot(artifact_ids=["a", "b", "c"])
    diff = diff_snapshots(before, after_added)
    assert diff["draft"]["artifact_ids"] == {"added": ["c"], "removed": []}


def test_form_answer_change_is_reported_per_field_not_as_an_opaque_swap():
    before = snapshot(
        forms=[{"form": "f1", "version": "v1", "answers": {"q1": "old", "q2": "same"}}]
    )
    after = snapshot(
        forms=[{"form": "f1", "version": "v1", "answers": {"q1": "new", "q2": "same"}}]
    )
    diff = diff_snapshots(before, after)
    assert diff["forms"] == [
        {
            "form": "f1",
            "status": "changed",
            "version_changed": False,
            "answers": {
                "added": {},
                "removed": {},
                "changed": {"q1": {"before": "old", "after": "new"}},
            },
        }
    ]


def test_republishing_a_form_with_identical_answers_is_not_reported_as_changed():
    before = snapshot(forms=[{"form": "f1", "version": "v1", "answers": {"q1": "same"}}])
    after = snapshot(forms=[{"form": "f1", "version": "v2", "answers": {"q1": "same"}}])
    diff = diff_snapshots(before, after)
    assert diff["forms"][0]["version_changed"] is True
    assert diff["forms"][0]["version"] == {"before": "v1", "after": "v2"}


def test_preflight_change_is_reported_even_when_authored_content_is_unchanged():
    before = snapshot()
    after = snapshot()
    before["preflight"] = {"status": "PASS", "checks": []}
    after["preflight"] = {"status": "WARNING", "checks": [{"code": "link_warning"}]}
    assert diff_snapshots(before, after)["preflight"] == {
        "before": before["preflight"],
        "after": after["preflight"],
    }


def test_added_and_removed_artifacts_are_reported():
    before = snapshot(artifacts=[{"id": "a1", "kind": "repository", "title": "Repo"}])
    after = snapshot(
        artifacts=[
            {"id": "a1", "kind": "repository", "title": "Repo"},
            {"id": "a2", "kind": "live_url", "title": "Demo"},
        ]
    )
    diff = diff_snapshots(before, after)
    assert diff["artifacts"]["added"] == [{"id": "a2", "kind": "live_url", "title": "Demo"}]
    assert diff["artifacts"]["removed"] == []


def test_changed_artifact_fields_are_reported_by_id():
    before = snapshot(artifacts=[{"id": "a1", "kind": "repository", "title": "Old title"}])
    after = snapshot(artifacts=[{"id": "a1", "kind": "repository", "title": "New title"}])
    diff = diff_snapshots(before, after)
    assert diff["artifacts"]["changed"]["a1"]["changed"] == {
        "title": {"before": "Old title", "after": "New title"}
    }


def test_reordering_a_list_without_content_changes_is_not_reported():
    before = snapshot(artifacts=[{"id": "a1", "title": "One"}, {"id": "a2", "title": "Two"}])
    after = snapshot(artifacts=[{"id": "a2", "title": "Two"}, {"id": "a1", "title": "One"}])
    assert diff_snapshots(before, after) == {}
