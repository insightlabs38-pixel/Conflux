# Judging replay, audit capsule and decision explanations

All under `.../stages/<s>/evaluation-plans/<p>/`.

## Replay — `GET runs/<run>/replay/[?timeline=true]` (organizer)

Feeds a run's frozen ballots back through the same solver and compares grand mean, solver trace, judge effects, project raw/final scores, per-ballot adjusted scores and the ranking. It then checks the frozen ballots against the ballots that exist now: **changed** responses, **missing** ballots and ballots that predate the run but were **omitted**. The response carries a `verdict` (`verified`/`mismatch`), the digest of the inputs and of the report itself; two replays of a run are identical. `timeline=true` adds up to 20 checkpoints showing the top three as ballots arrived. Pairwise runs replay from the comparisons recorded before the run (their evidence stores outputs only).

## Audit capsule — `GET audit-capsule/` (organizer)

A signed envelope (the archive signer: checksums plus Ed25519 signature) holding the published rubric versions, every counted ballot with its authored responses, judge effects, results with tie-breaks, award winners with evidence, eligibility rulings and the replay verdict. Judges are pseudonymous (`J01`…) and projects have stable labels; exports are audited.

```sh
python scripts/verify_capsule.py capsule.json --public-key record-key.pem
```

The public key is served by `GET /api/v1/records/verification-key/`. The script needs no server or database: it checks the checksums and signature, recomputes each ballot's weighted score from its responses, re-solves the normalization, and confirms the ranking order and award evidence. Any edit — even one that re-computes the checksums — fails the signature check. Without `--public-key`, integrity is checked but authenticity is reported as not established.

## Explanation — `GET explain/<project>/`

A deterministic account built from the frozen run: rank, raw versus adjusted score, what the judge-bias adjustment did, the rank without it, ties, and per-criterion averages. Organizers also get per-judge lines and the projects immediately above and below. A project's own members get the aggregated version (no judge lines, no rival names) once the plan's results are visible to participants; other participants get 404, judges 403.
