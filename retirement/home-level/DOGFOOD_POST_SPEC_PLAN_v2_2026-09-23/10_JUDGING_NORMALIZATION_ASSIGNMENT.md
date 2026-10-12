# Judging, Assignment and Normalization Design

## EvaluationPlan
A plan defines candidate population, evaluator pool, assignment strategy, ballot strategy, aggregation strategy, visibility and completion rules. This supports rubric, community and later pairwise modes without schema forks.

## Assignment
Hard constraints: authorization/eligibility/conflicts. Objective terms: minimum review coverage, load balance, track/expertise fit, and overlap/connectivity sufficient for defensible cross-judge normalization.

## Fixture evidence
Released corpus: 41 projects, 30 judges, 8 tracks, 126 score records. Per-project review count ranges 2–5 (mean 3.07). Judge-project graph connected: True. Deliberate constant scorer: jdg_07 with mean score 4.0 across 3 reviews.

## Normalization family
Use a documented regularized additive judge-effect model rather than naïve per-judge z-scores:

`observed project review score = project effect + judge severity effect + residual`.

Estimate judge severity from overlap, with regularization/shrinkage toward zero for weakly supported judges. Normalize by removing the estimated severity before weighted aggregation. Criterion-level treatment must be explicit; weights belong to the rubric rather than being accidentally re-estimated.

## Required edge behavior
- constant scorers: no division-by-zero or arbitrary inflation;
- sparse judges: strong shrinkage / bounded influence;
- unequal review counts: aggregation remains valid;
- disconnected/weak assignment graph: surface inability/weakness rather than fabricate comparability;
- missing reviews: progress and result policies handle them explicitly;
- deterministic reruns on the same evidence.

## Normalization Proof
Provide fixture-backed raw → estimated judge effect → adjusted → final examples, parameters/regularization disclosure, edge cases and rank-change inspection. Never call the normalized ranking objectively true; present it as the configured documented method.

## Pairwise
Bradley–Terry is Stretch #1 through BallotStrategy/AggregationStrategy, not a parallel judging subsystem.
