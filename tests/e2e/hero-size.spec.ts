import { expect, test } from "@playwright/test";
import {
  accessible,
  chooseWorkspaceEvent,
  eventIds,
  goToDestination,
  goToTask,
  noHorizontalOverflow,
  openWorkspace,
  settled,
  signIn,
} from "./support";

// PD-F004-B02-T08: the organizer chooses how much room the public hero takes (none, compact,
// standard) in the Public page task; the choice is stored in the page's theme settings, validated
// by the server, and the public page follows. Isolated: it edits the event's page.
const BUDGET = { compact: 240, standard: 360, none: 240 };

for (const width of [390, 1440]) {
  test(`organizer chooses the hero size and the public page follows at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    const { event } = await eventIds(page);
    await page.goto("/app/");
    await openWorkspace(page);
    await chooseWorkspaceEvent(page);
    await goToDestination(page, "setup");
    await goToTask(page, "Public page");
    await page.getByRole("tab", { name: /^Appearance/ }).click();
    await settled(page);

    const size = page.getByLabel("Hero size", { exact: true });
    await expect(size).toHaveValue("compact"); // an event that never chose gets compact
    const bands: Record<string, number> = {};
    for (const choice of ["none", "standard", "compact"] as const) {
      await size.selectOption(choice);
      await page.getByRole("button", { name: "Save appearance" }).click();
      await expect(page.getByText("Event appearance saved.")).toBeVisible();
      await accessible(page);
      await noHorizontalOverflow(page);

      const site = await page.context().newPage();
      await site.setViewportSize({ width, height: 900 });
      await site.goto(`/e/${event}/`);
      await site.waitForLoadState("networkidle");
      await expect(site.locator("body")).toHaveAttribute(
        "data-hero-size",
        choice,
      );
      await expect(site.locator("h1")).toHaveCount(1);
      await expect(site.locator(".cx-hero .cx-button--primary")).toBeVisible();
      const band = await site
        .locator(".cx-hero__band")
        .evaluate((el) => el.getBoundingClientRect().height);
      bands[choice] = band;
      expect(band).toBeLessThanOrEqual(width < 768 ? 120 : BUDGET[choice]);
      const hidden = await site
        .locator(".cx-hero__identity, .cx-hero__image, .cx-event-kicker")
        .evaluateAll((els) =>
          els.every((el) => getComputedStyle(el).display === "none"),
        );
      expect(hidden).toBe(choice === "none" || width < 768);
      await noHorizontalOverflow(site);
      await site.close();
    }
    if (width >= 768) {
      expect(bands.none).toBeLessThan(bands.compact);
      expect(bands.compact).toBeLessThan(bands.standard);
    }
    await size.selectOption("compact");
  });
}

test("an unsupported hero size is refused by the server and nothing is stored", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "desktop", "explicit viewport matrix");
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const url = `/api/v1/workspaces/${workspace}/events/${event}/page/`;
  const before = await (await page.request.get(url)).json();
  const refused = await page.request.patch(url, {
    data: { theme_config: { ...before.theme_config, hero_size: "immersive" } },
  });
  expect(refused.status()).toBe(400);
  expect(JSON.stringify(await refused.json())).toContain("hero_size");
  const after = await (await page.request.get(url)).json();
  expect(after.theme_config).toEqual(before.theme_config);
});
