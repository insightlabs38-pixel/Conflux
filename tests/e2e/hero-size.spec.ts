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

// A 1x1 PNG stands in for the organizer's artwork so the spec needs no network.
const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "base64",
);
const ART = "https://art.example.org/hero.png";

for (const width of [390, 1440]) {
  test(`the immersive hero needs art, keeps the title off the picture and stays within its caps at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page
      .context()
      .route(ART, (route) =>
        route.fulfill({ contentType: "image/png", body: PNG }),
      );
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
    // opt-in: not selectable until there is art
    await expect(size.locator("option[value=immersive]")).toBeDisabled();
    await page.getByLabel("Hero image URL").fill(ART);
    await expect(size.locator("option[value=immersive]")).toBeEnabled();
    await size.selectOption("immersive");
    await page.getByRole("button", { name: "Save appearance" }).click();
    await expect(page.getByText("Event appearance saved.")).toBeVisible();

    const site = await page.context().newPage();
    await site.setViewportSize({ width, height: 900 });
    await site.goto(`/e/${event}/`);
    await site.waitForLoadState("networkidle");
    await expect(site.locator("body")).toHaveAttribute(
      "data-hero-size",
      "immersive",
    );
    const hero = await site.evaluate(() => {
      const art = document
        .querySelector(".cx-hero__image")!
        .getBoundingClientRect();
      const title = document
        .querySelector(".cx-hero h1")!
        .getBoundingClientRect();
      const action = document
        .querySelector(".cx-hero .cx-button--primary")!
        .getBoundingClientRect();
      return {
        art: {
          top: art.top,
          bottom: art.bottom,
          height: art.height,
          width: art.width,
        },
        titleTop: title.top,
        actionBottom: action.bottom,
        wide: document.documentElement.scrollWidth - innerWidth,
        h1: document.querySelectorAll("h1").length,
      };
    });
    expect(hero.art.height).toBeLessThanOrEqual(width < 768 ? 120 : 352);
    expect(hero.art.height).toBeGreaterThan(80);
    expect(hero.titleTop).toBeGreaterThanOrEqual(hero.art.bottom); // never text over art
    expect(hero.h1).toBe(1);
    expect(hero.wide).toBeLessThanOrEqual(0);
    await accessible(site);
    await site.close();

    // back to the default so the fixture is left as found
    await size.selectOption("compact");
    await page.getByLabel("Hero image URL").fill("");
    await page.getByRole("button", { name: "Save appearance" }).click();
    await expect(page.getByText("Event appearance saved.")).toBeVisible();
  });
}

test("a saved immersive hero cannot lose its art, and the refusal says why", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "desktop", "explicit viewport matrix");
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const url = `/api/v1/workspaces/${workspace}/events/${event}/page/`;
  const before = await (await page.request.get(url)).json();
  try {
    const saved = await page.request.patch(url, {
      data: { theme_config: { hero_size: "immersive", banner_url: ART } },
    });
    expect(saved.ok()).toBe(true);
    const refused = await page.request.patch(url, {
      data: { theme_config: { hero_size: "immersive" } },
    });
    expect(refused.status()).toBe(400);
    expect(JSON.stringify(await refused.json())).toContain("artwork");
    const after = await (await page.request.get(url)).json();
    expect(after.theme_config.banner_url).toBe(ART);
  } finally {
    await page.request.patch(url, {
      data: { theme: before.theme, theme_config: before.theme_config },
    });
  }
});

// Boundary: a very long hero title wraps inside the compact band instead of being cut or pushing the
// action off the screen; the band still stays within the 280px the spec allows on a desktop.
test("a long hero title wraps inside the compact band and the action stays above the fold", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "desktop", "explicit viewport matrix");
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const base = `/api/v1/workspaces/${workspace}/events/${event}/page/blocks/`;
  const blocks = await (await page.request.get(base)).json();
  const hero = (blocks.results ?? blocks).find(
    (block: { kind: string }) => block.kind === "hero",
  );
  expect(hero).toBeTruthy();
  const url = `${base}${hero.public_id}/`;
  const title =
    "The International Symposium of Applied Hackathon Engineering and Open Collaboration 2026";
  try {
    const renamed = await page.request.patch(url, {
      data: { config: { ...hero.config, title } },
    });
    expect(renamed.ok()).toBe(true);
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(`/e/${event}/`);
    await page.waitForLoadState("networkidle");
    const measured = await page.evaluate(() => ({
      band: document.querySelector(".cx-hero__band")!.getBoundingClientRect()
        .height,
      action: document
        .querySelector(".cx-hero .cx-button--primary")
        ?.getBoundingClientRect().bottom,
      title: document.querySelector(".cx-hero h1")!.textContent,
    }));
    expect(measured.title).toBe(title); // not cut
    expect(measured.band).toBeLessThanOrEqual(280);
    if (measured.action !== undefined)
      expect(measured.action).toBeLessThan(900);
  } finally {
    await page.request.patch(url, { data: { config: hero.config } });
  }
});

test("an unsupported hero size is refused by the server and nothing is stored", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "desktop", "explicit viewport matrix");
  await signIn(page, "organizer");
  const { workspace, event } = await eventIds(page);
  const url = `/api/v1/workspaces/${workspace}/events/${event}/page/`;
  const before = await (await page.request.get(url)).json();
  const refused = await page.request.patch(url, {
    data: { theme_config: { ...before.theme_config, hero_size: "huge" } },
  });
  expect(refused.status()).toBe(400);
  expect(JSON.stringify(await refused.json())).toContain("hero_size");
  const after = await (await page.request.get(url)).json();
  expect(after.theme_config).toEqual(before.theme_config);
});
