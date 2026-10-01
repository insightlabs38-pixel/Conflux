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

// The bulk-operation planner (PD-F002-B01-T04): select projects in the grid, pick a track, read
// exactly what would change, apply, keep the receipt. It writes, so it runs on an isolated fixture.
for (const width of [390, 1440]) {
  test(`projects are moved to a track through a previewed, receipted bulk operation at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    await openWorkspace(page);
    const { workspace, event } = await eventIds(page);
    const api = `/api/v1/workspaces/${workspace}/events/${event}`;
    const track = await (
      await page.request.post(`${api}/tracks/`, {
        data: { name: `Bulk ${width}` },
      })
    ).json();
    const receiptsBefore = (
      await (await page.request.get(`${api}/operations/bulk/receipts/`)).json()
    ).length;
    const before = await (
      await page.request.get(`${api}/entities/projects/?sort=name`)
    ).json();
    expect(before.total).toBeGreaterThan(2);
    const [first, second, untouched] = before.rows as {
      id: string;
      name: string;
    }[];

    await page.goto(`/app/w/${workspace}/participants?event=${event}`);
    await settled(page);
    await goToTask(page, "Projects");
    const panel = page.locator('[data-entity="projects"]');
    await expect(panel.locator("tbody tr")).toHaveCount(before.total);
    await noHorizontalOverflow(page);

    // No selection, no bulk bar. Select two projects by keyboard-reachable checkboxes.
    await expect(page.getByRole("group", { name: "Bulk actions" })).toHaveCount(
      0,
    );
    await panel.getByLabel(`Select ${first.name}`).check();
    await panel.getByLabel(`Select ${second.name}`).check();
    const bar = page.getByRole("group", { name: "Bulk actions" });
    await expect(bar).toContainText("2 selected");
    await expect(
      bar.getByRole("button", { name: "Preview move" }),
    ).toBeDisabled();
    await bar
      .getByLabel("Move to track")
      .selectOption({ label: `Bulk ${width}` });
    await bar.getByRole("button", { name: "Preview move" }).click();

    // The dry run states the effect and changed nothing yet.
    const dialog = page.getByRole("dialog");
    await expect(dialog).toContainText(`Move 2 projects to Bulk ${width}`);
    await expect(dialog).toContainText("All or nothing");
    expect(
      (
        await (
          await page.request.get(
            `${api}/entities/projects/?filter=${encodeURIComponent(JSON.stringify({ field: "track", op: "eq", value: `Bulk ${width}` }))}`,
          )
        ).json()
      ).total,
    ).toBe(0);
    await accessible(page);

    // Apply: the receipt names what happened, the list reloads, the selection is gone.
    await dialog.getByRole("button", { name: `Move to Bulk ${width}` }).click();
    await expect(dialog).toContainText("Applied.");
    await expect(dialog.getByRole("list", { name: "Receipt" })).toContainText(
      "Move 2 projects",
    );
    await dialog.getByRole("button", { name: "Close" }).click();
    await expect(dialog).toHaveCount(0);
    await expect(page.getByRole("group", { name: "Bulk actions" })).toHaveCount(
      0,
    );
    await expect(
      panel.locator("tbody tr", { hasText: first.name }),
    ).toContainText(`Bulk ${width}`);

    const moved = await (
      await page.request.get(
        `${api}/entities/projects/?filter=${encodeURIComponent(JSON.stringify({ field: "track", op: "eq", value: `Bulk ${width}` }))}`,
      )
    ).json();
    expect(moved.rows.map((r: { id: string }) => r.id).sort()).toEqual(
      [first.id, second.id].sort(),
    );
    const other = before.rows.find(
      (r: { id: string }) => r.id === untouched.id,
    );
    expect(other).toBeDefined();
    // The receipt is on the record and readable through the API.
    const receipts = await (
      await page.request.get(`${api}/operations/bulk/receipts/`)
    ).json();
    expect(receipts).toHaveLength(receiptsBefore + 1);
    expect(receipts[0].actions).toEqual(["move"]); // newest first
    const detail = await (
      await page.request.get(
        `${api}/operations/bulk/receipts/${receipts[0].public_id}/`,
      )
    ).json();
    expect(detail.effects[0].changes).toHaveLength(2);
    expect(track.public_id).toBeTruthy();

    // A second run on projects already on the track still previews and applies cleanly.
    await panel.getByLabel(`Select ${first.name}`).check();
    await bar
      .getByLabel("Move to track")
      .selectOption({ label: `Bulk ${width}` });
    await bar.getByRole("button", { name: "Preview move" }).click();
    await expect(dialog).toContainText("Move 1 project");
    await dialog.getByRole("button", { name: "Cancel" }).click();
    await expect(dialog).toHaveCount(0);
    await noHorizontalOverflow(page);
  });
}
