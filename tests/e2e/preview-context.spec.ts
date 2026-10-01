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

// Preview as a person, version or time (PD-F002-B03-T01): an organizer sees a saved form as a
// participant, a judge or the public would, at a kept version or as of a time, with the sentence
// that says so and a way back to live. The spec creates a form with two published versions, so it
// runs on an isolated fixture.
const ALL = ["participant", "judge", "organizer"];
const field = (id: string, label: string, visible_to = ALL) => ({
  id,
  type: "text",
  label,
  required: false,
  visible_to,
});

for (const width of [390, 1440]) {
  test(`a saved form is previewed as a person, version or time at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    await openWorkspace(page);
    const { workspace, event } = await eventIds(page);
    const base = `/api/v1/workspaces/${workspace}/events/${event}`;
    const name = `Preview demo ${width}`;

    const created = await page.request.post(`${base}/forms/`, {
      data: { name },
    });
    expect(created.status()).toBe(201);
    const form = (await created.json()).public_id as string;
    const put = (fields: unknown[]) =>
      page.request.put(`${base}/forms/${form}/`, {
        data: { schema: { fields } },
      });
    expect(
      (
        await put([
          field("pitch", "Pitch"),
          field("repo", "Repository", ["participant"]),
        ])
      ).status(),
    ).toBe(200);
    expect(
      (await page.request.post(`${base}/forms/${form}/publish/`)).status(),
    ).toBe(201);
    expect(
      (
        await put([
          field("pitch", "Pitch"),
          field("repo", "Repository", ["participant"]),
          field("notes", "Judge notes", ["judge", "organizer"]),
        ])
      ).status(),
    ).toBe(200);
    expect(
      (await page.request.post(`${base}/forms/${form}/publish/`)).status(),
    ).toBe(201);

    const writes: string[] = [];
    page.on("request", (request) => {
      if (request.method() !== "GET" && !request.url().includes("/preview-as/"))
        writes.push(`${request.method()} ${request.url()}`);
    });

    await page.goto("/app/");
    await openWorkspace(page);
    await chooseWorkspaceEvent(page);
    await goToDestination(page, "setup");
    await goToTask(page, "Forms");
    await page.getByLabel("Edit form").selectOption(form);
    await page
      .getByText("Preview the saved form as a person, version or time", {
        exact: true,
      })
      .click();
    const preview = page.getByRole("region", {
      name: "Preview of the saved form",
    });
    await expect(preview).toBeVisible();
    // Live is what participants get now: the latest published version, every field for the organizer.
    await expect(preview.getByRole("status").first()).toContainText(
      "Previewing Version 2 (live). Nothing is saved or sent.",
    );
    const table = preview.getByRole("region", {
      name: "Fields in the preview",
    });
    await expect(table.locator("tbody tr")).toHaveCount(3);

    // As a judge: the repository field is not shown, and the sentence says who this is for.
    await preview.getByLabel("Person").selectOption("judge");
    await expect(preview.getByRole("status").first()).toContainText(
      "Previewing as judge, Version 2 (live)",
    );
    await expect(table.locator("tbody tr")).toHaveCount(2);
    await expect(table).toContainText("Judge notes");
    await expect(table).not.toContainText("Repository");
    await expect(preview).toContainText(
      "1 of 3 fields is not shown to that person.",
    );

    // At version 1 the judge-only field does not exist yet.
    await preview.getByLabel("Version").selectOption({ index: 1 }); // Version 1
    await expect(preview.getByRole("status").first()).toContainText(
      "Previewing as judge, Version 1",
    );
    await expect(table).not.toContainText("Judge notes");

    // A time before anything was kept is explained, and the controls and last answer stay.
    await preview.getByLabel("As of").fill("2001-01-01T00:00");
    await expect(preview.getByRole("alert")).toContainText(
      "Nothing was kept yet at that time",
    );
    await expect(preview.getByLabel("Person")).toBeVisible();
    // A time after both versions resolves to the latest.
    await preview.getByLabel("As of").fill("2099-01-01T00:00");
    await expect(preview.getByRole("status").first()).toContainText(
      "Version 2",
    );
    await noHorizontalOverflow(page);
    await accessible(page);

    await preview.getByRole("button", { name: "Back to live" }).click();
    await expect(preview.getByRole("status").first()).toContainText(
      "Previewing Version 2 (live).",
    );
    await expect(
      preview.getByRole("button", { name: "Back to live" }),
    ).toBeDisabled();

    // The API is the same resolution, uncached, organizer-only, and a preview changes nothing.
    const direct = await page.request.post(
      `/api/v1/workspaces/${workspace}/preview-as/form/`,
      {
        data: { ref: { event, form }, context: { role: "public" } },
      },
    );
    expect(direct.status()).toBe(200);
    expect(direct.headers()["cache-control"]).toContain("no-store");
    expect((await direct.json()).data.fields).toEqual([]);
    expect(
      (
        await page.request.get(
          `/api/v1/workspaces/${workspace}/preview-as/form/`,
        )
      ).status(),
    ).toBe(405);
    expect(writes).toEqual([]);
    await settled(page);
  });
}
