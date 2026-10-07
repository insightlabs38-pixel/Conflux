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
    await page.getByLabel("Hero image URL", { exact: true }).fill(ART);
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
    await page.getByLabel("Hero image URL", { exact: true }).fill("");
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

// PD-F004-B03-T06: image focal point and a phone image. Set through the form (a disclosure under the
// brand settings), stored as whole percents, drawn as the crop's object-position, and the phone image
// is what the browser picks on a phone.
const PHONE = "https://art.example.org/hero-phone.png";
for (const width of [390, 1440]) {
  test(`the focal point sets the crop and a phone image replaces the art on a phone at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    for (const url of [ART, PHONE])
      await page
        .context()
        .route(url, (route) =>
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

    await page.getByLabel("Hero image URL", { exact: true }).fill(ART);
    const crop = page.locator("details.cx-theme-art");
    await expect(crop).not.toHaveAttribute("open", ""); // advanced: closed until asked for
    await crop.locator("summary").click();
    await crop.getByLabel("Phone hero image URL").fill(PHONE);
    await crop.getByLabel("Focal point, left to right").fill("30");
    await crop.getByLabel("Focal point, top to bottom").fill("70");
    await expect(crop.getByText("30% from the left")).toBeVisible();
    await page
      .getByLabel("Hero size", { exact: true })
      .selectOption("immersive");
    await page.getByRole("button", { name: "Save appearance" }).click();
    await expect(page.getByText("Event appearance saved.")).toBeVisible();

    const site = await page.context().newPage();
    await site.setViewportSize({ width, height: 900 });
    await site.goto(`/e/${event}/`);
    await site.waitForLoadState("networkidle");
    const art = await site.evaluate(() => {
      const img = document.querySelector<HTMLImageElement>(".cx-hero__image")!;
      return {
        position: getComputedStyle(img).objectPosition,
        source: img.currentSrc,
        height: img.getBoundingClientRect().height,
      };
    });
    expect(art.position).toBe("30% 70%");
    expect(art.source).toBe(width < 768 ? PHONE : ART);
    expect(art.height).toBeLessThanOrEqual(width < 768 ? 120 : 352);
    await noHorizontalOverflow(site);
    await accessible(site);
    await site.close();

    // a refused crop says why and keeps the draft; the saved page is not changed
    await crop.getByLabel("Phone hero image URL").fill("javascript:alert(1)");
    await page.getByRole("button", { name: "Save appearance" }).click();
    await expect(page.getByRole("alert")).toContainText("safe absolute");
    await page.reload();
    await page.getByRole("tab", { name: /^Appearance/ }).click();
    await page.locator("details.cx-theme-art summary").click();
    await expect(page.getByLabel("Phone hero image URL")).toHaveValue(PHONE);

    // restore the default so the fixture is left as found
    await page.getByLabel("Hero size", { exact: true }).selectOption("compact");
    await page.getByLabel("Hero image URL", { exact: true }).fill("");
    await page.getByLabel("Phone hero image URL").fill("");
    await page.getByRole("button", { name: "Centre the crop" }).click();
    await page.getByRole("button", { name: "Save appearance" }).click();
    await expect(page.getByText("Event appearance saved.")).toBeVisible();
  });
}

// PD-F004-B03-T05: an event-specific lead replaces the hero. It is added through the page builder, its
// action link is checked by the server, and the public page shows one h1 with no default hero.
for (const width of [390, 1440]) {
  test(`a lead block added in the page builder replaces the hero on the public page at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    const { workspace, event } = await eventIds(page);
    const base = `/api/v1/workspaces/${workspace}/events/${event}/page/blocks/`;
    const openers = (
      (await (await page.request.get(base)).json()) as {
        kind: string;
        public_id: string;
      }[]
    ).filter((block) => block.kind === "hero" || block.kind === "lead");
    for (const block of openers)
      await page.request.delete(`${base}${block.public_id}/`);
    await page.goto("/app/");
    await openWorkspace(page);
    await chooseWorkspaceEvent(page);
    await goToDestination(page, "setup");
    await goToTask(page, "Public page");
    await settled(page);

    await page
      .getByLabel("Add block")
      .selectOption({ label: "Lead (replaces the hero)" });
    await page.getByRole("button", { name: "Add", exact: true }).click();
    const editor = page.getByRole("region", {
      name: "Edit Lead (replaces the hero) block",
    });
    await editor
      .getByLabel("Title", { exact: true })
      .fill("Applications close Friday");
    await editor
      .getByLabel("Body", { exact: true })
      .fill("Bring a laptop and a team of up to four.");
    await editor.getByLabel("Action label").fill("Apply now");
    await editor.getByLabel("Action link").fill("javascript:alert(1)");
    await editor.getByRole("button", { name: "Save block" }).click();
    await expect(editor.getByRole("alert")).toContainText("path on this site");
    await editor.getByLabel("Action link").fill("/apply/");
    await editor.getByRole("button", { name: "Save block" }).click();
    await expect(editor.getByText("All changes saved")).toBeVisible();
    await accessible(page);

    const site = await page.context().newPage();
    await site.setViewportSize({ width, height: 900 });
    await site.goto(`/e/${event}/`);
    await site.waitForLoadState("networkidle");
    await expect(site.locator("h1")).toHaveCount(1);
    await expect(site.locator("h1")).toHaveText("Applications close Friday");
    await expect(site.getByRole("link", { name: "Apply now" })).toHaveAttribute(
      "href",
      "/apply/",
    );
    await expect(site.locator(".cx-hero")).toHaveCount(0);
    const top = await site.evaluate(
      () => document.querySelector(".cx-lead h1")!.getBoundingClientRect().top,
    );
    expect(top).toBeLessThan(900 * 0.3);
    await noHorizontalOverflow(site);
    await accessible(site);
    await site.close();
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
    data: { theme_config: { ...before.theme_config, hero_size: "huge" } },
  });
  expect(refused.status()).toBe(400);
  expect(JSON.stringify(await refused.json())).toContain("hero_size");
  const after = await (await page.request.get(url)).json();
  expect(after.theme_config).toEqual(before.theme_config);
});
