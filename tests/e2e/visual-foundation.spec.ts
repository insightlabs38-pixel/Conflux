import { expect, test, type Page } from "@playwright/test";
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

// PD-F004-B01: the Conflux v3 visual foundation as it renders. Read-only; every check is computed
// style on the live pages, so an inline style or a stylesheet outside the token layer is caught.
const SCALE = [11, 12, 13, 14, 16, 20, 24, 32];
// Decorative monogram glyphs of the project cover (replaced by PD-F004-B03).
const GLYPH = ".cx-project-cover, .cx-project-card__cover";

/** Every visible text-bearing element whose computed size is off the scale, as `size selector text`. */
async function offScale(page: Page) {
  return page.evaluate(
    ({ scale, glyph }) => {
      const bad: string[] = [];
      const walker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_TEXT,
      );
      const seen = new Set<Element>();
      for (let node = walker.nextNode(); node; node = walker.nextNode()) {
        const el = node.parentElement;
        if (!el || seen.has(el) || !node.textContent?.trim()) continue;
        seen.add(el);
        if (el.closest(glyph) || el.closest("script,style,noscript,svg"))
          continue;
        const box = el.getBoundingClientRect();
        if (!box.width || !box.height) continue;
        const size = parseFloat(getComputedStyle(el).fontSize);
        const fluid = size > 24 && size < 32; // --fs-display, between two scale steps
        if (!scale.includes(Math.round(size * 100) / 100) && !fluid)
          bad.push(
            `${size} ${el.tagName.toLowerCase()}.${el.className} ${node.textContent.trim().slice(0, 30)}`,
          );
      }
      return bad;
    },
    { scale: SCALE, glyph: GLYPH },
  );
}

/** Visible form controls and buttons shorter than `min` px, as `height tag.class label`. */
async function shortControls(page: Page, min: number) {
  return page.evaluate((limit) => {
    const bad: string[] = [];
    const selector =
      'button, select, textarea, input:not([type="checkbox"]):not([type="radio"]):not([type="hidden"]), [role="tab"], [role="button"]';
    for (const el of document.querySelectorAll<HTMLElement>(selector)) {
      if (el.closest(".cx-visually-hidden, [hidden]")) continue;
      const box = el.getBoundingClientRect();
      if (!box.width || !box.height) continue;
      if (getComputedStyle(el).visibility === "hidden") continue;
      if (box.height < limit - 0.5)
        bad.push(
          `${Math.round(box.height)} ${el.tagName.toLowerCase()}.${el.className} ${(el.textContent || el.getAttribute("aria-label") || "").trim().slice(0, 24)}`,
        );
    }
    return bad;
  }, min);
}

/** Rendered corners off the 3/5/8px scale (pill and circle excepted), as `radius tag.class`. */
async function offScaleRadii(page: Page) {
  return page.evaluate(() => {
    const bad = new Set<string>();
    for (const el of document.querySelectorAll<HTMLElement>("body *")) {
      const box = el.getBoundingClientRect();
      if (!box.width || !box.height) continue;
      const radius = parseFloat(getComputedStyle(el).borderTopLeftRadius);
      if (![0, 3, 5, 8].includes(radius) && radius < 100)
        bad.add(`${radius} ${el.tagName.toLowerCase()}.${el.className}`);
    }
    return [...bad];
  });
}

/** Elements at rest that cast a shadow, as `tag.class`; only floating layers may. */
async function shadowed(page: Page) {
  return page.evaluate(() =>
    [...document.querySelectorAll<HTMLElement>("body *")]
      .filter(
        (el) =>
          getComputedStyle(el).boxShadow !== "none" && el.checkVisibility(),
      )
      .map((el) => `${el.tagName.toLowerCase()}.${el.className}`),
  );
}

/**
 * Contexts (form, dialog, section, panel, list row) holding more than one visible primary button,
 * and destructive-final buttons visible at rest, with every closed disclosure opened first.
 */
async function actionHierarchy(page: Page) {
  return page.evaluate(() => {
    document.querySelectorAll("details").forEach((d) => (d.open = true));
    const context =
      "dialog,[role=dialog],form,section,article,[role=region],.cx-card,.cx-state,fieldset,li";
    const byContext = new Map<Element, string[]>();
    const danger: string[] = [];
    for (const b of document.querySelectorAll<HTMLElement>(
      "main .cx-button--primary, main .cx-button--danger",
    )) {
      if (!b.checkVisibility()) continue;
      const label = (b.textContent ?? "").trim().slice(0, 24);
      if (b.classList.contains("cx-button--danger")) danger.push(label);
      else {
        const c = b.closest(context) ?? document.body;
        byContext.set(c, [...(byContext.get(c) ?? []), label]);
      }
    }
    return {
      manyPrimaries: [...byContext]
        .filter(([, labels]) => labels.length > 1)
        .map(
          ([c, labels]) =>
            `${c.tagName.toLowerCase()}.${(c as HTMLElement).className}: ${labels.join(" / ")}`,
        ),
      dangerAtRest: danger,
    };
  });
}

/** Icons that break the contract: wrong size, unnamed and not hidden, or alone on a coloured tile. */
async function iconProblems(page: Page) {
  return page.evaluate(() => {
    const bad: string[] = [];
    for (const icon of document.querySelectorAll<SVGElement>("svg.cx-icon")) {
      if (!icon.checkVisibility()) continue;
      const box = icon.getBoundingClientRect();
      const where = `${icon.parentElement?.tagName.toLowerCase()}.${icon.parentElement?.className}`;
      if (![12, 16, 20].includes(Math.round(box.width)))
        bad.push(`size ${box.width} in ${where}`);
      const hidden = icon.getAttribute("aria-hidden") === "true";
      const named =
        icon.getAttribute("role") === "img" &&
        !!icon.getAttribute("aria-label");
      if (!hidden && !named) bad.push(`unnamed icon in ${where}`);
      const parent = icon.parentElement!;
      const tile =
        parent.childElementCount === 1 &&
        !parent.textContent?.trim() &&
        getComputedStyle(parent).backgroundColor !== "rgba(0, 0, 0, 0)";
      if (tile) bad.push(`coloured tile ${where}`);
    }
    return bad;
  });
}

/** Shell chrome measurements: top bar, rail, brand mark and the absence of marketing copy. */
async function shellGeometry(page: Page) {
  return page.evaluate(() => {
    const box = (selector: string) => {
      const el = document.querySelector<HTMLElement>(selector);
      const r = el?.getBoundingClientRect();
      return r
        ? {
            w: Math.round(r.width),
            h: Math.round(r.height),
            y: Math.round(r.y),
          }
        : null;
    };
    const mark = document.querySelector<HTMLElement>(".cx-brand-mark");
    return {
      header: box(".cx-shell--workspace > .cx-shell__header"),
      rail: box(".cx-sidebar"),
      markBackground: mark ? getComputedStyle(mark).backgroundColor : null,
      inkColor: getComputedStyle(document.documentElement)
        .getPropertyValue("--ink")
        .trim(),
      marketing: /build with confidence/i.test(document.body.innerText),
    };
  });
}

/** Disclosure summaries under the WCAG 2.2 24px target, with every closed disclosure left as is. */
async function shortSummaries(page: Page) {
  return page.evaluate(() =>
    [...document.querySelectorAll<HTMLElement>("main summary")]
      .filter((el) => el.checkVisibility())
      .map((el) => [
        Math.round(el.getBoundingClientRect().height),
        (el.textContent ?? "").trim().slice(0, 24),
      ])
      .filter(([h]) => (h as number) < 24)
      .map(([h, label]) => `${h} ${label}`),
  );
}

/** Statuses that are not an icon plus words, and any leftover colour chip. */
async function statusProblems(page: Page) {
  return page.evaluate(() => {
    const bad: string[] = [];
    for (const el of document.querySelectorAll<HTMLElement>(".cx-status")) {
      if (!el.checkVisibility()) continue;
      const label = (el.textContent ?? "").trim();
      if (!label) bad.push("status without words");
      if (!el.querySelector("svg.cx-icon"))
        bad.push(`status without icon: ${label}`);
      if (getComputedStyle(el).backgroundColor !== "rgba(0, 0, 0, 0)")
        bad.push(`status with a fill: ${label}`);
    }
    if (document.querySelector(".cx-badge"))
      bad.push("cx-badge still rendered");
    return bad;
  });
}

/** Running animations (ambient motion) and the transition time of the first button. */
async function motion(page: Page) {
  return page.evaluate(() => ({
    running: document
      .getAnimations()
      .filter((a) => a.playState === "running" && !(a instanceof CSSTransition))
      .length,
    button: parseFloat(
      getComputedStyle(document.querySelector(".cx-button")!)
        .transitionDuration,
    ),
  }));
}

/** Empty states without a reason, with every closed disclosure opened first. */
async function emptyProblems(page: Page) {
  return page.evaluate(() => {
    document.querySelectorAll("details").forEach((d) => (d.open = true));
    return [...document.querySelectorAll<HTMLElement>(".cx-state--empty")]
      .filter((el) => el.checkVisibility())
      .filter(
        (el) => !(el.querySelector(".cx-state__why")?.textContent ?? "").trim(),
      )
      .map((el) =>
        (el.querySelector(".cx-state__title")?.textContent ?? "").trim(),
      );
  });
}

/** Disclosures that do not use the shared look: native marker showing, or no chevron drawn. */
async function disclosureProblems(page: Page) {
  return page.evaluate(() =>
    [...document.querySelectorAll<HTMLElement>("main details > summary")]
      .filter((el) => el.checkVisibility())
      .filter((el) => {
        const marker = getComputedStyle(el).listStyleType;
        const chevron = getComputedStyle(el, "::before");
        return marker !== "none" || parseFloat(chevron.width) < 6;
      })
      .map((el) => (el.textContent ?? "").trim().slice(0, 30)),
  );
}

const ROLES = ["organizer", "participant-01", "judge-01"];
for (const width of [390, 1440]) {
  for (const role of ROLES) {
    test(`typography on the ${role} overview at ${width}`, async ({
      page,
    }, info) => {
      test.skip(info.project.name !== "desktop", "explicit viewport matrix");
      await page.setViewportSize({ width, height: 900 });
      await signIn(page, role);
      await openWorkspace(page);
      if (role === "organizer") await chooseWorkspaceEvent(page);
      else {
        await page
          .getByRole("combobox", { name: "Event", exact: true })
          .selectOption({ index: 1 });
      }
      await settled(page);
      await goToDestination(page, "overview");
      await settled(page);
      expect(await offScale(page)).toEqual([]);
      // standard density keeps controls at 28px or more; touch layouts at the 44px hit area
      expect(await shortControls(page, width < 768 ? 44 : 28)).toEqual([]);
      expect(await offScaleRadii(page)).toEqual([]);
      expect(await shortSummaries(page)).toEqual([]);
      expect(await disclosureProblems(page)).toEqual([]);
      expect(await iconProblems(page)).toEqual([]);
      expect(await statusProblems(page)).toEqual([]);
      await page.emulateMedia({ reducedMotion: "no-preference" }); // the suite runs with reduce
      const still = await motion(page);
      expect(still.running).toBe(0); // nothing moves on its own
      expect(still.button).toBeGreaterThanOrEqual(0.12);
      expect(still.button).toBeLessThanOrEqual(0.18);
      await page.emulateMedia({ reducedMotion: "reduce" });
      expect((await motion(page)).button).toBeLessThanOrEqual(0.00001);
      const shell = await shellGeometry(page);
      expect(shell.marketing).toBe(false);
      // below 1024px the header still wraps its navigation onto rows until the mobile navigation (PD-F005)
      if (width >= 1024) expect(shell.header).toMatchObject({ h: 44 }); // --h-top, hairline included
      expect(shell.markBackground).toBe("rgb(22, 26, 33)"); // --ink: neutral mark, not the accent
      if (width >= 1024) {
        expect(shell.rail?.w).toBe(216);
        // one line per rail item: a wrapped label costs density (the rail is 216px)
        const tall = await page
          .locator(".cx-sidebar__link")
          .evaluateAll((links) =>
            links
              .map((l) => l.getBoundingClientRect().height)
              .filter((h) => h > 36),
          );
        expect(tall).toEqual([]);
      }
      if (width >= 1024)
        expect(
          await page
            .locator(".cx-sidebar__link:not(:has(svg.cx-icon))")
            .count(),
        ).toBe(0);
      expect(await shadowed(page)).toEqual([]);
      if (role === "organizer" && width >= 768) {
        await page.locator(".cx-account summary").click();
        expect(await shadowed(page)).toEqual(["div.cx-account__panel"]);
      }
      expect(await actionHierarchy(page)).toEqual({
        manyPrimaries: [],
        dangerAtRest: [],
      });
      expect(await emptyProblems(page)).toEqual([]);
      const title = await page
        .locator("main h1")
        .first()
        .evaluate((el) => parseFloat(getComputedStyle(el).fontSize));
      expect(title).toBeLessThanOrEqual(20);
      const body = await page.evaluate(
        () => getComputedStyle(document.body).fontFamily,
      );
      expect(body).toContain("IBM Plex Sans");
      expect(body).toContain("system-ui");
    });
  }

  test(`typography on a public event page at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    const { event } = await eventIds(page);
    await page.goto(`/e/${event}/`);
    await page.waitForLoadState("networkidle");
    expect(await offScale(page)).toEqual([]);
    const h1 = await page
      .locator("h1")
      .first()
      .evaluate((el) => parseFloat(getComputedStyle(el).fontSize));
    expect(h1).toBeGreaterThanOrEqual(24);
    expect(h1).toBeLessThanOrEqual(32);
  });

  // V-HERO-1 / D-012: the default public hero is compact. The band (lockup or art, title, status)
  // is 160-240px on desktop (the lower bound is not a floor) and at most 120px on mobile; the
  // description and the one primary action sit under it; no text sits over art; no sideways scroll.
  test(`the default public hero is a compact band with its action beneath at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    const { event } = await eventIds(page);
    await page.goto(`/e/${event}/`);
    await page.waitForLoadState("networkidle");
    const hero = await page.evaluate(() => {
      const box = (selector: string) =>
        document.querySelector(selector)?.getBoundingClientRect();
      const band = box(".cx-hero .cx-hero__band");
      const after = box(".cx-hero .cx-hero__after");
      const action = box(".cx-hero .cx-button--primary");
      const art = document.querySelector<HTMLElement>(
        ".cx-hero__identity, .cx-hero__image",
      );
      return {
        size: document.body.dataset.heroSize ?? "",
        band: band && { top: band.top, height: band.height },
        after: after && { top: after.top },
        action: action && { top: action.top, bottom: action.bottom },
        art: art && getComputedStyle(art).display,
        h1: document.querySelectorAll("h1").length,
        wide: document.documentElement.scrollWidth - innerWidth,
      };
    });
    expect(hero.size === "" || hero.size === "compact").toBe(true);
    expect(hero.band).not.toBeNull();
    expect(hero.band!.height).toBeLessThanOrEqual(width < 768 ? 120 : 240);
    expect(hero.after!.top).toBeGreaterThanOrEqual(
      hero.band!.top + hero.band!.height - 1,
    );
    expect(hero.action!.bottom).toBeLessThan(900); // the primary action is above the fold
    expect(hero.h1).toBe(1);
    expect(hero.wide).toBeLessThanOrEqual(0);
    // the lockup or art is its own column on desktop and steps aside on mobile
    expect(hero.art === "none").toBe(width < 768);
  });
}

// V-SLOP "advanced never means chaotic": every disclosure on the organizer destinations that have one
// draws the one chevron and hairline, and the chevron turns when it opens.
for (const width of [390, 1440]) {
  test(`every organizer disclosure shares one look, closed and open, at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    await openWorkspace(page);
    await chooseWorkspaceEvent(page);
    await settled(page);
    let seen = 0;
    for (const id of ["setup", "participants", "operations", "profile"]) {
      await goToDestination(page, id);
      await settled(page);
      expect(await disclosureProblems(page)).toEqual([]);
      const summaries = page.locator("main details > summary:visible");
      for (let i = 0; i < (await summaries.count()); i++) {
        const summary = summaries.nth(i);
        const details = summary.locator("xpath=..");
        const closed = await summary.evaluate(
          (el) => getComputedStyle(el, "::before").transform,
        );
        await summary.click();
        await expect(details).toHaveAttribute("open", "");
        await expect // the chevron turns when open (it eases over --t-fast)
          .poll(() =>
            summary.evaluate(
              (el) => getComputedStyle(el, "::before").transform,
            ),
          )
          .not.toBe(closed);
        await summary.click();
        seen += 1;
      }
    }
    expect(seen).toBeGreaterThan(0);
  });
}

// S-LOAD: a grid's columns are known, so while its rows load it keeps its header and shows the shape
// of the rows; past eight seconds it says so; nothing is invented about the data. Read-only: the
// list request is held and then released, never altered.
for (const width of [390, 1440]) {
  test(`a loading grid keeps its header, shows placeholders and admits a slow wait at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    await openWorkspace(page);
    const { workspace, event } = await eventIds(page);
    let release!: () => void;
    const gate = new Promise<void>((resolve) => (release = resolve));
    await page.route("**/entities/applications/**", async (route) => {
      await gate;
      await route.continue();
    });
    await page.clock.install();
    await page.goto(`/app/w/${workspace}/participants?event=${event}`);
    await goToTask(page, "Registration");
    const panel = page.locator('[data-entity="applications"]');
    const busy = panel.locator("[aria-busy='true']");
    await expect(busy).toBeVisible();
    await expect(panel.getByRole("status")).toContainText(
      "Loading Applications",
    );
    await expect(panel.locator(".cx-skeleton").first()).toBeVisible();
    await expect(panel.locator("tbody tr")).toHaveCount(0);
    await expect(panel.getByText("longer than usual")).toHaveCount(0);
    await noHorizontalOverflow(page);
    await accessible(page);
    await page.clock.fastForward(8000);
    await expect(panel.getByText("longer than usual")).toBeVisible();
    release();
    await expect(busy).toHaveCount(0);
    await expect(panel.locator("tbody tr").first()).toBeVisible();
  });
}

// S-ERR: a failed read says what happened, that nothing was changed, and what Try again does; the
// retry then loads the data. Read-only: the list request is answered with a server error once.
for (const width of [390, 1440]) {
  test(`a failed grid load says nothing was changed and recovers on retry at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    await openWorkspace(page);
    const { workspace, event } = await eventIds(page);
    let fail = true;
    await page.route("**/entities/applications/**", async (route) => {
      if (fail)
        await route.fulfill({
          status: 500,
          json: { detail: "The list could not be loaded." },
        });
      else await route.continue();
    });
    await page.goto(`/app/w/${workspace}/participants?event=${event}`);
    await goToTask(page, "Registration");
    const panel = page.locator('[data-entity="applications"]');
    const alert = panel.getByRole("alert");
    await expect(alert).toContainText("The list could not be loaded.");
    await expect(alert).toContainText("Nothing was changed.");
    const retry = alert.getByRole("button", { name: "Try again" });
    await expect(retry).toHaveAccessibleDescription(/loads it again/);
    await accessible(page);
    await noHorizontalOverflow(page);
    fail = false;
    await retry.click();
    await expect(alert).toHaveCount(0);
    await expect(panel.locator("tbody tr").first()).toBeVisible();
  });
}
