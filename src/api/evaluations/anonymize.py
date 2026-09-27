"""Blind judging (S06): a deterministic, judge-independent pseudonym for a
candidate, computed on the fly rather than persisted -- nothing to keep in
sync if candidates change, and every judge (and organizer, comparing notes)
sees the same label for the same project under the same plan.

Scoped to project identity only: no institution/affiliation field exists
on Project/Team to redact, and this is the one identity signal the product
actually exposes to a judge during live judging (see CandidateListView).
Inventing a new identity field just to redact it would violate the frozen
architecture constraint for a capability nothing else in the product uses.
"""

import hashlib


def anonymized_label(plan_id: int, project_public_id) -> str:
    digest = hashlib.sha256(f"{plan_id}:{project_public_id}".encode()).hexdigest()[:8].upper()
    return f"Candidate {digest}"
