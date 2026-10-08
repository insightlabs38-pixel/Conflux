import { expect, test, type Page } from "@playwright/test";
import { accessible, eventIds, settled, signIn } from "./support";

// PD-F006-B01-T01: sortable columns. Header activation cycles one column; Shift adds up to three
// keys; the server orders the rows and the address keeps the order. Read-only on the reference event.
const grid = (page: Page) =>
  page.locator('.cx-entity-grid[data-entity="projects"]');
const header = (page: Page, name: string) =>
  grid(page)
    .locator("thead th")
    .filter({ hasText: new RegExp(`^${name}`) });
const firstNames = (page: Page) =>
  grid(page).locator('tbody tr td[data-label="Project"]').allInnerTexts();

test("on a phone the Sort by control in the grid tools sorts through the same server order and address", async ({
  page,
}, info) => {
  test.skip(
    info.project.name !== "mobile",
    "headers are the control on desktop",
  );
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid`,
  );
  await settled(page);
  await grid(page).locator(".cx-entity-grid__tools summary").click();
  await grid(page)
    .getByLabel("Sort by")
    .selectOption({ label: "Project, descending" });
  await expect(page).toHaveURL(/sort_projects=-name/);
  const api = `/api/v1/workspaces/${workspace}/events/${event}/entities/projects/`;
  const expected = await (await page.request.get(`${api}?sort=-name`)).json();
  await expect
    .poll(() => firstNames(page).then((names) => names[0]))
    .toBe(String(expected.rows[0].name));
  await accessible(page);
});

test("headers sort through the server with up to three keys, and the address keeps the order", async ({
  page,
}, info) => {
  test.skip(
    info.project.name === "mobile",
    "the phone sorts through the tools",
  );
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const api = `/api/v1/workspaces/${workspace}/events/${event}/entities/projects/`;
  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid`,
  );
  await settled(page);
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();

  await header(page, "Project").getByRole("button").click();
  await expect(header(page, "Project")).toHaveAttribute(
    "aria-sort",
    "ascending",
  );
  await expect(page).toHaveURL(/sort_projects=name(&|$)/);
  const ascending = await (await page.request.get(`${api}?sort=name`)).json();
  await expect
    .poll(() => firstNames(page).then((names) => names[0]))
    .toBe(String(ascending.rows[0].name));

  await header(page, "Project").getByRole("button").click();
  await expect(header(page, "Project")).toHaveAttribute(
    "aria-sort",
    "descending",
  );
  await expect(page).toHaveURL(/sort_projects=-name/);

  // a second key with Shift, in the address and in the order the server returns
  await header(page, "Track")
    .getByRole("button")
    .click({ modifiers: ["Shift"] });
  await expect(header(page, "Track")).toHaveAttribute("aria-sort", "ascending");
  await expect(page).toHaveURL(/sort_projects=-name(%3A|:)track/);
  await expect(header(page, "Project")).toContainText("1");
  await expect(header(page, "Track")).toContainText("2");
  await accessible(page);

  // reload keeps both keys
  await page.reload();
  await settled(page);
  await expect(header(page, "Track")).toHaveAttribute("aria-sort", "ascending");
  await expect(header(page, "Project")).toHaveAttribute(
    "aria-sort",
    "descending",
  );

  // a plain click on another column starts again there
  await header(page, "Team").getByRole("button").click();
  await expect(header(page, "Team")).toHaveAttribute("aria-sort", "ascending");
  await expect(header(page, "Project")).toHaveAttribute("aria-sort", "none");
});
