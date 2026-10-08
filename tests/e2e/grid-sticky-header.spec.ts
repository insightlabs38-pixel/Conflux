import { expect, test, type Page } from "@playwright/test";
import { eventIds, settled, signIn } from "./support";

// PD-F006-B01-T08: the header stays in view while a tall list scrolls inside its own container,
// opaque and above the rows, also with the inspector docked; on a phone the list becomes a row
// list and there is no header to stick. Read-only on the reference event.
const grid = (page: Page) =>
  page.locator('.cx-entity-grid[data-entity="projects"]');

async function open(page: Page, width: number) {
  await page.setViewportSize({ width, height: 700 });
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&section=ProjectsGrid`,
  );
  await settled(page);
  await expect(grid(page).locator("tbody tr").first()).toBeVisible();
}

for (const width of [1440, 1100]) {
  test(`the header sticks to the top of the list's own scroll area at ${width}, also with the inspector open`, async ({
    page,
  }, info) => {
    test.skip(info.project.name === "mobile", "sets its own viewport");
    await open(page, width);
    const scroller = grid(page).locator(".cx-datagrid");
    const metrics = () =>
      scroller.evaluate((el) => ({
        scrolls: el.scrollHeight > el.clientHeight + 40,
        top: el.getBoundingClientRect().top,
      }));
    expect((await metrics()).scrolls).toBe(true); // 22 rows do not fit in 70% of 700px

    const probe = () =>
      grid(page)
        .locator("thead th")
        .filter({ hasText: /^Project/ })
        .evaluate((th) => {
          const r = th.getBoundingClientRect();
          const box = th.closest(".cx-datagrid")!.getBoundingClientRect();
          const style = getComputedStyle(th);
          const at = document.elementFromPoint(
            r.x + r.width / 2,
            r.y + r.height / 2,
          );
          return {
            offset: Math.round(r.top - box.top),
            opaque: !/rgba\(.*, 0\)|transparent/.test(style.backgroundColor),
            covers: th.contains(at),
            position: style.position,
          };
        });
    const stuck = async () => {
      await scroller.evaluate((el) => {
        el.scrollIntoView({ block: "center" }); // the page may have scrolled when the inspector opened
        el.scrollTop = 400;
      });
      // the layout settles for a moment after the inspector docks; wait for it, then judge
      await expect.poll(async () => (await probe()).covers).toBe(true); // nothing scrolls over it
      const head = await probe();
      expect(head.position).toBe("sticky");
      expect(Math.abs(head.offset)).toBeLessThanOrEqual(1);
      expect(head.opaque).toBe(true);
    };
    await stuck();

    // the inspector docked beside the list does not take the header with it
    await grid(page)
      .getByRole("button", { name: /^Details for/ })
      .first()
      .click();
    await expect(page.locator(".cx-inspector")).toBeVisible();
    await stuck();
    await page.keyboard.press("Escape");
  });
}

test("on a phone the list is a row list and its header is a bar that scrolls with the page, not a sticky row", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "mobile", "the phone project");
  await open(page, 390);
  const head = await grid(page)
    .locator("thead th")
    .nth(1)
    .evaluate((th) => getComputedStyle(th).position);
  expect(head).toBe("static"); // nothing sticks on the phone: the list is the page's own scroll
  // each cell carries its own label instead of a column header above it
  const label = await grid(page)
    .locator("tbody tr td")
    .nth(1)
    .evaluate((td) => td.getAttribute("data-label"));
  expect(label).toBeTruthy();
});
