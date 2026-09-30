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

// Consequences, not "Are you sure?" (PD-F001-B02-T02): before a destructive or high-impact
// operation the dialog states, from the server, what it would do, refuses what the domain refuses,
// and names its confirmation for the operation. Mutating, so it runs on an isolated fixture.
for (const width of [390, 1440]) {
  test(`destructive operations state their consequences at ${width}`, async ({
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
          name: `Conseq ${width} ${stamp}`,
          starts_at: "2027-03-05T09:00:00Z",
          timezone: "UTC",
        },
      },
    );
    expect(created.status()).toBe(201);
    const event = (await created.json()).public_id as string;
    const base = `/api/v1/workspaces/${workspace}/events/${event}`;
    await page.request.post(`${base}/stages/`, {
      data: { name: "Demo day", participation_mode: "team_locked" },
    });

    await page.goto(`/app/w/${workspace}/setup?event=${event}`);
    await settled(page);
    await goToTask(page, "Stages");
    const dialog = page.getByRole("dialog");

    // The judged stage has a published rubric: refused, with the reason, and nothing to confirm.
    await page.getByRole("button", { name: "Delete stage Judging" }).click();
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole("alert")).toContainText("cannot be done");
    await expect(dialog).toContainText("published rubric");
    await expect(dialog.getByRole("button")).toHaveCount(1);
    await noHorizontalOverflow(page);
    await accessible(page);
    await page.keyboard.press("Escape");
    await expect(dialog).toHaveCount(0);
    await expect(page.getByRole("list", { name: "Stage order" })).toContainText(
      "Judging",
    );

    // A link: what it would stop, and that the flow would break.
    await page
      .getByRole("button", { name: "Delete link Build to Judging" })
      .click();
    await expect(dialog).toContainText(
      "Participants can no longer be advanced from Build to Judging.",
    );
    await expect(dialog).toContainText("The stage flow breaks");
    await expect(dialog).toContainText("You can add it back afterwards.");
    await dialog.getByRole("button", { name: "Cancel" }).click();
    await expect(dialog).toHaveCount(0);

    // An isolated stage: confirm with the named button; the record says what it took with it.
    await page.getByRole("button", { name: "Delete stage Demo day" }).click();
    await expect(dialog).toContainText("This cannot be undone.");
    await dialog.getByRole("button", { name: "Delete stage Demo day" }).click();
    await expect(dialog).toHaveCount(0);
    await expect(
      page.getByRole("list", { name: "Stage order" }),
    ).not.toContainText("Demo day");
    const audit = await (
      await page.request.get(`/api/v1/audit/${workspace}/`)
    ).json();
    const rows = audit as {
      action: string;
      metadata: { consequences?: unknown[] };
    }[];
    expect(
      rows.find((row) => row.action === "stage.deleted")?.metadata.consequences,
    ).toBeDefined();

    // High-impact status change: the unresolved items and the one-way nature are stated first.
    await goToTask(page, "Settings");
    await page.getByRole("button", { name: "Move to open" }).click();
    await expect(dialog).toContainText("Still unresolved");
    await expect(dialog).toContainText("cannot be set back");
    await accessible(page);
    await dialog.getByRole("button", { name: "Cancel" }).click();
    expect((await (await page.request.get(`${base}/`)).json()).status).toBe(
      "draft",
    );
    await page.getByRole("button", { name: "Move to open" }).click();
    await dialog.getByRole("button", { name: /^Open Conseq/ }).click();
    await expect(dialog).toHaveCount(0);
    expect((await (await page.request.get(`${base}/`)).json()).status).toBe(
      "open",
    );
  });
}
