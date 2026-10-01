import { expect, test } from "@playwright/test";
import {
  accessible,
  eventIds,
  goToTask,
  noHorizontalOverflow,
  openWorkspace,
  settled,
  signIn,
} from "./support";

// Durable background jobs (PD-F002-B01-T05): an archive export runs on the real worker, is
// followed to its end in the page, stays listed with its download, and is visible only to those
// who may see it. It writes, so it runs on an isolated fixture.
for (const width of [390, 1440]) {
  test(`an archive export runs as a background job and stays downloadable at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    await openWorkspace(page);
    const { workspace, event } = await eventIds(page);
    const api = `/api/v1/workspaces/${workspace}`;
    const before = await (
      await page.request.get(`${api}/jobs/?event=${event}`)
    ).json();

    await page.goto(`/app/w/${workspace}/operations?event=${event}`);
    await settled(page);
    await goToTask(page, "Exports and jobs");
    const panel = page.locator(".cx-card").filter({
      has: page.getByRole("heading", { name: "Exports and background jobs" }),
    });
    await expect(panel).toBeVisible();
    await noHorizontalOverflow(page);

    await panel
      .getByRole("form", { name: "Export the event archive" })
      .getByLabel("What to export")
      .selectOption("config");
    await panel.getByRole("button", { name: "Start export" }).click();
    await expect(page.getByText("The export is ready.")).toBeVisible({
      timeout: 30_000,
    });
    const link = panel.getByRole("link", {
      name: /^Download .*-archive\.json$/,
    });
    await expect(link).toBeVisible();

    // The file is the same document the synchronous export serves.
    const href = (await link.getAttribute("href"))!;
    const file = await page.request.get(href);
    expect(file.status()).toBe(200);
    expect(file.headers()["content-disposition"]).toContain("attachment");
    const expected = await (
      await page.request.get(`${api}/events/${event}/archive/?mode=config`)
    ).json();
    expect(await file.json()).toEqual(expected);

    // It stays on the record after the page is gone.
    await page.reload();
    await settled(page);
    await goToTask(page, "Exports and jobs");
    const row = page
      .getByRole("region", { name: "Recent background jobs" })
      .locator("tbody tr")
      .first();
    await expect(row).toContainText("Event archive export");
    await expect(row).toContainText("succeeded");
    await expect(row.getByRole("link")).toBeVisible();
    const after = await (
      await page.request.get(`${api}/jobs/?event=${event}`)
    ).json();
    expect(after).toHaveLength(before.length + 1);
    expect(after[0]).toMatchObject({
      kind: "archive_export",
      status: "succeeded",
    });
    await accessible(page);
    await noHorizontalOverflow(page);

    // Jobs are not public: a signed-out client cannot see this job or its output.
    const stranger = await page.context().browser()!.newContext();
    const anonymous = await stranger.request.get(
      `${api}/jobs/${after[0].public_id}/`,
    );
    expect([401, 403]).toContain(anonymous.status());
    await stranger.close();
  });
}
