import { expect, test } from "@playwright/test";
import {
  accessible,
  eventIds,
  goToTask,
  openWorkspace,
  settled,
  signIn,
} from "./support";

// PD-F005-B03-T04: what is selected in a list becomes commands in the palette. "Move 2 projects to
// <track>" fills in the track and opens the same previewed bulk operation as the button, so nothing
// changes until it is applied. Creates a track, so it runs on an isolated fixture.
test.skip(({ isMobile }) => isMobile, "keyboard-driven; one viewport");

test("selected projects are offered to the palette as commands that open the preview, change nothing and go when the selection does", async ({
  page,
}) => {
  await signIn(page, "organizer");
  await openWorkspace(page);
  const { workspace, event } = await eventIds(page);
  const api = `/api/v1/workspaces/${workspace}/events/${event}`;
  await page.request.post(`${api}/tracks/`, {
    data: { name: "Palette track" },
  });
  const before = await (
    await page.request.get(`${api}/entities/projects/?sort=name`)
  ).json();
  const [first, second] = before.rows as { id: string; name: string }[];

  await page.goto(`/app/w/${workspace}/participants?event=${event}`);
  await settled(page);
  await goToTask(page, "Projects");
  const panel = page.locator('[data-entity="projects"]');
  const palette = async (text: string) => {
    await page.locator("main").focus();
    await page.keyboard.press("Control+k");
    await page.getByRole("dialog").getByRole("combobox").fill(text);
  };

  // nothing selected: no selection commands
  await palette("selected");
  await expect(
    page.getByRole("option", { name: /Move .* to Palette track/ }),
  ).toHaveCount(0);
  await page.keyboard.press("Escape");

  await panel.getByLabel(`Select ${first.name}`).check();
  await palette("Open details");
  await expect(
    page.getByRole("option", { name: `Open details for ${first.name}` }),
  ).toBeVisible();
  await page.keyboard.press("Escape");

  await panel.getByLabel(`Select ${second.name}`).check();
  await palette("Palette track");
  const move = page.getByRole("option", {
    name: "Move 2 projects to Palette track",
  });
  await expect(move).toBeVisible();
  await accessible(page);
  await page.keyboard.press("Enter");

  // the preview opens with the track chosen; nothing has been applied
  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText("Move 2 projects to Palette track");
  await expect(dialog).toContainText("All or nothing");
  const moved = await (
    await page.request.get(
      `${api}/entities/projects/?filter=${encodeURIComponent(JSON.stringify({ field: "track", op: "eq", value: "Palette track" }))}`,
    )
  ).json();
  expect(moved.total).toBe(0);
  await dialog
    .getByRole("button", { name: /^(Close|Cancel)/ })
    .first()
    .click();

  // clearing the selection from the palette withdraws the commands
  await palette("Clear the selection");
  await page.keyboard.press("Enter");
  await expect(panel.getByLabel(`Select ${first.name}`)).not.toBeChecked();
  await palette("Palette track");
  await expect(
    page.getByRole("option", { name: /Move .* to Palette track/ }),
  ).toHaveCount(0);
});
