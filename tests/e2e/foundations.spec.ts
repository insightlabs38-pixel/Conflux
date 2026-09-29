import { expect, test } from "@playwright/test";
import { accessible, noHorizontalOverflow, signIn, eventIds } from "./support";

for (const width of [390, 768, 1440]) {
  for (const theme of ["default", "dark", "minimal"]) {
    test(`entry foundations ${theme} at ${width}`, async ({ page }, info) => {
      test.skip(info.project.name !== "desktop", "explicit viewport matrix");
      await page.setViewportSize({ width, height: 900 });
      await page.goto("/app/");
      await expect(page.getByLabel("Username")).toBeVisible();
      await page.evaluate((theme) => {
        document.documentElement.dataset.theme = theme;
        document.body.classList.toggle("theme-minimal", theme === "minimal");
      }, theme);
      await accessible(page);
      await noHorizontalOverflow(page);
      await page.getByLabel("Username").focus();
      await page.keyboard.press("Tab");
      await expect(page.getByLabel("Password")).toBeFocused();
      await page.screenshot({
        path: `tests/e2e/artifacts/uiv2-b01/signin-${theme}-${width}.png`,
        fullPage: true,
      });
      await signIn(page, "organizer");
      await page.evaluate((theme) => {
        document.documentElement.dataset.theme = theme;
        document.body.classList.toggle("theme-minimal", theme === "minimal");
      }, theme);
      await expect(
        page.getByRole("heading", { name: "Choose your workspace" }),
      ).toBeVisible();
      await accessible(page);
      await noHorizontalOverflow(page);
      await page.screenshot({
        path: `tests/e2e/artifacts/uiv2-b01/workspaces-${theme}-${width}.png`,
        fullPage: true,
      });
      const event = (await eventIds(page)).event;
      for (const path of [`/e/${event}/`, `/e/${event}/gallery/`]) {
        await page.goto(path);
        await page.evaluate((theme) => {
          document.documentElement.dataset.theme = theme;
          document.body.classList.toggle("theme-minimal", theme === "minimal");
        }, theme);
        await accessible(page);
        await noHorizontalOverflow(page);
      }
    });
  }
}
