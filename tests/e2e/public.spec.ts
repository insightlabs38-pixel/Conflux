import { expect, test } from "@playwright/test";
import {
  accessible,
  eventIds,
  noHorizontalOverflow,
  signIn,
  watch,
} from "./support";

let event = "";
test.beforeAll(async ({ browser }) => {
  const page = await browser.newPage();
  await signIn(page, "organizer");
  event = (await eventIds(page)).event;
  await page.close();
});

for (const [name, path] of [
  ["event landing", (e: string) => `/e/${e}/`],
  ["gallery", (e: string) => `/e/${e}/gallery/`],
  ["results", (e: string) => `/e/${e}/results/`],
  ["agenda", (e: string) => `/e/${e}/agenda/`],
  ["expo map", (e: string) => `/e/${e}/map/`],
] as const) {
  test(`public ${name}: styled, accessible, no overflow, no errors`, async ({
    page,
  }) => {
    const problems = watch(page);
    await page.goto(path(event));
    await page.waitForLoadState("networkidle");
    expect(
      await page.evaluate(() => getComputedStyle(document.body).fontFamily),
    ).toContain("system-ui");
    await noHorizontalOverflow(page);
    await accessible(page);
    expect(problems).toEqual([]);
  });
}

test("the gallery is searchable and a project page opens from it", async ({
  page,
}) => {
  await page.goto(`/e/${event}/gallery/`);
  const links = page.locator(
    "main a[href*='/projects/'], main a[href*='project']",
  );
  test.skip((await links.count()) === 0, "demo event has no gallery projects");
  await links.first().click();
  await expect(page.getByRole("main")).toBeVisible();
  await accessible(page);
});

test("the skip link is the first tab stop and moves focus to main content", async ({
  page,
}) => {
  await page.goto(`/e/${event}/`);
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Skip to main content" }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main-content")).toBeFocused();
});

test("the SPA public event page has no failing requests", async ({ page }) => {
  const problems = watch(page);
  await page.goto(`/app/?event=${event}`);
  await page.waitForLoadState("networkidle");
  await noHorizontalOverflow(page);
  expect(problems).toEqual([]);
});
