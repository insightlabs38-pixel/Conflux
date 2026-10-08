import { expect, test, type Page } from "@playwright/test";
import { accessible, eventIds, settled, signIn } from "./support";

// PD-F006-B01-T07: paging. Rows per page is a fixed choice kept in the address; the footer says
// where the page is; a link to a page that no longer exists lands on the last one. Server paging
// only (no client windowing: spec 006 decision 8). Read-only on the reference event; the 5,012-row
// evidence is docs/verification/PD-F006-B01/T07-scale.log and tests/integration/test_entity_query_scale.py.
const grid = (page: Page) =>
  page.locator('.cx-entity-grid[data-entity="projects"]');

test("rows per page changes the request and the address, and a page past the end lands on the last", async ({
  page,
}) => {
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const api = `/api/v1/workspaces/${workspace}/events/${event}/entities/projects/`;
  const all = await (await page.request.get(`${api}?limit=100`)).json();
  const base = `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid`;

  await page.goto(base);
  await settled(page);
  const footer = grid(page).locator(".cx-datagrid__footer");
  await expect(footer).toContainText(`of ${all.total.toLocaleString("en-US")}`);
  await expect(footer).toContainText("Page 1 of 1");
  const size = grid(page).getByLabel("Rows per page");
  await expect(size).toHaveValue("25");
  await size.selectOption("50");
  await expect(page).toHaveURL(/size_projects=50/);
  await expect(size).toHaveValue("50");
  await size.selectOption("25");
  expect(page.url()).not.toContain("size_projects"); // the default is not written
  await accessible(page);

  // a link to a page that does not exist lands on the last one and says so
  await page.goto(`${base}&page_projects=9`);
  await settled(page);
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
  await expect(footer).toContainText("Page 1 of 1");
  await expect(footer).toContainText(`Showing 1–${all.total}`);
  expect(page.url()).not.toContain("page_projects=9");

  // sizes outside the fixed set are ignored
  await page.goto(`${base}&size_projects=7`);
  await settled(page);
  await expect(grid(page).getByLabel("Rows per page")).toHaveValue("25");
});
