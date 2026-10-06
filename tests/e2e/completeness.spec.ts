import { expect, test } from "@playwright/test";
import {
  accessible,
  chooseWorkspaceEvent,
  eventIds,
  goToDestination,
  goToTask,
  noHorizontalOverflow,
  openWorkspace,
  settled,
  signIn,
} from "./support";

// Completeness (PD-F003-B01-T01): an organizer sees which features provide what, with each
// feature's identity and lifecycle, checked against the running system; nothing can be changed.
for (const width of [390, 1440]) {
  test(`the completeness report is read-only and consistent at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    await openWorkspace(page);
    const { workspace } = await eventIds(page);

    const writes: string[] = [];
    page.on("request", (request) => {
      if (request.method() !== "GET")
        writes.push(`${request.method()} ${request.url()}`);
    });

    await page.goto("/app/");
    await openWorkspace(page);
    await chooseWorkspaceEvent(page);
    await goToDestination(page, "operations");
    await goToTask(page, "Completeness");
    await settled(page);
    const panel = page.locator(".cx-card").filter({
      has: page.getByRole("heading", { name: "Completeness" }),
    });
    await expect(panel.getByRole("status")).toContainText("Consistent");
    const table = panel.getByRole("region", {
      name: "Features and what they provide",
    });
    await expect(table.locator("tbody tr")).toHaveCount(15);
    const event = table.locator("tbody tr").filter({
      has: page.getByRole("rowheader", { name: /^Event \(event\)/ }),
    });
    await expect(event).toContainText("Provided · public id (public_id)");
    await expect(event).toContainText("Draft, Open, Closed, Archived");
    // A lifecycle opens to the transitions the code allows.
    await event.getByText("Draft, Open, Closed, Archived").click();
    await expect(event.getByText("Draft → Open")).toBeVisible();
    await expect(event.getByText("Closed → Archived")).toBeVisible();
    // Validation is checked too: where it is enforced, a test that proves it, and what the model shows.
    await expect(
      table.getByRole("columnheader", { name: "Validation and invariants" }),
    ).toBeVisible();
    await event.getByText("Provided", { exact: true }).first().click();
    await expect(
      event.getByText("check:events.models.Event.clean"),
    ).toBeVisible();
    await expect(
      event.getByText("A blank record is refused for: name, slug, workspace"),
    ).toBeVisible();
    // Authorization is held against the permission matrix: who reads, who changes, where it is scoped.
    await expect(
      table.getByRole("columnheader", { name: "Authorization and scope" }),
    ).toBeVisible();
    await event.getByText("Provided", { exact: true }).nth(1).click();
    await expect(event.getByText("route:event-status")).toBeVisible();
    await expect(
      event.getByText("Who can change: admin,organizer"),
    ).toBeVisible();
    await expect(
      event.getByText("Scoped through: Event → Workspace"),
    ).toBeVisible();
    // Audit is derived from the code: each change a feature accepts and the action it records.
    await expect(
      table.getByRole("columnheader", { name: "Audit events" }),
    ).toBeVisible();
    await event.getByText("Provided", { exact: true }).nth(2).click();
    await expect(
      event.getByText("write:event-status:POST=event.status_changed"),
    ).toBeVisible();
    await expect(
      event.getByText("Audited changes: POST event-list: event.created", {
        exact: false,
      }),
    ).toBeVisible();
    // Idempotency: what sending a change twice does, per change, derived and proved.
    await expect(
      table.getByRole("columnheader", { name: "Idempotency and concurrency" }),
    ).toBeVisible();
    await event.getByText("Provided", { exact: true }).nth(3).click();
    await expect(
      event.getByText("mode:event-status:POST=natural"),
    ).toBeVisible();
    await expect(
      event.getByText("When sent twice: POST event-list: unique", {
        exact: false,
      }),
    ).toBeVisible();
    // REST: the lists and records the OpenAPI document describes, and how a list is paged.
    await expect(
      table.getByRole("columnheader", { name: "REST representation" }),
    ).toBeVisible();
    await event.getByText("Provided", { exact: true }).nth(4).click();
    await expect(event.getByText("list:event-list")).toBeVisible();
    await expect(
      event.getByText("Lists: GET event-list: array of Event"),
    ).toBeVisible();
    // Generated SDKs: each operation of the feature and the type the clients give it.
    await expect(
      table.getByRole("columnheader", { name: "Generated SDK" }),
    ).toBeVisible();
    await event.getByText("Provided", { exact: true }).nth(5).click();
    await expect(event.getByText("generated:typescript")).toBeVisible();
    await expect(
      event.getByText("Operations in both SDKs: GET event-list: Event[]", {
        exact: false,
      }),
    ).toBeVisible();
    // Search: a registered query entity with its fields, or why there is none.
    await expect(
      table.getByRole("columnheader", { name: "Search and filter fields" }),
    ).toBeVisible();
    await event.getByText("Provided", { exact: true }).nth(6).click();
    await expect(
      event.getByText(
        "Why not: read whole through the workspace's event list",
        {
          exact: false,
        },
      ),
    ).toBeVisible();
    const application = table.locator("tbody tr").filter({
      has: page.getByRole("rowheader", {
        name: /^Registration application \(application\)/,
      }),
    });
    await application.getByText("Provided", { exact: true }).nth(6).click();
    await expect(
      application.getByText("Query: entity applications"),
    ).toBeVisible();
    await expect(
      application.getByText(
        "status (enum, filter, sort, scan within one event)",
      ),
    ).toBeVisible();
    // Base UI: the screen that reads the feature, its test, and an owed screen with its owner.
    await expect(
      table.getByRole("columnheader", { name: "Base UI" }),
    ).toBeVisible();
    await event.getByText("Provided", { exact: true }).nth(7).click();
    await expect(
      event.getByText("Screens: EventDashboard.tsx", { exact: false }),
    ).toBeVisible();
    const notice = table.locator("tbody tr").filter({
      has: page.getByRole("rowheader", {
        name: /^Announcement \(announcement\)/,
      }),
    });
    await expect(notice).toContainText("Planned");
    // Advanced UI: the shared components a screen uses, or why a feature has nothing beyond its base.
    await expect(
      table.getByRole("columnheader", { name: "Advanced UI" }),
    ).toBeVisible();
    await event.getByText("Provided", { exact: true }).nth(8).click();
    await expect(
      event.getByText(
        "Shared components: ConsequenceDialog in EventDashboard.tsx",
        {
          exact: false,
        },
      ),
    ).toBeVisible();
    const trackRow = table.locator("tbody tr").filter({
      has: page.getByRole("rowheader", { name: /^Track \(track\)/ }),
    });
    await trackRow.getByText("Provided", { exact: true }).nth(8).click();
    await expect(
      trackRow.getByText("Advanced: none beyond the base screen", {
        exact: false,
      }),
    ).toBeVisible();
    // Bulk operations: the planner actions a feature takes part in, or why a batch does not fit.
    await expect(
      table.getByRole("columnheader", { name: "Bulk operations" }),
    ).toBeVisible();
    const project = table.locator("tbody tr").filter({
      has: page.getByRole("rowheader", { name: /^Project \(project\)/ }),
    });
    await project.getByText("Provided", { exact: true }).nth(9).click();
    await expect(
      project.getByText("Bulk actions: move (Move projects to a track)", {
        exact: false,
      }),
    ).toBeVisible();
    await expect(project).toContainText("records project.track_moved");
    await expect(
      table.locator("tbody tr").filter({
        has: page.getByRole("rowheader", { name: /^Registration application/ }),
      }),
    ).toContainText("Planned");
    // CLI: the commands that administer a feature, or why the terminal has nothing for it.
    await expect(
      table.getByRole("columnheader", { name: "CLI" }),
    ).toBeVisible();
    await event.getByText("Provided", { exact: true }).nth(10).click();
    await expect(
      event.getByText("Commands: conflux-admin events list", { exact: false }),
    ).toBeVisible();
    // MCP: the tools an agent can call for a feature, each one an existing route.
    await expect(
      table.getByRole("columnheader", { name: "MCP" }),
    ).toBeVisible();
    const stage = table.locator("tbody tr").filter({
      has: page.getByRole("rowheader", { name: /^Stage \(stage\)/ }),
    });
    await stage.getByText("Provided", { exact: true }).nth(11).click();
    await expect(
      stage.getByText("Tools: list_stages (read): GET stage-list", {
        exact: false,
      }),
    ).toBeVisible();
    // Event-as-Code: the document sections a feature owns, or why it is runtime data.
    await expect(
      table.getByRole("columnheader", { name: "Event-as-Code" }),
    ).toBeVisible();
    await trackRow.getByText("Provided", { exact: true }).nth(12).click();
    await expect(
      trackRow.getByText("Document sections: tracks: events.Track", {
        exact: false,
      }),
    ).toBeVisible();
    // Webhooks and the outbox: which audited changes subscribers receive and which stay silent.
    await expect(
      table.getByRole("columnheader", { name: "Webhooks and outbox" }),
    ).toBeVisible();
    await trackRow.getByText("Provided", { exact: true }).nth(13).click();
    await expect(
      trackRow.getByText("Sent to subscribers: track.created → track.created", {
        exact: false,
      }),
    ).toBeVisible();
    // Archive and import: the table a feature travels in, how it is reached and which fields go.
    await expect(
      table.getByRole("columnheader", { name: "Archive and import" }),
    ).toBeVisible();
    await trackRow.getByText("Provided", { exact: true }).nth(14).click();
    await expect(
      trackRow.getByText("Archived tables: events.track: reached by event", {
        exact: false,
      }),
    ).toBeVisible();
    // Analytics: the summary section that counts a feature and the measures it owns.
    await expect(
      table.getByRole("columnheader", { name: "Analytics dimensions" }),
    ).toBeVisible();
    const team = table.locator("tbody tr").filter({
      has: page.getByRole("rowheader", { name: /^Team \(team\)/ }),
    });
    await team.getByText("Provided", { exact: true }).nth(15).click();
    await expect(
      team.getByText("Summary section: teams", { exact: false }),
    ).toBeVisible();
    await expect(
      team.getByText("Measures: teams.total", { exact: false }),
    ).toBeVisible();
    // Privacy: what happens to a person's rows, kept as evidence or erased, per feature.
    await expect(
      table.getByRole("columnheader", { name: "Retention and privacy" }),
    ).toBeVisible();
    await team.getByText("Provided", { exact: true }).nth(16).click();
    await expect(
      team.getByText("Kept as evidence: team_memberships", { exact: false }),
    ).toBeVisible();
    // Extension hooks: the registrations an app offers, typed in the SDK or in code only.
    await expect(
      table.getByRole("columnheader", { name: "Extension hooks" }),
    ).toBeVisible();
    await stage.getByText("Provided", { exact: true }).nth(17).click();
    await expect(
      stage.getByText("Hooks: advancement_strategy", { exact: false }),
    ).toBeVisible();
    // Versions and migration: immutable versions, counters and what a version can be compared with.
    await expect(
      table.getByRole("columnheader", { name: "Version and migration" }),
    ).toBeVisible();
    const form = table.locator("tbody tr").filter({
      has: page.getByRole("rowheader", { name: /^Form \(form\)/ }),
    });
    await form.getByText("Provided", { exact: true }).nth(18).click();
    await expect(
      form.getByText("Immutable versions: forms.FormVersion", { exact: false }),
    ).toBeVisible();
    // A feature without a state machine says how its records change.
    const track = table.locator("tbody tr").filter({
      has: page.getByRole("rowheader", { name: /^Track \(track\)/ }),
    });
    await track.getByText("No states").click();
    await expect(track).toContainText("Edited in place and deleted");
    // Fixtures: whether the demo scenario creates the feature, and who owes it when it does not.
    await expect(
      table.getByRole("columnheader", { name: "Test fixtures and scenarios" }),
    ).toBeVisible();
    await trackRow.getByText("Provided", { exact: true }).nth(19).click();
    await expect(
      trackRow.getByText("Created by the demo scenario: hackathon", {
        exact: false,
      }),
    ).toBeVisible();
    const message = table.locator("tbody tr").filter({
      has: page.getByRole("rowheader", { name: /^Message \(message\)/ }),
    });
    await expect(message).toContainText("PD-S061-B02-T01");
    // Every property of the contract is checked: nothing is left pending.
    await expect(panel.getByText(/properties are not checked yet/)).toHaveCount(
      0,
    );
    await expect(panel.getByRole("button")).toHaveCount(0);
    await noHorizontalOverflow(page);
    await accessible(page);

    // The API is the same report, uncached, and read-only.
    const direct = await page.request.get(
      `/api/v1/workspaces/${workspace}/completeness/`,
    );
    expect(direct.status()).toBe(200);
    expect(direct.headers()["cache-control"]).toContain("no-store");
    const body = await direct.json();
    expect(body.ok).toBe(true);
    expect(body.problems).toEqual([]);
    expect(body.features).toHaveLength(15);
    expect(
      (
        await page.request.post(`/api/v1/workspaces/${workspace}/completeness/`)
      ).status(),
    ).toBe(405);
    expect(writes).toEqual([]);
  });
}
