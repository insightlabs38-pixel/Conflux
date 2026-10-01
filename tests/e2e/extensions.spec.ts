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

// Extensions inventory (PD-F002-B02-T08): an organizer sees what this deployment's code provides
// and that its declarations agree with the live registries; nobody can change anything from it.
for (const width of [390, 1440]) {
  test(`the extensions inventory is read-only and consistent at ${width}`, async ({
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
    await goToTask(page, "Extensions");
    await settled(page);
    const panel = page.locator(".cx-card").filter({
      has: page.getByRole("heading", { name: "Extensions" }),
    });
    await expect(panel.getByRole("status")).toContainText("Consistent");
    const sources = panel.getByRole("region", { name: "Extension sources" });
    await expect(sources).toContainText("Platform core");
    await expect(sources).toContainText("Public pages");
    // A capability opens to its entries and who declared them.
    await panel.getByText(/^Page block \(\d+\)/).click();
    await expect(panel.getByText("hero)", { exact: false })).toBeVisible();
    await expect(
      panel.getByText(/^Archive exporter \(\d+\) · declared only/),
    ).toBeVisible();
    await expect(panel.getByRole("button")).toHaveCount(0);
    await noHorizontalOverflow(page);
    await accessible(page);

    // The API is the same inventory, uncached, and read-only.
    const direct = await page.request.get(
      `/api/v1/workspaces/${workspace}/extensions/`,
    );
    expect(direct.status()).toBe(200);
    expect(direct.headers()["cache-control"]).toContain("no-store");
    const body = await direct.json();
    expect(body.ok).toBe(true);
    expect(body.problems).toEqual([]);
    expect(
      (
        await page.request.post(`/api/v1/workspaces/${workspace}/extensions/`)
      ).status(),
    ).toBe(405);
    expect(writes).toEqual([]);
  });
}
