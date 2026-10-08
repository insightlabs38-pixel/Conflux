import { expect, test, type Page } from "@playwright/test";
import {
  accessible,
  eventIds,
  noHorizontalOverflow,
  settled,
  signIn,
} from "./support";

// PD-F006-B01-T05: the bulk-action bar. It appears with a selection, names the count, has one
// primary action, says why it is unavailable, and only opens the previewed operation. Nothing is
// applied here, so it is read-only on the reference event.
const grid = (page: Page) =>
  page.locator('.cx-entity-grid[data-entity="projects"]');

test("the bar appears with a selection, explains a disabled action and opens the preview without applying", async ({
  page,
}) => {
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const api = `/api/v1/workspaces/${workspace}/events/${event}/entities/projects/`;
  const before = await (await page.request.get(api)).json();
  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid`,
  );
  await settled(page);
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
  const bar = page.getByRole("group", { name: "Bulk actions" });
  await expect(bar).toHaveCount(0);

  const boxes = grid(page).locator("input[data-row-select]");
  await boxes.nth(0).check();
  await boxes.nth(1).check();
  await expect(bar).toContainText("2 selected");
  const preview = bar.getByRole("button", { name: "Preview move" });
  await expect(preview).toBeDisabled();
  await expect(bar).toContainText("Choose a track to move to.");
  await expect(bar.locator(".cx-button--primary")).toHaveCount(1);
  await noHorizontalOverflow(page);
  await accessible(page);

  const options = await bar
    .getByLabel("Move to track")
    .locator("option")
    .allInnerTexts();
  const track = options.find((name) => name.trim() !== "");
  expect(track).toBeTruthy();
  await bar.getByLabel("Move to track").selectOption({ label: track! });
  await expect(preview).toBeEnabled();
  await preview.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText("Move 2 projects");
  await page.keyboard.press("Escape"); // nothing applied
  await expect(dialog).toHaveCount(0);

  const after = await (await page.request.get(api)).json();
  expect(
    after.rows.map((r: { id: string; track: string }) => [r.id, r.track]),
  ).toEqual(
    before.rows.map((r: { id: string; track: string }) => [r.id, r.track]),
  );
});
