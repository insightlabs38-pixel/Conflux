import copy
import json

import pytest
from accounts.models import User
from awards.models import Award, SelectionSource
from django.core.exceptions import ValidationError
from events.models import BasePrize, Event, EventStatus, Track
from forms.models import FormDefinition, FormVersion
from integrations.archive import FORMAT_VERSION, build_archive, import_archive
from policies.models import Action, Policy, PolicyBinding, TemporalGate
from projects.models import Project
from stages.models import ParticipationMode, Stage, StageTransition
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def make_event(workspace=None, name="Source Event", slug="source-event"):
    workspace = workspace or Workspace.objects.create(name="Archives", slug="archives")
    event = Event.objects.create(workspace=workspace, name=name, slug=slug, description="An event.")
    track_a = Track.objects.create(
        event=event, name="Hardware", description="Physical builds", position=0
    )
    track_b = Track.objects.create(event=event, name="Software", position=1)
    BasePrize.objects.create(
        event=event,
        track=track_a,
        name="Grand Prize",
        kind=BasePrize.Kind.CASH,
        amount="500.00",
        currency="USD",
    )
    stage_submit = Stage.objects.create(
        event=event,
        name="Submission",
        position=0,
        is_initial=True,
        participation_mode=ParticipationMode.TEAM_FORMATION,
    )
    stage_judging = Stage.objects.create(
        event=event,
        name="Judging",
        position=1,
        participation_mode=ParticipationMode.TEAM_LOCKED,
    )
    StageTransition.objects.create(from_stage=stage_submit, to_stage=stage_judging)
    form = FormDefinition.objects.create(
        event=event, stage=stage_submit, name="Submission form", draft_schema={"fields": []}
    )
    FormVersion.objects.create(
        definition=form, number=1, schema={"fields": [{"id": "title", "type": "text"}]}
    )
    policy = Policy.objects.create(event=event, name="Submit window", ast={"op": "true"})
    PolicyBinding.objects.create(event=event, action=Action.SUBMIT, policy=policy)
    TemporalGate.objects.create(event=event, name="Judging window")
    award = Award.objects.create(
        event=event,
        name="Best Overall",
        eligibility_track=track_b,
        selection_source=SelectionSource.MANUAL,
        winner_count=1,
    )
    from awards.models import PrizeComponent, PrizePackage

    package = PrizePackage.objects.create(award=award, name=award.name)
    PrizeComponent.objects.create(
        package=package, kind="cash", name="Cash", quantity=1, amount="100.00", currency="USD"
    )
    creator = User.objects.create_user(username="builder", password="unused")
    Project.objects.create(event=event, track=track_b, name="Widget", created_by=creator)
    return workspace, event


def test_export_is_deterministic_and_versioned():
    _workspace, event = make_event()
    first = build_archive(event, mode="config")
    second = build_archive(event, mode="config")
    assert first == second
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["format_version"] == FORMAT_VERSION
    assert "projects" not in first


def test_config_mode_omits_projects_full_mode_includes_them():
    _workspace, event = make_event()
    config = build_archive(event, mode="config")
    full = build_archive(event, mode="full")
    assert "projects" not in config
    assert [p["name"] for p in full["projects"]] == ["Widget"]
    assert full["projects"][0]["created_by_username"] == "builder"


def test_roundtrip_config_is_semantically_equivalent():
    _workspace, event = make_event()
    exported = build_archive(event, mode="config")

    imported_event = import_archive(
        workspace=_workspace, archive=exported, name="Cloned Event", slug="cloned-event"
    )
    reexported = build_archive(imported_event, mode="config")

    assert _normalize(exported) == _normalize(reexported)
    # The clone is independent: a fresh, unpublished draft with its own refs.
    assert imported_event.status == EventStatus.DRAFT
    assert imported_event.pk != event.pk
    assert reexported["event"]["name"] == "Cloned Event"
    assert reexported["tracks"][0]["ref"] != exported["tracks"][0]["ref"]


def test_roundtrip_full_carries_projects():
    workspace, event = make_event()
    exported = build_archive(event, mode="full")

    imported_event = import_archive(
        workspace=workspace, archive=exported, name="Cloned Full", slug="cloned-full"
    )
    reexported = build_archive(imported_event, mode="full")

    assert _normalize(exported) == _normalize(reexported)
    assert Project.objects.filter(event=imported_event, name="Widget").exists()


def test_import_rejects_unsupported_format_version():
    workspace, event = make_event()
    archive = build_archive(event, mode="config")
    archive["format_version"] = 99
    with pytest.raises(ValidationError):
        import_archive(workspace=workspace, archive=archive, name="X", slug="x")


def test_import_rejects_dangling_reference():
    workspace, event = make_event()
    archive = build_archive(event, mode="config")
    archive["base_prizes"][0]["track_ref"] = "not-a-real-ref"
    with pytest.raises(ValidationError):
        import_archive(workspace=workspace, archive=archive, name="X", slug="x")


def test_import_rejects_missing_user_in_full_mode():
    workspace, event = make_event()
    archive = build_archive(event, mode="full")
    archive["projects"][0]["created_by_username"] = "no-such-user"
    with pytest.raises(ValidationError):
        import_archive(workspace=workspace, archive=archive, name="X", slug="x")


def test_import_rejects_missing_required_sections():
    with pytest.raises(ValidationError):
        import_archive(
            workspace=Workspace.objects.create(name="W", slug="w"),
            archive={"mode": "config"},
            name="X",
            slug="x",
        )


def test_import_does_not_bypass_domain_validation():
    workspace, event = make_event()
    archive = build_archive(event, mode="config")
    # Cash prizes require a positive amount; corrupt the archive to try to
    # smuggle one through without it.
    archive["base_prizes"][0]["amount"] = None
    with pytest.raises(ValidationError):
        import_archive(workspace=workspace, archive=archive, name="X", slug="x")


def _normalize(archive):
    """Semantic-equivalence comparator for roundtrip tests: refs are
    per-document identities, not stable values, so canonicalize each one to
    a positional token (in first-seen order) before comparing. Also drops
    `event.name`/`event.slug`, which the importer is deliberately given a
    caller-supplied value for.
    """
    archive = copy.deepcopy(archive)
    archive["event"].pop("name", None)
    archive["event"].pop("slug", None)

    counter = {"n": 0}
    seen = {}

    def token(ref):
        if ref not in seen:
            seen[ref] = f"REF{counter['n']}"
            counter["n"] += 1
        return seen[ref]

    def walk(node):
        if isinstance(node, dict):
            return {
                key: (
                    token(value)
                    if key
                    in (
                        "ref",
                        "from_ref",
                        "to_ref",
                        "track_ref",
                        "stage_ref",
                        "policy_ref",
                        "eligibility_track_ref",
                    )
                    and value is not None
                    else walk(value)
                )
                for key, value in node.items()
            }
        if isinstance(node, list):
            return [walk(item) for item in node]
        return node

    return walk(archive)
