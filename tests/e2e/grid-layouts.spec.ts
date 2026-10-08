import { expect, test, type Page } from "@playwright/test";
import {
  accessible,
  eventIds,
  noHorizontalOverflow,
  settled,
  signIn,
} from "./support";

// PD-F006-B03-T01: board, matrix and calendar are layouts of the one entity query. Read-only on the
// reference event: every number on screen is compared with the API's own answer.
const grid = (page: Page) =>
  page.locator('.cx-entity-grid[data-entity="projects"]');

async function open(page: Page, workspace: string, event: string, query = "") {
  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid${query}`,
  );
  await settled(page);
}
const layout = (page: Page, name: string) =>
  grid(page)
    .getByRole("group", { name: "Layout" })
    .getByRole("button", { name });

test("a board has a column per track with the API's counts, and a card opens the record beside it", async ({
  page,
}) => {
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const api = `/api/v1/workspaces/${workspace}/events/${event}/entities/projects/`;
  const buckets = await (await page.request.get(`${api}?group=track`)).json();
  expect(buckets.groups.length).toBeGreaterThan(1);

  await open(page, workspace, event);
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
  await layout(page, "Board").click();
  await expect(page).toHaveURL(/layout_projects=board/);
  const heads = grid(page).locator(".cx-board__head");
  await expect(heads).toHaveCount(buckets.groups.length);
  for (const [index, group] of buckets.groups.entries())
    await expect(heads.nth(index)).toHaveText(
      new RegExp(`^${group.label}\\s+· ${group.count}$`),
    );
  const first = buckets.groups[0];
  await expect(
    grid(page).locator(".cx-board__column").first().locator(".cx-board__item"),
  ).toHaveCount(Math.min(first.count, 10));
  await noHorizontalOverflow(page);
  await accessible(page);

  // a card opens the record in the inspector, found by its id
  await grid(page).locator(".cx-board__open").first().click();
  await expect(page).toHaveURL(/row_projects=/);
  await expect(page.locator(".cx-inspector")).toBeVisible();
  await expect(page.locator(".cx-inspector__fields dt").first()).toBeVisible();
  await page.keyboard.press("Escape");

  // reload keeps the layout; the list is one click away
  await page.reload();
  await settled(page);
  await expect(heads.first()).toBeVisible();
  await layout(page, "List").click();
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
  await expect(page).not.toHaveURL(/layout_projects/);
});

test("a matrix is a table whose cells equal the API's counts and open the rows they count", async ({
  page,
}) => {
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const api = `/api/v1/workspaces/${workspace}/events/${event}/entities/projects/`;
  const cross = await (
    await page.request.get(`${api}?group=track&subgroup=gallery_visible`)
  ).json();
  await open(page, workspace, event, "&layout_projects=matrix");
  const table = grid(page).locator(".cx-matrix__table");
  await expect(table).toBeVisible();
  const rows = table.locator("tbody tr");
  await expect(rows).toHaveCount(cross.groups.length);
  for (const [index, group] of cross.groups.entries())
    await expect(rows.nth(index).locator("td").last()).toHaveText(
      String(group.count),
    );
  await expect(table.locator("tfoot td").last()).toHaveText(
    String(cross.total),
  );
  await noHorizontalOverflow(page);
  await accessible(page);

  const cell = table.locator(".cx-matrix__cell").first();
  const count = Number(await cell.textContent());
  await cell.click();
  await expect(cell).toHaveAttribute("aria-expanded", "true");
  await expect(grid(page).locator(".cx-matrix__rows tbody tr")).toHaveCount(
    Math.min(count, 25),
  );
});

test("a calendar places rows on days, a day opens its rows, months step in the address", async ({
  page,
}) => {
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const api = `/api/v1/workspaces/${workspace}/events/${event}/entities/projects/`;
  const now = new Date().toISOString().slice(0, 7);
  // find a month that has rows (the seed's creation month), by walking back from now
  let month = now;
  let days: { date: string; count: number }[] = [];
  for (let back = 0; back < 24 && days.length === 0; back++) {
    const date = new Date(`${now}-01T00:00:00Z`);
    date.setUTCMonth(date.getUTCMonth() - back);
    month = date.toISOString().slice(0, 7);
    days = (
      await (
        await page.request.get(`${api}?calendar=created_at&month=${month}`)
      ).json()
    ).days;
  }
  expect(days.length).toBeGreaterThan(0);
  await open(
    page,
    workspace,
    event,
    `&layout_projects=calendar&month_projects=${month}`,
  );
  const buttons = grid(page).locator(".cx-calendar__open");
  await expect(buttons).toHaveCount(days.length);
  await expect(buttons.first().locator("strong")).toHaveText(
    String(days[0].count),
  );
  await noHorizontalOverflow(page);
  await accessible(page);
  await buttons.first().click();
  await expect(grid(page).locator(".cx-calendar__rows tbody tr")).toHaveCount(
    Math.min(days[0].count, 25),
  );
  await grid(page).getByRole("button", { name: "Next month" }).click();
  await expect(page).toHaveURL(/month_projects=/);
  await expect(
    grid(page).locator(".cx-calendar__title").first(),
  ).not.toHaveText(/^$/);
});
