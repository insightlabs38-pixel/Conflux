import { expect, type Page } from "@playwright/test";

/** Waits until the page stops changing: the element count is the same on four reads 120 ms apart,
 * so a panel that renders after its data arrives is measured, not its loading shell. */
export async function stable(page: Page) {
  let last = -1;
  let same = 0;
  await expect
    .poll(
      async () => {
        const count = await page.evaluate(
          () => document.body.querySelectorAll("*").length,
        );
        same = count === last ? same + 1 : 0;
        last = count;
        return same;
      },
      { intervals: [120], timeout: 10_000 },
    )
    .toBeGreaterThanOrEqual(4);
}

/**
 * The anti-slop gate (spec 004, V-SLOP-*) measured on the rendered page. Each rule is a function
 * that runs in the page and returns what breaks it, as short strings; a page passes when every
 * list is empty. Rules are added by the task that implements them (PD-F004-B04-T01..T08).
 */
export type SlopRule =
  | "gradient"
  | "iconTile"
  | "kpiCards"
  | "operatorCopy"
  | "pills"
  | "nestedCards"
  | "repeatedLabels"
  | "hiddenActions";

export async function slopProblems(page: Page, rules: SlopRule[]) {
  return page.evaluate((wanted) => {
    const found: Record<string, string[]> = {};
    const add = (rule: string, text: string) => (found[rule] ??= []).push(text);
    const name = (el: Element) =>
      `${el.tagName.toLowerCase()}${el.className && typeof el.className === "string" ? "." + el.className.trim().split(/\s+/).slice(0, 2).join(".") : ""}`;
    const shown = (el: Element) => {
      const box = el.getBoundingClientRect();
      return box.width > 0 && box.height > 0 && !el.closest("[hidden]");
    };
    const filled = (color: string) => {
      const m = color.match(/rgba?\(([^)]+)\)/);
      if (!m) return false;
      const parts = m[1].split(",").map((p) => parseFloat(p));
      return (parts[3] ?? 1) > 0;
    };
    const all = [...document.body.querySelectorAll("*")].filter(
      (el) => !el.closest("script,style,noscript"),
    );

    if (wanted.includes("gradient")) {
      for (const el of all) {
        for (const pseudo of [null, "::before", "::after"]) {
          const style = getComputedStyle(el, pseudo);
          if (
            /gradient/i.test(style.backgroundImage) ||
            /gradient/i.test(style.borderImageSource) ||
            /gradient/i.test(style.maskImage)
          ) {
            add("gradient", `${name(el)}${pseudo ?? ""}`);
          }
        }
      }
    }

    if (wanted.includes("iconTile")) {
      for (const svg of document.body.querySelectorAll("svg")) {
        if (!shown(svg)) continue;
        for (
          let el: Element | null = svg.parentElement, depth = 0;
          el && depth < 2;
          el = el.parentElement, depth++
        ) {
          const box = el.getBoundingClientRect();
          const bare = !(el.textContent ?? "").trim();
          if (
            bare &&
            box.width <= 64 &&
            box.height <= 64 &&
            filled(getComputedStyle(el).backgroundColor)
          )
            add("iconTile", `${name(el)} around ${name(svg)}`);
        }
      }
    }
    if (wanted.includes("operatorCopy")) {
      // authenticated pages are tools, not landing pages (V-SLOP-6): nothing larger than 20px, and a
      // page header carries a title and its context, not a tagline of more than ten words
      const app = document.querySelector(
        ".cx-shell--workspace, .cx-shell__main",
      );
      if (app && !document.querySelector(".cx-event-site")) {
        const walker = document.createTreeWalker(app, NodeFilter.SHOW_TEXT);
        const seen = new Set<Element>();
        for (let node = walker.nextNode(); node; node = walker.nextNode()) {
          const el = node.parentElement;
          if (!el || seen.has(el) || !node.textContent?.trim() || !shown(el))
            continue;
          seen.add(el);
          const size = parseFloat(getComputedStyle(el).fontSize);
          if (size > 20.5)
            add(
              "operatorCopy",
              `${size}px text in ${name(el)}: ${node.textContent.trim().slice(0, 30)}`,
            );
        }
        for (const lede of document.querySelectorAll(
          ".cx-page-header__description, .cx-lede, .cx-hero-copy",
        )) {
          const words = (lede.textContent ?? "")
            .trim()
            .split(/\s+/)
            .filter(Boolean).length;
          if (shown(lede) && words > 10)
            add("operatorCopy", `a ${words}-word tagline under a page title`);
        }
      }
    }

    if (wanted.includes("kpiCards")) {
      // a row of three or more boxes with their own border or fill is a card dashboard (V-SLOP-3,
      // V-SLOP-14); a summary is one strip of figures, and a list of records is a table. Only the
      // application: the public gallery is browsing and its cards are the content.
      const boxed = (el: Element) => {
        const style = getComputedStyle(el);
        const border =
          parseFloat(style.borderTopWidth) > 0 ||
          parseFloat(style.borderLeftWidth) > 0;
        return border || filled(style.backgroundColor);
      };
      for (const parent of all) {
        if (!parent.closest("main") || parent.closest(".cx-event-site"))
          continue;
        const kids = [...parent.children].filter(
          (kid) =>
            shown(kid) &&
            boxed(kid) &&
            kid.getBoundingClientRect().width >= 140 &&
            kid.getBoundingClientRect().height >= 48 &&
            !kid.matches("td, th, tr, li, option, button, a, input, select"),
        );
        if (kids.length < 3) continue;
        const tops = kids.map((kid) =>
          Math.round(kid.getBoundingClientRect().top),
        );
        const inARow = kids.filter((_, i) => Math.abs(tops[i] - tops[0]) <= 2);
        if (inARow.length >= 3)
          add("kpiCards", `${inARow.length} cards in a row in ${name(parent)}`);
      }
    }

    if (wanted.includes("iconTile")) {
      // an icon is for recognition where it helps, not a decoration in front of every heading
      const headings = [
        ...document.body.querySelectorAll("h1, h2, h3, h4"),
      ].filter(shown);
      const iconed = headings.filter((h) => h.querySelector(":scope > svg"));
      if (headings.length >= 3 && iconed.length * 2 > headings.length)
        add(
          "iconTile",
          `${iconed.length} of ${headings.length} headings lead with an icon`,
        );
    }
    return found;
  }, rules);
}
