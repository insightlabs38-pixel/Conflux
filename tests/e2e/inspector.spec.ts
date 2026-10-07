import { expect, test, type Page } from "@playwright/test";
import { accessible, eventIds, settled, signIn } from "./support";

// PD-F005-B02-T06: a record opens in an inspector beside the list without leaving it - docked from
// 1024px, a sheet below - the list keeps its place, and the record is panel state in the URL.
// Read-only on the reference event.
test.skip(({ isMobile }) => isMobile, "sets its own viewport");

const grid = (page: Page) =>
  page.locator('.cx-entity-grid[data-entity="projects"]');
const inspector = (page: Page) => page.locator(".cx-inspector");

async function open(page: Page, width: number) {
  await page.setViewportSize({ width, height: 900 });
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid`,
  );
  await settled(page);
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
  return { workspace, event };
}

for (const width of [1440, 1100]) {
  test(`a record opens beside the list, the list keeps its place and its row is marked at ${width}`, async ({
    page,
  }) => {
    await open(page, width);
    const rows = grid(page).locator("tbody tr");
    expect(await rows.count()).toBeGreaterThan(5);
    // scroll the list, then open a row that is lower down
    await grid(page)
      .locator(".cx-datagrid")
      .evaluate((el) => (el.scrollTop = 120));
    const scrolled = await grid(page)
      .locator(".cx-datagrid")
      .evaluate((el) => el.scrollTop);
    const target = rows.nth(4);
    const name = (
      await target.locator('td[data-label="Project"]').innerText()
    ).trim();
    await target.getByRole("button", { name: /^Details for/ }).click();
    await expect(inspector(page)).toBeVisible();
    await expect(inspector(page).getByRole("heading", { level: 3 })).toHaveText(
      name,
    );
    await expect(
      inspector(page).getByRole("heading", { level: 3 }),
    ).toBeFocused();
    // docked: beside the list, not over it
    const list = (await grid(page)
      .locator(".cx-entity-grid__main")
      .boundingBox())!;
    const panel = (await inspector(page).boundingBox())!;
    expect(panel.x).toBeGreaterThanOrEqual(list.x + list.width - 1);
    // the list was not reset: same scroll, the same row in the same place, marked
    expect(
      await grid(page)
        .locator(".cx-datagrid")
        .evaluate((el) => el.scrollTop),
    ).toBe(scrolled);
    await expect(target).toHaveAttribute("aria-current", "true");
    // the row stays in view in the list (narrowing the list may rewrap cells, so not to the pixel)
    const scroller = (await grid(page).locator(".cx-datagrid").boundingBox())!;
    const placed = (await target.boundingBox())!;
    expect(placed.y).toBeGreaterThanOrEqual(scroller.y - 1);
    expect(placed.y + placed.height).toBeLessThanOrEqual(
      scroller.y + scroller.height + 1,
    );
    // every field of the record, not only the list's columns
    const labels = await inspector(page).locator("dt").allTextContents();
    expect(labels).toEqual(
      expect.arrayContaining(["Project", "Track", "In gallery", "Created"]),
    );
    expect(labels).toContain("Description"); // a field the list does not show
    // panel state in the URL, replaced: Back leaves the page
    expect(new URL(page.url()).searchParams.get("row_projects")).toBeTruthy();
    await accessible(page);
    // step to the next record, then close with Escape and focus returns to the control
    const position = inspector(page).locator(".cx-inspector__step span");
    await expect(position).toHaveText(/^5 of \d+/);
    await inspector(page).getByRole("button", { name: "Next" }).click();
    await expect(position).toHaveText(/^6 of \d+/);
    await expect(rows.nth(5)).toHaveAttribute("aria-current", "true");
    await expect(rows.nth(4)).not.toHaveAttribute("aria-current", "true");
    await page.keyboard.press("Escape");
    await expect(inspector(page)).toHaveCount(0);
    expect(new URL(page.url()).searchParams.get("row_projects")).toBeNull();
    await expect(
      rows.nth(5).getByRole("button", { name: /^Details for/ }),
    ).toBeFocused();
    expect(
      await grid(page)
        .locator(".cx-datagrid")
        .evaluate((el) => el.scrollTop),
    ).toBe(scrolled);
  });
}

for (const width of [800, 390]) {
  test(`below 1024 the record is a full-height sheet over the list and closes with its button at ${width}`, async ({
    page,
  }) => {
    await open(page, width);
    await grid(page)
      .locator("tbody tr")
      .first()
      .getByRole("button", { name: /^Details for/ })
      .click();
    await expect(inspector(page)).toBeVisible();
    const panel = (await inspector(page).boundingBox())!;
    expect(panel.height).toBeGreaterThanOrEqual(850); // the viewport, minus nothing
    expect(Math.round(panel.x + panel.width)).toBe(width); // against the right edge
    expect(panel.width).toBeGreaterThanOrEqual(Math.min(340, width));
    await accessible(page);
    await inspector(page)
      .getByRole("button", { name: "Close details" })
      .first()
      .click();
    await expect(inspector(page)).toHaveCount(0);
  });
}

test("a link opens the record, and a record that is not on the page is said so", async ({
  page,
}) => {
  const { workspace, event } = await open(page, 1440);
  const id = await grid(page)
    .locator("tbody tr")
    .nth(2)
    .getAttribute("data-row-id");
  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid&row_projects=${id}`,
  );
  await settled(page);
  await expect(inspector(page)).toBeVisible();
  await expect(grid(page).locator(`tr[data-row-id="${id}"]`)).toHaveAttribute(
    "aria-current",
    "true",
  );
  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid&row_projects=00000000-0000-0000-0000-000000000000`,
  );
  await settled(page);
  await expect(inspector(page)).toContainText("not on the current page");
});
