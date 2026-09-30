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

// Presets to custom workflows (PD-F001-B01-T06): an event created from a format follows it until the
// organizer changes the stages; the Stages tab says what is still the format's and what is custom,
// and changing it back restores the answer. Nothing is locked or reset on the way. Mutating, so it
// runs on an isolated fixture.
for (const width of [390, 1440]) {
  test(`stages say whether they still follow the format at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    await openWorkspace(page);
    const { workspace } = await eventIds(page);
    const stamp = Date.now();
    const created = await page.request.post(
      `/api/v1/workspaces/${workspace}/event-templates/library/hackathon/instantiate/`,
      {
        data: {
          name: `Flow ${width} ${stamp}`,
          slug: `flow-${width}-${stamp}`,
          starts_at: "2027-03-05T09:00:00Z",
          timezone: "UTC",
        },
      },
    );
    expect(created.status()).toBe(201);
    const event = (await created.json()).public_id as string;
    const base = `/api/v1/workspaces/${workspace}/events/${event}`;
    const source = async () =>
      (await (await page.request.get(`${base}/workflow/`)).json()).source;

    expect(await source()).toBe("preset");
    await page.goto(`/app/w/${workspace}/setup?event=${event}`);
    await settled(page);
    await goToTask(page, "Stages");
    const status = page.getByRole("region", { name: "Workflow source" });
    await expect(status).toContainText("Follows the format");

    // Add a stage through the same endpoint the builder uses: only that becomes custom.
    const added = await page.request.post(`${base}/stages/`, {
      data: { name: "Demo day", participation_mode: "team_locked" },
    });
    expect(added.status()).toBe(201);
    await status.getByRole("button", { name: "Check again" }).click();
    await expect(status).toContainText("Customized");
    await expect(status).toContainText("Stage 'Demo day' was added.");
    expect(await source()).toBe("custom");

    // Taking it out again returns to the format.
    const demo = (await added.json()).public_id as string;
    expect((await page.request.delete(`${base}/stages/${demo}/`)).ok()).toBe(
      true,
    );
    await status.getByRole("button", { name: "Check again" }).click();
    await expect(status).toContainText("Follows the format");
    await noHorizontalOverflow(page);
    await accessible(page);
  });
}
