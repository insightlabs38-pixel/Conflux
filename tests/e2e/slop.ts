import type { Page } from "@playwright/test";

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
