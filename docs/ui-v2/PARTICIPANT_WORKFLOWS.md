# Participant workflows

Overview uses the participant's real team, projects, finalized stage submissions,
eligibility findings and configured event deadline. Failed reads produce an error,
not zero counts. Returning to Overview refreshes the summary; leaving it clears an
in-flight loading state without overwriting drafts in the workspace.

Team separates roster/invitations from the people-first marketplace. Event resources
separate rules, sponsor challenges and attendance. The project workspace separates
story, evidence/preflight, event forms, submission, eligibility, support and
continuation. Native keyboard tabs retain mounted drafts and use explicit selected
state; narrow screens reorganize the task controls without horizontal overflow.

Story editing uses the existing project PATCH API. Evidence upload, validation,
preflight, form submission and draft revision/finalize semantics stay unchanged.
Submission can refresh its artifact choices without discarding notes. The server
continues to enforce policy, temporal, eligibility and frozen-evidence guarantees.

The signed receipt leads with project/event/stage/version/time/reference and the
existing drift-checked frozen judge-visible evidence. Artifact downloads disappear
when drift is reported. Claims, signature token and version/digest history remain
available through native disclosures; they are neither removed nor substituted.
Participant remediation keeps finding/severity/state, response and organizer decision
separate while retaining the existing respond/review protocol.

The existing Playwright lifecycle now enters the visible tasks explicitly, selects
the actual configured event identity, and edits the story before requesting review.
The existing single-worker harness also verifies retained drafts, keyboard controls,
readable receipts, axe and overflow at 390/768/1024/1440.
