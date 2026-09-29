# Judge workflow

Overview shows assigned/remaining/awaiting-response/recused counts, the next
unscored project with its room/table from the existing route, and a progress meter.
Review queue shows a scored-of-total meter, an assigned-project list (Next / status
badges) beside a work area: safe artifact inspector and rubric scoring. Scoring shows
criterion title, range, weight, anchors, score, comment, criteria-scored count,
autosave state, project position, previous/next, "Recuse or report a conflict"
(moves to the assignment response, where Decline records the recusal and reason),
Submit ballot and Submit and continue. Narrow screens stack list → evidence →
rubric with a "Jump to scoring" link and a sticky action bar.

Unchanged: draft autosave, offline outbox, submit semantics, assignment eligibility,
normalization and peer-score isolation (no peer data is fetched). The inspector still
renders only inspected static text/facts; links open with noopener and files remain
untrusted downloads.
