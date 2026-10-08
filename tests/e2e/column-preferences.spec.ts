import { expect, test, type Page } from "@playwright/test";
import { accessible, eventIds, settled, signIn } from "./support";

// PD-F005-B03-T01: a person's column choice for a list is remembered on this device (per person,
// workspace and list), survives a reload, is undone by Reset columns, and is never carried by a link.
// Read-only: only this browser's storage changes.
const grid = (page: Page) =>
  page.locator('.cx-entity-grid[data-entity="projects"]');

async function openTools(page: Page) {
  const tools = grid(page).locator(".cx-entity-grid__tools");
  if (!(await tools.evaluate((el) => (el as HTMLDetailsElement).open)))
    await tools.locator("summary").click();
}

test("a column chosen in the picker is still there after a reload, and Reset columns brings the defaults back", async ({
  page,
}) => {
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const url = `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid`;
  await page.goto(url);
  await settled(page);
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
  await openTools(page);
  const columns = grid(page).getByRole("group", { name: "Columns" });
  const unchecked = columns.locator('input[type="checkbox"]:not(:checked)');
  expect(await unchecked.count()).toBeGreaterThan(0);
  const label = (
    await unchecked.first().locator("xpath=..").innerText()
  ).trim();
  const headers = grid(page).locator("thead th");
  await expect(headers.filter({ hasText: label })).toHaveCount(0);
  await unchecked.first().check();
  await expect(headers.filter({ hasText: label })).toHaveCount(1);
  await expect(columns).toContainText("remembered on this device");

  await page.reload();
  await settled(page);
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
  await expect(headers.filter({ hasText: label })).toHaveCount(1);
  expect(page.url()).not.toContain("columns");

  await openTools(page);
  await columns.getByRole("button", { name: "Reset columns" }).click();
  await expect(headers.filter({ hasText: label })).toHaveCount(0);
  await page.reload();
  await settled(page);
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
  await expect(headers.filter({ hasText: label })).toHaveCount(0);
  await accessible(page);
});
