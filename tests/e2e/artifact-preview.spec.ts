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

// Safe previews (PD-F002-B02-T03): the output of a background job opens as a preview built by the
// server (what it is, what the checks found, an excerpt as text) with the existing download left
// in place, and nothing is saved by looking. It runs a real export job, so it runs on an
// isolated fixture. The reviewer's inspector, the other adopter, is covered by the lifecycle canary.
for (const width of [390, 1440]) {
  test(`a job's output previews safely at ${width}`, async ({ page }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    await openWorkspace(page);
    const { workspace, event } = await eventIds(page);
    const api = `/api/v1/workspaces/${workspace}`;

    await page.goto(`/app/w/${workspace}/operations?event=${event}`);
    await settled(page);
    await goToTask(page, "Exports and jobs");
    const panel = page.locator(".cx-card").filter({
      has: page.getByRole("heading", { name: "Exports and background jobs" }),
    });
    await panel
      .getByRole("form", { name: "Export the event archive" })
      .getByLabel("What to export")
      .selectOption("config");
    await panel.getByRole("button", { name: "Start export" }).click();
    await expect(page.getByText("The export is ready.")).toBeVisible({
      timeout: 30_000,
    });

    // Nothing is inspected until it is asked for, and looking writes nothing.
    const writes: string[] = [];
    page.on("request", (request) => {
      if (request.method() !== "GET")
        writes.push(`${request.method()} ${request.url()}`);
    });
    const open = panel.getByRole("button", {
      name: /^Preview .*-archive\.json$/,
    });
    await open.first().click();
    const excerpt = panel.locator("pre.cx-artifact__preview").first();
    await expect(excerpt).toBeVisible();
    await expect(excerpt).toContainText("{");
    await expect(panel.getByText(/^Data · /).first()).toBeVisible();
    await expect(panel.getByText("Detected type: text").first()).toBeVisible();
    await expect(
      panel.getByRole("link", { name: /^Download .*-archive\.json$/ }),
    ).toHaveCount(1);
    await noHorizontalOverflow(page);
    await accessible(page);

    // The API gave the same answer, derived and uncached.
    const jobs = await (
      await page.request.get(`${api}/jobs/?event=${event}`)
    ).json();
    const job = jobs[0];
    const name = job.artifacts[0].name;
    const direct = await page.request.get(
      `${api}/previews/job_output/?job=${job.public_id}&name=${encodeURIComponent(name)}`,
    );
    expect(direct.status()).toBe(200);
    expect(direct.headers()["cache-control"]).toContain("no-store");
    expect(await direct.json()).toMatchObject({
      kind: "data",
      state: "ready",
      name,
    });
    const missing = await page.request.get(
      `${api}/previews/job_output/?job=${job.public_id}&name=nope.json`,
    );
    expect(missing.status()).toBe(404);
    expect(writes).toEqual([]);

    // Closing it removes it.
    await panel
      .getByRole("button", { name: /^Hide preview of .*-archive\.json$/ })
      .first()
      .click();
    await expect(excerpt).toHaveCount(0);
  });
}
