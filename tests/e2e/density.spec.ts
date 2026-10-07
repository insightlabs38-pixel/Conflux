import { expect, test, type Page } from "@playwright/test";
import { eventIds, settled, signIn } from "./support";

// PD-F005-B02-T08: the person's table density (comfortable, compact, high), chosen in the account
// menu, applied to the app's own tables, kept on the device and forgotten at sign-out.
// Read-only on the reference event.
test.skip(({ isMobile }) => isMobile, "sets its own viewport");

const menu = (page: Page) => page.locator(".cx-account");
const attr = (page: Page) =>
  page.evaluate(() => document.documentElement.getAttribute("data-density"));

/** The median height of the body rows of the first table on the page. */
const rowHeight = (page: Page) =>
  page.evaluate(() => {
    const heights = [
      ...document.querySelectorAll<HTMLElement>("main .cx-table tbody tr"),
    ]
      .filter((row) => row.checkVisibility())
      .map((row) => row.getBoundingClientRect().height)
      .sort((a, b) => a - b);
    return heights[Math.floor(heights.length / 2)] ?? 0;
  });

async function choose(page: Page, label: string) {
  await menu(page).locator("summary").click();
  await menu(page).getByRole("radio", { name: label }).check();
  await page.keyboard.press("Escape");
}

test("rows follow the chosen density and a reload keeps it", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  await page.goto(
    `/app/w/${workspace}/participants?event=${event}&section=RegistrationPanel`,
  );
  await settled(page);
  await expect(page.locator("main .cx-table tbody tr").first()).toBeVisible();
  await menu(page).locator("summary").click();
  await expect(
    menu(page).getByRole("radio", { name: "Comfortable" }),
  ).toBeChecked();
  await page.keyboard.press("Escape");
  expect(await attr(page)).toBeNull(); // the default sets nothing
  const comfortable = await rowHeight(page);
  expect(comfortable).toBeGreaterThan(44);

  // the cells ease into their new padding, so measure what the row settles at
  await choose(page, "Compact");
  await expect.poll(() => attr(page)).toBe("compact");
  await expect.poll(() => rowHeight(page)).toBeLessThan(comfortable - 4);
  const compact = await rowHeight(page);
  await choose(page, "High density");
  await expect.poll(() => attr(page)).toBe("high");
  await expect.poll(() => rowHeight(page)).toBeLessThan(compact - 4);
  const high = await rowHeight(page);
  expect(high).toBeGreaterThan(26);
  expect(compact).toBeGreaterThan(36);

  // the person's choice, not the viewport's: a reload keeps it
  await page.reload();
  await settled(page);
  await expect.poll(() => attr(page)).toBe("high");
  await menu(page).locator("summary").click();
  await expect(
    menu(page).getByRole("radio", { name: "High density" }),
  ).toBeChecked();
});

test("on a phone the choice is kept and controls keep their 44px, so touch targets are unaffected", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  await page.goto(`/app/w/${workspace}/participants?event=${event}`);
  await settled(page);
  const control = page.locator(".cx-search-open");
  const before = (await control.boundingBox())!.height;
  expect(before).toBeGreaterThanOrEqual(44);
  await choose(page, "High density");
  await expect.poll(() => attr(page)).toBe("high");
  await page.waitForTimeout(300); // let any transition finish
  expect((await control.boundingBox())!.height).toBe(before);
  const bar = page.locator(".cx-bottom-nav__item").first();
  expect((await bar.boundingBox())!.height).toBeGreaterThanOrEqual(44);
  await page.reload();
  await settled(page);
  await expect.poll(() => attr(page)).toBe("high");
});

test("the choice is forgotten at sign-out and the palette can set it", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  await page.goto(`/app/w/${workspace}/overview?event=${event}`);
  await settled(page);
  await page.keyboard.press("Control+k");
  await page.getByRole("combobox").fill("high-density");
  await page.getByRole("combobox").press("Enter");
  await expect.poll(() => attr(page)).toBe("high");
  await menu(page).locator("summary").click();
  await menu(page)
    .getByRole("button", { name: "Sign out", exact: true })
    .click();
  await expect(page.getByLabel("Username")).toBeVisible();
  await expect.poll(() => attr(page)).toBeNull();
  expect(
    await page.evaluate(() =>
      Object.keys(localStorage).filter((k) => k.includes(":density")),
    ),
  ).toEqual([]);
});
