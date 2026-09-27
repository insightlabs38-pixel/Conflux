from community.ordering import ordered_candidates


class FakeProject:
    def __init__(self, public_id):
        self.public_id = public_id


def test_order_is_stable_for_the_same_voter():
    candidates = [FakeProject("a"), FakeProject("b"), FakeProject("c")]
    first = [p.public_id for p in ordered_candidates(candidates, "voter-1")]
    second = [p.public_id for p in ordered_candidates(candidates, "voter-1")]
    assert first == second


def test_different_voters_can_see_different_orders():
    candidates = [FakeProject(str(i)) for i in range(20)]
    orders = {
        tuple(p.public_id for p in ordered_candidates(candidates, f"voter-{i}")) for i in range(10)
    }
    # Overwhelmingly unlikely all 10 distinct voters land on the identical
    # permutation of 20 items if the ordering is actually voter-dependent.
    assert len(orders) > 1


def test_ordering_is_a_permutation_never_drops_or_duplicates():
    candidates = [FakeProject(str(i)) for i in range(15)]
    ordered = ordered_candidates(candidates, "voter-x")
    assert sorted(p.public_id for p in ordered) == sorted(p.public_id for p in candidates)
