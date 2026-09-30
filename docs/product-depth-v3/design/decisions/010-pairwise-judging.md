# D-010 · Pairwise judging
**Status**: accepted (r2) — supersedes the "split the centre pane" note. Foundation design closed (r2.1).
- Dedicated layout: pair queue | aligned A/B evidence (linked scroll, sticky frozen labels, structured-field facts) | decision panel.
- Decisions: A/B; tie only if configured (cap shown, disabled with reason when forced-choice); skip; recuse from A or B; one key press saves with 10 s undo and auto-advance.
- Criterion context is one line; no dual rubrics. Nothing is coloured better/worse. Order randomised per judge.
- Adaptive counts are shown honestly (12 of 40, range 34–46) with "why this pair?".
- Hybrid: rubric → close-call detection → tiebreak pairs; rubric scores of A/B hidden during tiebreak; feeds only the tiebreaker row in Deliberation.
- Narrow: <768 A/B/Compare tabs + sticky decision bar; 768–1023 two columns + docked bar.
**Refs**: Pairwise-Compare, Pairwise-States, Pairwise-Narrow.

## Product-policy items moved to the judging spec (r2.1)
Not foundation-design blockers; decided in the judging/product specification, not here:
- default tie-share cap (the fixture shows "≤ 20 %" only as an example configured value);
- whether strength-of-preference ships (the fixture shows "Off (binary choice)").
The UI is already parameterised for them: tie button present/absent/disabled-with-reason, the cap and remaining ties shown when configured, and the read-only method summary (Pairwise-States §6) lists whatever the event configured. Adding strength would add one control row to the decision panel without changing the layout.
