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

// Provenance (PD-F002-B02-T07): an export says what it was made from and by whom, a downloaded
// file can be checked against the digest recorded for it, and a configuration restore records
// where it came from. It runs a real export and a real restore, so it uses an isolated fixture.
for (const width of [390, 1440]) {
  test(`an export and a restore show their provenance at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    await openWorkspace(page);
    const { workspace, event, name } = await eventIds(page);
    const api = `/api/v1/workspaces/${workspace}`;

    // An export runs on the real worker; its job record carries the envelope.
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
    const jobs = await (
      await page.request.get(`${api}/jobs/?event=${event}`)
    ).json();
    const job = jobs[0];
    const made = job.result.provenance;
    expect(made.source).toEqual({ kind: "archive_export", id: job.public_id });
    expect(made.inputs.refs[0]).toMatchObject({ kind: "event", id: event });
    const file = job.artifacts[0].name as string;
    const bytes = await (
      await page.request.get(`${api}/jobs/${job.public_id}/artifacts/${file}/`)
    ).body();

    await page.reload();
    await settled(page);
    await goToTask(page, "Exports and jobs");
    const row = page
      .getByRole("region", { name: "Recent background jobs" })
      .locator("tbody tr")
      .first();
    await row.getByText("Provenance", { exact: true }).click();
    const view = row.getByRole("region", { name: /^Provenance of / });
    await expect(view).toContainText("archive of");
    await expect(view).toContainText("event_archive");
    await expect(view).toContainText(made.output.sha256);
    await noHorizontalOverflow(page);
    await accessible(page);

    // The downloaded file is exactly what the record describes; an altered one is not.
    const check = view.getByLabel("Check a downloaded file");
    await check.setInputFiles({
      name: file,
      mimeType: "application/json",
      buffer: bytes,
    });
    await expect(view.getByRole("status")).toHaveText(
      "This is exactly the file recorded here.",
    );
    await check.setInputFiles({
      name: file,
      mimeType: "application/json",
      buffer: Buffer.concat([bytes, Buffer.from(" ")]),
    });
    await expect(view.getByRole("status")).toHaveText(
      "This is not the file recorded here.",
    );

    // A restore records where it came from.
    const renamed = `${name} (provenance)`;
    expect(
      (
        await page.request.patch(`${api}/events/${event}/`, {
          data: { name: renamed },
        })
      ).status(),
    ).toBe(200);
    await page.goto("/app/");
    await openWorkspace(page);
    await chooseWorkspaceEvent(page);
    await goToDestination(page, "operations");
    await goToTask(page, "Configuration history");
    await settled(page);
    await page
      .getByRole("button", { name: "Restore before values" })
      .first()
      .click();
    await page.getByRole("button", { name: "Confirm restore" }).click();
    await expect(page.getByText(/Configuration restored/)).toBeVisible();
    const restored = page
      .locator(".cx-config-history > li")
      .filter({ hasText: "event.restored" })
      .first();
    await restored.getByText("Provenance", { exact: true }).click();
    const record = restored.getByRole("region", {
      name: "Provenance of event.restored",
    });
    await expect(record).toContainText("Restored 1 field of Event");
    await expect(record).toContainText("restore_before_values (version 1)");
    await expect(record).toContainText("1 change (1 changed)");
    await accessible(page);
    expect(
      (await (await page.request.get(`${api}/events/${event}/`)).json()).name,
    ).toBe(name);
  });
}
