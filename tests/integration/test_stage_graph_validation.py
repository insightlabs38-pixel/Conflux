import pytest
from events.models import Event
from stages.graph import StageGraphError, topological_order, validate_event_graph
from stages.models import Stage, StageTransition
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def make_event(name="Dogfood"):
    workspace = Workspace.objects.create(name=f"{name} Workspace", slug=name.lower())
    return Event.objects.create(workspace=workspace, name=name, slug=name.lower())


def make_stage(event, name, **kwargs):
    return Stage.objects.create(event=event, name=name, **kwargs)


def test_topological_order_respects_a_linear_chain():
    event = make_event()
    a = make_stage(event, "A", is_initial=True)
    b = make_stage(event, "B")
    c = make_stage(event, "C")
    StageTransition.objects.create(from_stage=a, to_stage=b)
    StageTransition.objects.create(from_stage=b, to_stage=c)

    assert topological_order(event) == [a, b, c]


def test_topological_order_tie_breaks_by_position_then_id_not_insertion_order():
    event = make_event()
    # Created out of position order on purpose.
    second = make_stage(event, "Second", position=2, is_initial=True)
    first = make_stage(event, "First", position=1, is_initial=True)
    # Both are roots (no incoming edges); the tie must break on `position`.
    assert topological_order(event) == [first, second]


def test_topological_order_raises_on_a_cycle_created_via_bulk_create():
    """bulk_create skips StageTransition.clean() entirely — this is the
    real hazard a bulk graph-replace endpoint (ST-005) would hit, not a
    hypothetical.
    """
    event = make_event()
    a = make_stage(event, "A", is_initial=True)
    b = make_stage(event, "B")
    StageTransition.objects.bulk_create(
        [
            StageTransition(from_stage=a, to_stage=b),
            StageTransition(from_stage=b, to_stage=a),
        ]
    )
    with pytest.raises(StageGraphError):
        topological_order(event)


def test_validate_event_graph_passes_for_a_well_formed_graph():
    event = make_event()
    a = make_stage(event, "A", is_initial=True)
    b = make_stage(event, "B")
    StageTransition.objects.create(from_stage=a, to_stage=b)
    validate_event_graph(event)  # must not raise


def test_validate_event_graph_requires_at_least_one_initial_stage():
    event = make_event()
    make_stage(event, "A")
    with pytest.raises(StageGraphError, match="initial stage"):
        validate_event_graph(event)


def test_validate_event_graph_rejects_an_orphan_stage():
    event = make_event()
    make_stage(event, "A", is_initial=True)
    make_stage(event, "Unreachable")
    with pytest.raises(StageGraphError, match="Unreachable"):
        validate_event_graph(event)


def test_validate_event_graph_rejects_a_cycle_from_bulk_create():
    event = make_event()
    a = make_stage(event, "A", is_initial=True)
    b = make_stage(event, "B")
    StageTransition.objects.bulk_create(
        [
            StageTransition(from_stage=a, to_stage=b),
            StageTransition(from_stage=b, to_stage=a),
        ]
    )
    with pytest.raises(StageGraphError):
        validate_event_graph(event)
