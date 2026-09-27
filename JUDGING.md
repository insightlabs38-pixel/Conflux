# Judging

Judging runs on `EvaluationPlan` (per stage): a candidate type, a pool
strategy, a weighted rubric, and the judges who score against it. See
`src/api/evaluations/` for the implementation; this document is the
normalization method's defense (NORM-006) -- what it does, what it
assumes, and where it's known to fall short.

## Assignment

Each plan draws judges from an `EvaluationPool`. Under `all_judges`, every
non-conflicted judge reviews every candidate. Under `assigned_subset`, a
deterministic greedy algorithm (`evaluations/assignment.py`) picks the
least-loaded eligible judges per candidate, then a repair pass
(`evaluations/connectivity.py`) tries to stitch the resulting judge-overlap
graph into one connected component -- normalization below is only
meaningful across judges who share at least an indirect chain of common
candidates. Repair tries alternate components and both bridge directions
when a conflict blocks its first choice. For a single candidate, it keeps
the coverage/track-fit assignment because there is no cross-project ranking
to calibrate. `ConflictOfInterest` is a hard constraint throughout: excluded
from assignment, and rejected outright if a ballot is attempted anyway.

## Normalization method

**Model.** Each ballot's aggregate score (its rubric's declared weights
applied to the judge's per-criterion scores -- see "Aggregation" below) is
modeled as:

    observed(judge, project) ~= grand_mean + project_effect[project] + judge_effect[judge]

`project_effect` is the quality signal the whole system exists to recover,
so it's left unregularized. `judge_effect` is ridge-regularized toward
zero: a judge who reviewed few candidates, or who (in a weakly-connected
assignment graph) has little information tying their scale to the rest of
the pool, gets a small, cautious correction rather than an overconfident
one built on noise.

**Solving it.** Alternating (Gauss-Seidel) updates: hold judge effects
fixed and recompute each project's effect as the unregularized mean
residual; hold project effects fixed and recompute each judge's effect as
`sum(residuals) / (n_reviews + ridge_lambda)`. Iterate in a fixed, sorted
order (never randomized) until the largest single-value change drops below
a tolerance, capped at a fixed maximum iteration count. Same input, same
output, always -- see `evaluations/normalization.py::estimate_judge_effects`.

**Aggregation.** A ballot's aggregate score always uses the weights frozen
into *that ballot's own* `RubricVersion` (`evaluations/rubric.py::weighted_score`),
never the plan's current draft or latest published weights, and never a
weighting numerically re-derived from the score data itself. Republishing
a rubric with different weights can never retroactively change what an
already-cast ballot meant (NORM-002).

**Persistence.** Computing a run freezes an immutable `NormalizationRun`
(NORM-004), carrying the full raw -> adjusted -> final trace per project in
`evidence`: each project's raw (unadjusted) mean score alongside its
normalized final score, every judge's estimated effect, iteration count,
and convergence status. Re-running normalization creates a new numbered
run; it never mutates a previous one.

## Assumptions

- Judge bias is additive and roughly constant across the candidates a
  given judge reviews (a purely additive model; it does not attempt to
  model per-criterion or per-candidate-difficulty judge behavior).
- Enough judges review enough overlapping candidates for the ridge-anchored
  estimates to be meaningful comparisons, not just independent shrinkage
  toward zero. C-B15's connectivity repair exists specifically to keep this
  assumption realistic.
- A judge's raw scores are otherwise honest evidence (no distinct fraud/
  abuse detection here -- that's a different concern from bias correction).

## Known limitations

- **Weak bridges are diagnosed, not fixed.** `connectivity.cut_vertices`
  reports a judge whose removal would disconnect the graph, but the
  assignment repair only guarantees *one* connected component, not
  2-edge-connectivity; a single cut judge can still be the sole link
  between two halves of the pool.
- **No track-conditional bias.** A judge's effect is a single scalar across
  every candidate they reviewed, even though `PoolMembership.track_expertise`
  and `Project.track` exist; a judge who is harsh specifically on one track
  and lenient on another is not distinguished from a uniformly harsh judge.
- **Ridge lambda is a fixed input, not tuned.** The default (1.0) is a
  reasonable, deterministic choice, not the output of cross-validation
  against this event's own data -- there usually isn't enough data per
  event to do that reliably.
- **Fixture-backed proof, not a formal guarantee.** NORM-005's tests
  (`tests/integration/normalization/test_fixture_proof.py`) verify real
  properties (convergence, finiteness, an actual change versus raw means,
  sparse-judge shrinkage) against the official 30-judge/41-project/126-score
  corpus, but that is empirical evidence on one dataset, not a proof the
  method behaves well on every possible score distribution.
