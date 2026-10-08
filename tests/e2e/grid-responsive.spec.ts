import { expect, test, type Page } from "@playwright/test";
import {
  accessible,
  eventIds,
  noHorizontalOverflow,
  settled,
  signIn,
} from "./support";

// PD-F006-B02-T01: the list on narrow screens. At 640px and below the rows are a list and the
// header becomes a bar above them (select the page, sort); from 641 to 1023 a wide list scrolls
// sideways inside its container and keeps the select box and the name column in view.
// Read-only on the reference event.
const grid = (page: Page) =>
  page.locator('.cx-entity-grid[data-entity="projects"]');

async function open(page: Page, width: number) {
  await page.setViewportSize({ width, height: 800 });
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid`,
  );
  await settled(page);
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
}

test("on a phone the header is a bar above the rows with select-page and sort in reach", async ({
  page,
}, info) => {
  test.skip(info.project.name === "mobile", "sets its own viewport");
  await open(page, 390);
  const bar = grid(page).locator("thead tr");
  await expect(bar).toBeVisible();
  const select = grid(page).getByRole("checkbox", {
    name: /Select all projects on this page/,
  });
  await expect(select).toBeVisible();
  const sortButtons = grid(page).locator("thead .cx-datagrid__sort");
  expect(await sortButtons.count()).toBeGreaterThan(1);
  for (const index of [0, 1]) {
    const box = await sortButtons.nth(index).boundingBox();
    expect(box!.height).toBeGreaterThanOrEqual(43); // a touch target
  }
  // not sticky: the list is the page's own scroll
  expect(
    await grid(page)
      .locator("thead th")
      .nth(1)
      .evaluate((th) => getComputedStyle(th).position),
  ).toBe("static");
  await sortButtons.first().click();
  await expect(grid(page).locator("thead th[aria-sort=ascending]")).toHaveCount(
    1,
  );
  await select.check();
  await expect(
    grid(page).locator(".cx-datagrid__footer [role=status]"),
  ).toContainText("selected");
  await noHorizontalOverflow(page);
  await accessible(page);
});

test("from 641 to 1023px a wide list keeps its select box and name column while it scrolls sideways", async ({
  page,
}, info) => {
  test.skip(info.project.name === "mobile", "sets its own viewport");
  await open(page, 800);
  const scroller = grid(page).locator(".cx-datagrid");
  const overflows = await scroller.evaluate(
    (el) => el.scrollWidth > el.clientWidth + 20,
  );
  expect(overflows).toBe(true);
  await scroller.evaluate((el) => (el.scrollLeft = 200));
  const where = await grid(page)
    .locator("tbody tr")
    .first()
    .evaluate((tr) => {
      const box = tr.closest(".cx-datagrid")!.getBoundingClientRect();
      const select = tr
        .querySelector("td.cx-datagrid__select")!
        .getBoundingClientRect();
      const name = tr
        .querySelector("td.cx-datagrid__name")!
        .getBoundingClientRect();
      const style = getComputedStyle(tr.querySelector("td.cx-datagrid__name")!);
      return {
        selectOffset: Math.round(select.left - box.left),
        nameOffset: Math.round(name.left - box.left),
        opaque: !/rgba\(.*, 0\)|transparent/.test(style.backgroundColor),
      };
    });
  expect(where.selectOffset).toBeLessThanOrEqual(2);
  expect(where.nameOffset).toBeGreaterThan(30);
  expect(where.nameOffset).toBeLessThan(60); // just right of the select box
  expect(where.opaque).toBe(true);
  await accessible(page);
});
