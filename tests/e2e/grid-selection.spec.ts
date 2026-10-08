import { expect, test, type Page } from "@playwright/test";
import { accessible, eventIds, settled, signIn } from "./support";

// PD-F006-B01-T04: row selection. Rows are chosen with labelled checkboxes, the header selects the
// page, the count is announced, and Clear selection empties it. Read-only on the reference event
// (nothing is applied).
const grid = (page: Page) =>
  page.locator('.cx-entity-grid[data-entity="projects"]');

test("rows are selected by checkbox and keyboard, the page by the header, and the count is announced", async ({
  page,
}) => {
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid`,
  );
  await settled(page);
  const rows = grid(page).locator("tbody tr");
  await expect(rows.first()).toBeVisible();
  const count = await rows.count();
  const footer = grid(page).locator(".cx-datagrid__footer [role=status]");
  await expect(footer).not.toContainText("selected");

  const boxes = grid(page).locator("input[data-row-select]");
  await boxes.nth(0).check();
  await boxes.nth(1).focus();
  await page.keyboard.press("Space"); // the keyboard selects too
  await expect(footer).toContainText("2 selected");
  await expect(rows.nth(0)).toHaveAttribute("aria-selected", "true");
  // the header's select-all is reachable on every width (on a phone it is the bar above the rows)
  const header = grid(page).getByRole("checkbox", {
    name: /Select all projects on this page/,
  });
  expect(
    await header.evaluate((el: HTMLInputElement) => el.indeterminate),
  ).toBe(true);
  await header.check();
  await expect(footer).toContainText(`${count} selected`);
  await accessible(page);

  await grid(page).getByRole("button", { name: "Clear selection" }).click();
  await expect(footer).not.toContainText("selected");
  await expect(boxes.nth(0)).not.toBeChecked();
  await expect(page.getByRole("group", { name: "Bulk actions" })).toHaveCount(
    0,
  );
});
