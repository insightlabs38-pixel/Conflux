from evaluations.assignment import Pairing
from evaluations.connectivity import (
    connectivity_report,
    cut_vertices,
    overlap_graph,
    repair_connectivity,
)


def P(judge_id, project_id):
    return Pairing(judge_id=judge_id, project_id=project_id)


def test_overlap_graph_links_judges_who_share_a_candidate():
    pairs = [P(1, 100), P(2, 100), P(3, 200)]
    graph = overlap_graph(pairs)
    assert graph[1] == {2}
    assert graph[2] == {1}
    assert graph[3] == set()


def test_connectivity_report_detects_a_single_connected_component():
    pairs = [P(1, 100), P(2, 100), P(2, 200), P(3, 200)]
    report = connectivity_report(pairs, [1, 2, 3])
    assert report.connected
    assert report.component_count == 1
    assert report.component_sizes == [3]
    assert report.isolated_judges == 0


def test_connectivity_report_detects_disconnection_and_isolation():
    pairs = [P(1, 100), P(2, 200)]  # no shared candidate at all
    report = connectivity_report(pairs, [1, 2])
    assert not report.connected
    assert report.component_count == 2
    assert report.isolated_judges == 2


def test_single_judge_pool_is_trivially_connected():
    report = connectivity_report([P(1, 100)], [1])
    assert report.connected
    assert report.component_count == 1


def test_cut_vertex_is_found_on_a_weak_bridge_graph():
    # 1-2 overlap via 100; 2-3 overlap via 200; only judge 2 links the halves.
    pairs = [P(1, 100), P(2, 100), P(2, 200), P(3, 200)]
    assert cut_vertices(overlap_graph(pairs), [1, 2, 3]) == [2]


def test_repair_connectivity_stitches_two_disjoint_pairs_deterministically():
    pairs = [P(1, 100), P(2, 200)]
    load = {1: 1, 2: 1}
    repaired, extra = repair_connectivity(pairs, judge_ids=[1, 2], load=load, conflicts=set())
    assert extra == 1
    report = connectivity_report(repaired, [1, 2])
    assert report.connected

    # Same inputs -> same repair, every time.
    again, extra_again = repair_connectivity(
        [P(1, 100), P(2, 200)], judge_ids=[1, 2], load={1: 1, 2: 1}, conflicts=set()
    )
    assert (repaired, extra) == (again, extra_again)


def test_repair_connectivity_gives_up_gracefully_when_every_bridge_is_conflicted():
    pairs = [P(1, 100), P(2, 200)]
    load = {1: 1, 2: 1}
    # The only possible bridge (judge 1 also reviewing 200) is conflicted out.
    repaired, extra = repair_connectivity(
        pairs, judge_ids=[1, 2], load=load, conflicts={(1, 200), (2, 100)}
    )
    assert extra == 0
    assert repaired == pairs
    assert not connectivity_report(repaired, [1, 2]).connected
