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
  | "hiddenActions"
  | "recordGrids"
  | "alarmColors"
  | "fakeAi"
  | "precision"
  | "opaqueIds";

export async function slopProblems(page: Page, rules: SlopRule[]) {
  return page.evaluate((wanted) => {
    const found: Record<string, string[]> = {};
    const add = (rule: string, text: string) => (found[rule] ??= []).push(text);
    const name = (el: Element) =>
      `${el.tagName.toLowerCase()}${el.className && typeof el.className === "string" ? "." + el.className.trim().split(/\s+/).slice(0, 2).join(".") : ""}`;
    const shown = (el: Element) => {
      const box = el.getBoundingClientRect();
      if (box.width <= 0 || box.height <= 0 || el.closest("[hidden]"))
        return false;
      // the content of a closed disclosure is not on the page for anyone
      const closed = el.closest("details:not([open])");
      return !closed || !!el.closest("summary");
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

    if (wanted.includes("pills")) {
      // pills carry a state or a count, never ordinary text (V-SLOP-5, V-RAD-1): nothing drawn
      // pill-shaped around words, and at most one tag in a row of a table or list (a project's own
      // tag list is the content and may hold several)
      for (const el of all) {
        if (!shown(el) || el.closest("svg")) continue;
        const style = getComputedStyle(el);
        const box = el.getBoundingClientRect();
        const radius = parseFloat(style.borderTopLeftRadius);
        const text = (el.textContent ?? "").trim();
        const outlined =
          parseFloat(style.borderTopWidth) > 0 || filled(style.backgroundColor);
        if (
          outlined &&
          radius >= Math.min(box.width, box.height) / 2 &&
          box.height < 64 &&
          /[A-Za-z]{3}/.test(text) &&
          !el.matches(".cx-avatar, .cx-avatar *")
        )
          add("pills", `pill around "${text.slice(0, 24)}" in ${name(el)}`);
      }
      for (const row of document.querySelectorAll("tr, li")) {
        if (!shown(row) || row.closest(".cx-tags")) continue;
        const tags = [...row.querySelectorAll(".cx-tag")].filter(shown);
        if (tags.length > 1)
          add("pills", `${tags.length} tags in one ${name(row)}`);
      }
    }

    if (wanted.includes("nestedCards")) {
      // a box with its own border or fill inside another such box is a card in a card (V-SLOP-4):
      // hierarchy comes from hairlines and spacing. Controls, table parts, groups and code are not cards.
      const cardlike = (el: Element) => {
        if (
          el.matches(
            "input, select, textarea, button, a, td, th, tr, thead, tbody, table, li, option, fieldset, legend, summary, pre, code, kbd, progress, meter, img, svg, iframe, video, canvas, dialog, [role=tab], [role=tablist], [role=progressbar], [role=listbox], [role=menu], [role=alert], [role=status], [role=grid], .cx-avatar, .cx-tag, .cx-status, .cx-scroll-region",
          )
        )
          return false;
        const style = getComputedStyle(el);
        const box = el.getBoundingClientRect();
        if (box.width < 120 || box.height < 40) return false;
        const border =
          parseFloat(style.borderTopWidth) > 0 &&
          parseFloat(style.borderRightWidth) > 0 &&
          parseFloat(style.borderBottomWidth) > 0 &&
          parseFloat(style.borderLeftWidth) > 0;
        const padded =
          parseFloat(style.paddingTop) >= 12 &&
          parseFloat(style.paddingLeft) >= 12;
        return border || (filled(style.backgroundColor) && padded);
      };
      for (const el of all) {
        if (!shown(el) || !el.closest("main") || !cardlike(el)) continue;
        for (
          let up = el.parentElement;
          up && up.tagName !== "MAIN";
          up = up.parentElement
        )
          if (cardlike(up)) {
            add("nestedCards", `${name(el)} inside ${name(up)}`);
            break;
          }
      }
    }

    if (wanted.includes("repeatedLabels")) {
      // the same label must not be said again as a heading, a crumb and a card title (V-SLOP-7). The
      // rail names where you are and is allowed to match the page title; headings, the selected
      // task tab and breadcrumbs must each say something different.
      const norm = (text: string | null) =>
        (text ?? "").replace(/\s+/g, " ").trim().toLowerCase();
      const scope = document.querySelector("main") ?? document.body;
      const headings = [
        ...scope.querySelectorAll("h1, h2, h3, h4, .cx-card__title"),
      ]
        .filter(shown)
        .map((h) => ({ el: h, text: norm(h.textContent) }))
        .filter((h) => h.text);
      const seen = new Map<string, number>();
      for (const h of headings) seen.set(h.text, (seen.get(h.text) ?? 0) + 1);
      for (const [text, count] of seen)
        if (count > 1)
          add("repeatedLabels", `heading "${text}" appears ${count} times`);
      const tab = scope.querySelector('[role="tab"][aria-selected="true"]');
      const tabLabel = norm(tab?.firstElementChild?.textContent ?? "");
      if (tabLabel && seen.has(tabLabel))
        add(
          "repeatedLabels",
          `the selected tab "${tabLabel}" is repeated as a heading`,
        );
      const h1 = norm(scope.querySelector("h1")?.textContent ?? "");
      for (const crumb of scope.querySelectorAll(
        '.cx-breadcrumbs a, .cx-breadcrumbs span:not([aria-hidden="true"])',
      ))
        if (h1 && norm(crumb.textContent) === h1)
          add("repeatedLabels", `breadcrumb "${h1}" repeats the page title`);
    }

    if (wanted.includes("hiddenActions")) {
      // an action people use every day is a labelled button on the row or the page, not a menu
      // behind a three-dot glyph (V-SLOP-8). Flags a menu popup, a trigger whose only text is a
      // dots glyph, and an icon-only "more/actions/options" control. A labelled disclosure
      // ("Advanced", "Show filters") is progressive disclosure and stays allowed.
      const dots = /^[\s.\u2026\u22ef\u22ee\u2807\u00b7\u2022]+$/;
      const vague = /^(more|more actions|actions|options|menu|overflow)$/i;
      for (const el of document.querySelectorAll(
        'main button, main summary, main [role="button"], main [aria-haspopup]',
      )) {
        if (!shown(el)) continue;
        const text = (el.textContent ?? "").trim();
        const label = (el.getAttribute("aria-label") ?? text).trim();
        if (
          el.matches(
            '[aria-haspopup]:not([aria-haspopup="false"]):not([aria-haspopup="dialog"])',
          )
        )
          add("hiddenActions", `menu trigger "${label}" in ${name(el)}`);
        else if (dots.test(text) || (!text && vague.test(label)))
          add(
            "hiddenActions",
            `three-dot control "${label || "dots"}" in ${name(el)}`,
          );
      }
      for (const menu of document.querySelectorAll('main [role="menu"]'))
        if (shown(menu)) add("hiddenActions", `a menu popup in ${name(menu)}`);
    }

    if (wanted.includes("recordGrids")) {
      // records the organizer works through (people, projects, submissions) are rows of a sortable
      // table, not a grid of boxed items three across (V-SLOP-14). kpiCards catches boxed blocks;
      // this catches list items and articles laid out in columns. Only the application: the public
      // gallery is browsing and its cards are the content.
      const boxedItem = (el: Element) => {
        const style = getComputedStyle(el);
        return (
          parseFloat(style.borderTopWidth) > 0 ||
          parseFloat(style.borderLeftWidth) > 0 ||
          filled(style.backgroundColor)
        );
      };
      for (const parent of all) {
        if (!parent.closest("main") || parent.closest(".cx-event-site"))
          continue;
        const kids = [...parent.children].filter(
          (kid) =>
            shown(kid) &&
            kid.matches("li, article") &&
            boxedItem(kid) &&
            kid.getBoundingClientRect().width >= 140,
        );
        if (kids.length < 3) continue;
        const tops = kids.map((kid) =>
          Math.round(kid.getBoundingClientRect().top),
        );
        const across = kids.filter((_, i) => Math.abs(tops[i] - tops[0]) <= 2);
        if (across.length >= 3)
          add(
            "recordGrids",
            `${across.length} boxed items across in ${name(parent)}`,
          );
      }
    }

    if (wanted.includes("alarmColors")) {
      // red is for the thing that failed and for the final destructive button, nowhere else
      // (V-SLOP-9). Anything painted in the error hue (text, fill or border) must sit in an alert,
      // an invalid field, a failing status, a refusal or a confirmation dialog, and a page may not
      // carry more than a handful of red marks.
      const red = (color: string) => {
        const m = color.match(/rgba?\((\d+), (\d+), (\d+)(?:, ([\d.]+))?\)/);
        if (!m || (m[4] !== undefined && parseFloat(m[4]) < 0.2)) return false;
        const [r, g, b] = [+m[1] / 255, +m[2] / 255, +m[3] / 255];
        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        const l = (max + min) / 2;
        const sat = max === min ? 0 : (max - min) / (1 - Math.abs(2 * l - 1));
        if (sat < 0.35 || max !== r) return false;
        const hue = (((g - b) / (max - min)) * 60 + 360) % 360;
        return hue <= 15 || hue >= 345;
      };
      const allowed =
        '[role="alert"], [role="alertdialog"], [role="dialog"], dialog, [aria-invalid="true"], ' +
        ".cx-alert, .cx-status--danger, .cx-consequence, [role='group'][aria-label^='Confirm'], .cx-error, [data-state='error'], " +
        "[data-severity='error'], [data-severity='blocker'], [data-denied], .cx-denied";
      const marks: string[] = [];
      for (const el of all) {
        if (!shown(el) || el.closest(allowed)) continue;
        const style = getComputedStyle(el);
        const ownText = [...el.childNodes].some(
          (n) => n.nodeType === 3 && (n.textContent ?? "").trim(),
        );
        const painted =
          (ownText && red(style.color)) ||
          (filled(style.backgroundColor) && red(style.backgroundColor)) ||
          (parseFloat(style.borderTopWidth) > 0 && red(style.borderTopColor)) ||
          (parseFloat(style.borderLeftWidth) > 0 && red(style.borderLeftColor));
        if (painted) marks.push(name(el));
      }
      for (const mark of marks.slice(0, 6))
        add(
          "alarmColors",
          `red outside a failure or a final destructive action: ${mark}`,
        );
      if (marks.length > 6)
        add("alarmColors", `${marks.length} red marks on one page`);
    }

    if (wanted.includes("fakeAi")) {
      // the deterministic workflows (scoring, eligibility, publication) must not borrow the look of
      // an assistant: no sparkle, no "AI", copilot, magic or smart-suggest control (V-SLOP-10). Only
      // the product's own controls are read (buttons, tabs, summaries, labels, legends, options and
      // their accessible names); a project called "AI Tutor" in a link, heading, table or tag is
      // participant content and stays as typed. "Email magic link" is a real sign-in method.
      const fake =
        /\bA\.?I\b|artificial intelligence|copilot|assistant|sparkle|magic(?! link)|smart (?:suggest|fill|assist|reply|draft)|auto-?generat|\bGPT\b|\bLLM\b|\u2728|\u{1FA84}|\u{1F916}/iu;
      for (const el of document.querySelectorAll(
        "button, summary, [role=tab], [role=button], legend, label, [aria-label], [title], input[placeholder], textarea[placeholder]",
      )) {
        if (!shown(el) || el.closest("table, .cx-tag, a, [data-user-content]"))
          continue;
        const own = [...el.childNodes]
          .filter((n) => n.nodeType === 3)
          .map((n) => n.textContent)
          .join(" ");
        const said = [
          el.matches("button, summary, [role=tab], [role=button]")
            ? el.textContent
            : el.matches("legend, label")
              ? own
              : "",
          el.getAttribute("aria-label"),
          el.getAttribute("title"),
          el.getAttribute("placeholder"),
        ].filter(Boolean) as string[];
        const hit = said.find((text) => fake.test(text));
        if (hit)
          add(
            "fakeAi",
            `assistant-like control "${hit.trim().slice(0, 40)}" in ${name(el)}`,
          );
      }
      const decor = document.querySelector(
        "main [class*='sparkle'], main [class*='magic'], main [class*='-ai-']",
      );
      if (decor) add("fakeAi", `sparkle styling in ${name(decor)}`);
    }

    if (wanted.includes("precision")) {
      // a figure is shown to the precision people can act on: two decimals at most (V-SLOP-11).
      // Whatever the server stores, a score of 0.8333333 reads 0.83. Code, preformatted text, inputs
      // and version-like strings (1.2.3) are not figures; fractions of a second after a clock time
      // are not either.
      const long = /(?<![\d.:])\d+\.\d{3,}(?![\d.])/g;
      const walker = document.createTreeWalker(
        document.querySelector("main") ?? document.body,
        NodeFilter.SHOW_TEXT,
      );
      for (let node = walker.nextNode(); node; node = walker.nextNode()) {
        const text = node.textContent ?? "";
        const parent = node.parentElement;
        if (
          !parent ||
          !shown(parent) ||
          parent.closest(
            "code, pre, kbd, samp, script, style, textarea, [data-raw]",
          )
        )
          continue;
        for (const m of text.matchAll(long))
          add(
            "precision",
            `"${m[0]}" shown with ${m[0].split(".")[1].length} decimals in ${name(parent)}`,
          );
      }
    }

    if (wanted.includes("opaqueIds")) {
      // an advanced capability must not depend on someone memorizing or pasting an opaque id
      // (V-SLOP-12): a record is chosen by name from a list. A text box that asks for a UUID or an
      // "X ID", or one already holding a UUID, is the failure. A key the author is inventing (a
      // field's own id) is not a reference to an existing record and says so with data-authored-key.
      const asksForId =
        /\b(?:uuid|guid)\b|\b(?:public|record|object|internal)\s+id\b|\b[a-z]+\s+ids?\b|^\s*ids?\b/i;
      const uuid =
        /\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b/i;
      for (const el of document.querySelectorAll(
        "input:not([type=hidden]):not([type=checkbox]):not([type=radio]):not([type=range]):not([type=file]):not([type=submit]):not([type=button]), textarea",
      )) {
        const box = el as HTMLInputElement;
        if (!shown(el) || box.readOnly || box.disabled) continue;
        if (el.closest("[data-authored-key], [data-user-content]")) continue;
        const labels = [...(box.labels ?? [])].map((l) =>
          [...l.childNodes]
            .filter((n) => n.nodeType === 3)
            .map((n) => n.textContent)
            .join(" "),
        );
        const said = [
          el.getAttribute("aria-label"),
          el.getAttribute("placeholder"),
          ...labels,
        ].filter(Boolean) as string[];
        const hit = said.find((text) => asksForId.test(text));
        if (hit)
          add(
            "opaqueIds",
            `input asks for an id ("${hit.trim().slice(0, 40)}") in ${name(el)}`,
          );
        else if (uuid.test(box.value))
          add("opaqueIds", `input holds an opaque id in ${name(el)}`);
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
