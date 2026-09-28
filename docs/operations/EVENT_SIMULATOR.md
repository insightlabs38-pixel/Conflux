# Dry-run event simulator

Run this standalone command with the application's database settings and required secrets:

```sh
uv run --frozen python src/api/manage.py simulate_event EVENT_PUBLIC_ID PLAN_PUBLIC_ID \
  --participants 2 --judges 2
```

The event must be draft and have no operational projects. The selected plan must belong to the event and use standard rubric scoring with all judges. Counts are bounded to 1–10. `--at` accepts a timezone-aware ISO timestamp; the default is just after the later of now and event start. Event status is temporarily open, while a clock confined to this standalone process supplies that timestamp. Dates, temporal gates, policies, registration settings, published forms and rubric criteria keep their configured values.

Synthetic identities replay the actual session-authenticated API: registration, organizer approval for pending applications, project creation, draft save, finalization, rubric publication if needed, ballots, normalization, results publication and result readback. Invite-only registration creates a temporary invitation. A configured judge pool receives the synthetic judges temporarily. The resulting ranking must cover every synthetic project.

The JSON report lists real response statuses, the simulation time, temporary overlays and the resulting ranking or first blocker. A blocked scenario exits unsuccessfully. All database changes, audit/outbox rows and on-commit callbacks are rolled back before returning, including on unexpected errors. Report IDs identify ephemeral records and cannot be queried later. PostgreSQL sequences may advance despite rollback.

This is a database/application rehearsal, not a browser, network or external-service availability test. It does not upload files, process objects, send notifications or run workers. The blank submission scenario reports missing required form answers/artifacts as blockers. Capacity/waitlist, deadline and policy failures retain their real behavior. Pairwise, assigned-subset, prize and calibration plans fail explicitly rather than receiving a modified configuration. Existing operational projects also fail explicitly; use a draft template clone to rehearse an event that already contains them. No live-mode or commit option exists.
