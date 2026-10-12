# Open Organizer Clarifications

## C1 — T3/T4 checker behavior (highest priority)
The released `run.py` contains no T3/T4 checks and therefore cannot mark T3/T4 verified using its current ladder algorithm. Ask whether these tiers are intentionally manually judged and a `claimed but not verified` line is expected, or whether a revised checker will be published.

## C2 — Signed judge record verification expectations
Clarify whether any signature/format/key-discovery convention is expected beyond publicly verifiable semantics. Architecture should remain generic until answered.

## C3 — Offline external links/integrations
The platform itself must function offline; optional Git/repo/video/integration validators should fail gracefully or defer rather than make hosted services mandatory.

None of these blocks the architecture or Core implementation.
