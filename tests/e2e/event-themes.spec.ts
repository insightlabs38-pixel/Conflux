import { expect, test } from "@playwright/test";
import {
  accessible,
  eventIds,
  noHorizontalOverflow,
  signIn,
  watch,
} from "./support";

const variants = {
  technical: {
    theme: "default",
    theme_config: {
      typography: "technical",
      personality: "square",
      hero: "split",
      density: "compact",
      width: "wide",
      accent: "#126454",
    },
  },
  student: {
    theme: "default",
    theme_config: {
      typography: "system",
      personality: "expressive",
      hero: "poster",
      density: "comfortable",
      width: "wide",
      accent: "#a32918",
    },
  },
  conference: {
    theme: "minimal",
    theme_config: {
      typography: "editorial",
      personality: "restrained",
      hero: "editorial",
      density: "comfortable",
      background: "paper",
      accent: "#363636",
    },
  },
  dark: { theme: "dark", theme_config: { hero: "split" } },
};
for (const width of [390, 768, 1024, 1440]) {
  for (const [name, config] of Object.entries(variants)) {
    test(`public theme ${name} at ${width}`, async ({ page }, info) => {
      test.skip(info.project.name !== "desktop", "explicit viewport matrix");
      await signIn(page, "organizer");
      const { workspace, event } = await eventIds(page);
      const url = `/api/v1/workspaces/${workspace}/events/${event}/page/`;
      const original = await (await page.request.get(url)).json();
      try {
        expect((await page.request.patch(url, { data: config })).ok()).toBe(
          true,
        );
        await page.setViewportSize({ width, height: 900 });
        const problems = watch(page);
        await page.goto(`/e/${event}/`);
        await expect(page.locator("body")).toHaveAttribute(
          "data-hero",
          config.theme_config.hero,
        );
        await accessible(page);
        await noHorizontalOverflow(page);
        await page.screenshot({
          path: `tests/e2e/artifacts/uiv2-b03/${name}-${width}.png`,
          fullPage: true,
        });
        await page.goto(`/app/?event=${event}`);
        await expect(page.locator(".cx-event-site")).toHaveAttribute(
          "data-hero",
          config.theme_config.hero,
        );
        await page.waitForLoadState("networkidle");
        await accessible(page);
        await noHorizontalOverflow(page);
        expect(problems).toEqual([]);
      } finally {
        expect(
          (
            await page.request.patch(url, {
              data: {
                theme: original.theme,
                theme_config: original.theme_config,
              },
            })
          ).ok(),
        ).toBe(true);
      }
    });
  }
}
