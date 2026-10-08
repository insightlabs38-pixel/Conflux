import { expect, test, type Page } from "@playwright/test";
import {
  accessible,
  eventIds,
  noHorizontalOverflow,
  settled,
  signIn,
} from "./support";

// PD-F005-B03-T05: live operations mode is a device choice, off by default. On, a list shows its
// connection health and the data's age, keeps its rows when the connection drops and says so.
// Read-only on the reference event; only this browser's storage changes.
const grid = (page: Page) =>
  page.locator('.cx-entity-grid[data-entity="projects"]');

async function openTools(page: Page) {
  const tools = grid(page).locator(".cx-entity-grid__tools");
  if (!(await tools.evaluate((el) => (el as HTMLDetailsElement).open)))
    await tools.locator("summary").click();
}

test("live operations shows connection health and data age, survives going offline and returns", async ({
  page,
  context,
}) => {
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid`,
  );
  await settled(page);
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
  await expect(grid(page).locator(".cx-live")).toHaveCount(0);

  await openTools(page);
  await grid(page).getByRole("button", { name: "Live operations" }).click();
  const live = grid(page).locator(".cx-live");
  await expect(live).toContainText("Live operations");
  await expect(live).toContainText(/Data as of \d\d:\d\d:\d\d/);
  await expect(live).toContainText(/Checking|Connected/);
  const rows = await grid(page).locator("tbody tr").count();

  // the choice outlives a reload
  await page.reload();
  await settled(page);
  await expect(grid(page).locator(".cx-live")).toHaveCount(1);

  // offline: said plainly, the rows stay, the age keeps counting
  await context.setOffline(true);
  await expect(live).toContainText("Offline");
  await expect(live).toContainText("no connection");
  expect(await grid(page).locator("tbody tr").count()).toBe(rows);
  await noHorizontalOverflow(page);
  await accessible(page);

  await context.setOffline(false);
  await expect(live).not.toContainText("Offline");

  await openTools(page);
  await grid(page).getByRole("button", { name: "Live operations" }).click();
  await expect(grid(page).locator(".cx-live")).toHaveCount(0);
});
