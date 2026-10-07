import { expect, test, type Page } from "@playwright/test";
import {
  chooseWorkspaceEvent,
  eventIds,
  goToDestination,
  openWorkspace,
  settled,
  signIn,
} from "./support";

// PD-F004-B01: the Conflux v3 visual foundation as it renders. Read-only; every check is computed
// style on the live pages, so an inline style or a stylesheet outside the token layer is caught.
const SCALE = [11, 12, 13, 14, 16, 20, 24, 32];
// Decorative monogram glyphs of the public hero and project cover (replaced by PD-F004-B02/B03).
const GLYPH = ".cx-hero__identity, .cx-project-cover, .cx-project-card__cover";

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
}
