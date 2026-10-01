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

// Version comparison (PD-F002-B02-T05): two versions of a form are compared by field identity,
// and a configuration change shows the diff the server produced. Both are read-only views over
// existing history, but the spec creates a form and edits the event, so it runs on an isolated
// fixture.
const VISIBLE = ["participant", "judge", "organizer"]; // the form builder always sets this
const PITCH = {
  id: "pitch",
  type: "text",
  label: "Pitch",
  required: false,
  visible_to: VISIBLE,
};
const URL_FIELD = {
  id: "url",
  type: "url",
  label: "Repository",
  required: false,
  visible_to: VISIBLE,
};

for (const width of [390, 1440]) {
  test(`form versions and configuration changes are shown as diffs at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    await openWorkspace(page);
    const { workspace, event, name } = await eventIds(page);
    const base = `/api/v1/workspaces/${workspace}/events/${event}`;

    // A form with two published versions, and a draft that reorders and edits.
    const created = await page.request.post(`${base}/forms/`, {
      data: { name: `Diff demo ${width}` },
    });
    expect(created.status()).toBe(201);
    const form = (await created.json()).public_id as string;
    const put = (fields: unknown[]) =>
      page.request.put(`${base}/forms/${form}/`, {
        data: { schema: { fields } },
      });
    expect((await put([PITCH])).status()).toBe(200);
    expect(
      (await page.request.post(`${base}/forms/${form}/publish/`)).status(),
    ).toBe(201);
    expect(
      (await put([{ ...PITCH, label: "Your pitch" }, URL_FIELD])).status(),
    ).toBe(200);
    expect(
      (await page.request.post(`${base}/forms/${form}/publish/`)).status(),
    ).toBe(201);
    expect(
      (await put([URL_FIELD, { ...PITCH, label: "Your pitch" }])).status(),
    ).toBe(200);

    const writes: string[] = [];
    page.on("request", (request) => {
      if (request.method() !== "GET")
        writes.push(`${request.method()} ${request.url()}`);
    });

    await page.goto("/app/");
    await openWorkspace(page);
    await chooseWorkspaceEvent(page);
    await goToDestination(page, "setup");
    await goToTask(page, "Forms");
    await page.getByLabel("Edit form").selectOption(form);
    await page.getByText("Compare versions", { exact: true }).click();
    const compare = page.getByRole("region", { name: "Compare form versions" });
    await expect(compare).toBeVisible();
    // Version 2 against the draft: one field moved, nothing else.
    const diff = compare.getByRole("group", {
      name: "Changes from Version 2 to Current draft",
    });
    await expect(diff).toContainText("Moved");
    await expect(diff).toContainText("from position 2 to 1");
    // Version 1 against version 2: a label changed, a field added (by identity, not position).
    await compare.getByLabel("Compare").selectOption({ index: 0 });
    await compare.getByLabel("with").selectOption({ index: 1 });
    const first = compare.getByRole("group", {
      name: "Changes from Version 1 to Version 2",
    });
    await expect(first).toContainText("Changed");
    await expect(first).toContainText("fields › 0 › label");
    await expect(first).toContainText('"Your pitch"');
    await expect(first).toContainText("Added");
    await expect(first).toContainText("2 changes.");
    await noHorizontalOverflow(page);
    await accessible(page);

    // The same comparison from the API, uncached.
    const direct = await page.request.get(
      `/api/v1/workspaces/${workspace}/versions/form/diff/?event=${event}&form=${form}&older=draft&newer=draft`,
    );
    expect(direct.status()).toBe(200);
    expect(direct.headers()["cache-control"]).toContain("no-store");
    expect((await direct.json()).diff.total).toBe(0);

    // A configuration change shows its diff in the history.
    const renamed = `${name} (renamed)`;
    expect(
      (
        await page.request.patch(`${base}/`, { data: { name: renamed } })
      ).status(),
    ).toBe(200);
    await page.goto("/app/");
    await openWorkspace(page);
    await chooseWorkspaceEvent(page);
    await goToDestination(page, "operations");
    await goToTask(page, "Configuration history");
    await settled(page);
    const history = page
      .getByRole("group", { name: "Changes to name" })
      .first();
    await expect(history).toContainText("Changed");
    await expect(history).toContainText(JSON.stringify(renamed));
    await noHorizontalOverflow(page);
    await accessible(page);
    expect(writes).toEqual([]);
  });
}
