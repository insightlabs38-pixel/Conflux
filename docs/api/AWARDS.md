# Awards and prizes

Organizers create awards at `POST /api/v1/workspaces/{workspace}/events/{event}/awards/`. An award names its selection source (`manual`, `evaluation`, or `community`), winner count, optional eligible track, finalized submission requirement, stacking rule, and optional conflict group. Evaluation awards name a plan from the same event. `GET` on the same route lists award configuration, components, winners, and fulfillment state for organizers.

Add typed prize components at `POST .../awards/{award}/components/`. Cash components require a positive amount and three-letter currency; noncash components have no monetary amount. Components are never summed across types.

Use `GET .../awards/candidates/` to see all event projects as an organizer, including projects the organizer does not belong to. Select winners at `POST .../awards/{award}/winners/` with a project ID and optional `override_reason`. Selection checks event, track, submission, capacity, stacking, and conflict constraints in a transaction. Evaluation and community sources require published results. Selecting outside their ranking requires a recorded reason. Once all winner positions are filled, `POST .../awards/{award}/publish/` freezes the award. Public visitors can read published winners for a public event at `GET /api/v1/events/{event}/awards/`; internal evidence and override reasons are omitted.

Each winner and component pair has fulfillment state. Organizers advance it with `PATCH .../awards/{award}/fulfillments/{fulfillment}/` and `{ "state": "contacted" }`, then `verified`, `sent`, and finally `claimed` or `failed`. Failure requires a note. Invalid transitions are rejected. Fulfillment changes are audited.
