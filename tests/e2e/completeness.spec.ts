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
    await event.getByText("Provided", { exact: true }).last().click();
    await expect(
      event.getByText("check:events.models.Event.clean"),
    ).toBeVisible();
    await expect(
      event.getByText("A blank record is refused for: name, slug, workspace"),
    ).toBeVisible();
    // A feature without a state machine says how its records change.
    const track = table.locator("tbody tr").filter({
      has: page.getByRole("rowheader", { name: /^Track \(track\)/ }),
    });
    await track.getByText("No states").click();
    await expect(track).toContainText("Edited in place and deleted");
    await panel.getByText(/properties are not checked yet/).click();
    await expect(panel.getByText("Event-as-Code")).toBeVisible();
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
