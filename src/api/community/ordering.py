"""Randomized-but-stable candidate ordering (COM-002).

A global fixed order would bias voters toward whichever candidate happens
to be listed first. Storing a persisted shuffle per voter would work but is
unnecessary state: hashing (voter_key, candidate_id) together gives the
same property -- each voter sees a consistent order across reloads, but
different voters see different orders -- without writing anything down.
"""

import hashlib


def _sort_key(voter_key: str, candidate_id) -> str:
    return hashlib.sha256(f"{voter_key}:{candidate_id}".encode()).hexdigest()


def ordered_candidates(candidates, voter_key: str) -> list:
    return sorted(candidates, key=lambda candidate: _sort_key(voter_key, candidate.public_id))
