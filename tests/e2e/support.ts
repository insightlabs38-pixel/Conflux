import AxeBuilder from "@axe-core/playwright";
import {
  expect,
  type Page,
  type PageScreenshotOptions,
} from "@playwright/test";

export const SEED = process.env.E2E_DEMO_SEED ?? "7";
export const PASSWORD = process.env.E2E_DEMO_PASSWORD ?? "demo-pass-7";
export const account = (label: string, seed: string | number = SEED) =>
  `demo-hackathon-${seed}-${label}`;

/** Identity of a demo scenario; defaults to the shared reference (E2E_DEMO_SEED). */
export type Who = { seed: string | number; password: string };

/**
 * Capture policy (PD-B03-T07). Routine runs are failure-first: Playwright keeps a screenshot and
 * trace only for failing tests, and specs take no explicit screenshots or videos. A visual campaign
 * (design review, demo media: `E2E_CAPTURE=visual`, which `make demo-e2e` sets) turns them on.
 */
export const VISUAL = process.env.E2E_CAPTURE === "visual";

/** Explicit screenshot of a page or locator; a no-op outside visual campaigns. */
export async function capture(
  target: { screenshot(options?: PageScreenshotOptions): Promise<unknown> },
  options: PageScreenshotOptions,
) {
  if (VISUAL) await target.screenshot(options);
}

/** Collects browser-side problems so a test can assert there were none. */
export function watch(page: Page) {
  const problems: string[] = [];
  page.on(
    "console",
    (m) =>
      m.type() === "error" &&
      problems.push(`console: ${m.text().slice(0, 200)}`),
  );
  page.on("pageerror", (e) =>
    problems.push(`pageerror: ${e.message.slice(0, 200)}`),
  );
  page.on("response", (r) => {
    if (r.status() >= 400)
      problems.push(`http ${r.status()}: ${new URL(r.url()).pathname}`);
  });
  return problems;
}

export async function signIn(page: Page, label: string, who?: Who) {
  await page.goto("/app/");
  await page.getByLabel("Username").fill(account(label, who?.seed));
  await page.getByLabel("Password").fill(who?.password ?? PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(
    page.getByRole("navigation", { name: "Your workspaces" }),
  ).toBeVisible();
}

export async function openWorkspace(page: Page) {
  await page
    .getByRole("navigation", { name: "Your workspaces" })
    .getByRole("button")
    .first()
    .click();
}

export async function noHorizontalOverflow(page: Page) {
  const { overflow, culprit } = await page.evaluate(() => {
    const width = document.documentElement.clientWidth;
    const overflow = document.documentElement.scrollWidth - width;
    let culprit = "";
    if (overflow > 0)
      for (const element of document.body.querySelectorAll("*")) {
        const box = element.getBoundingClientRect();
        if (box.width > 0 && box.right > width + 1) {
          culprit = `${element.tagName.toLowerCase()}.${String(element.className).slice(0, 60)} (right ${Math.round(box.right)} > ${width})`;
          break;
        }
      }
    return { overflow, culprit };
  });
  expect(
    overflow,
    `horizontal overflow (px)${culprit ? `; first offender ${culprit}` : ""}`,
  ).toBeLessThanOrEqual(0);
}

/**
 * axe on the whole page. `exclude` names frames axe cannot enter (a sandboxed preview frame hangs
 * it); the frame's own document is the public page and is checked on its own URL, the frame element
 * stays in the scan (its title and size) because only its contents are left out.
 */
export async function accessible(page: Page, exclude: string[] = []) {
  let builder = new AxeBuilder({ page }).withTags([
    "wcag2a",
    "wcag2aa",
    "wcag21a",
    "wcag21aa",
    "wcag22aa",
  ]);
  for (const selector of exclude) builder = builder.exclude(selector);
  const { violations } = await builder.analyze();
  expect(
    violations.map(
      (v) =>
        `${v.id}: ${v.nodes.length} node(s) — ${v.help} [${v.nodes
          .slice(0, 3)
          .map((n) => n.target.join(" "))
          .join("; ")}]`,
    ),
    "axe violations",
  ).toEqual([]);
}

export async function eventIds(page: Page) {
  const me = await (await page.request.get("/api/v1/accounts/me/")).json();
  const workspace = me.memberships[0].workspace as string;
  const events = await (
    await page.request.get(`/api/v1/workspaces/${workspace}/events/`)
  ).json();
  return {
    workspace,
    event: events[0].public_id as string,
    name: events[0].name as string,
    status: events[0].status as string,
  };
}

/** Waits until every loading indicator has resolved into content or an error. */
export async function settled(page: Page) {
  await page.waitForLoadState("networkidle");
  await expect(page.getByText(/^(Loading|Checking) .*(…|\.\.\.)$/)).toHaveCount(
    0,
  );
}

/** The workspace navigation link to a destination (`/w/<workspace>/<id>`, optionally with a search). */
export function destinationLink(page: Page, id: string) {
  return page.locator(
    `#workspace-navigation a:is([href$="/${id}"], [href*="/${id}?"])`,
  );
}

/** The same place in the phone's bottom bar (visible only below 768). */
export function barLink(page: Page, id: string) {
  return page.locator(
    `.cx-bottom-nav a:is([href$="/${id}"], [href*="/${id}?"])`,
  );
}

/**
 * Navigate the visible role shell: a place in the phone's bottom bar is tapped there, any other is
 * reached through the control that discloses the list ("Navigation" drawer on a tablet, "More" sheet
 * on a phone).
 */
export async function goToDestination(page: Page, id: string) {
  const link = destinationLink(page, id);
  const bar = barLink(page, id);
  if (await bar.isVisible()) await bar.click();
  else {
    if (!(await link.isVisible()))
      await page
        .getByRole("button", { name: /^(Navigation|More)$/ })
        .filter({ visible: true })
        .click();
    await link.click();
  }
  // the list holds every place (hidden or not), so the current one is marked whichever way it was reached
  await expect(link).toHaveAttribute("aria-current", "page");
}

/** Open a retained workflow task using its accessible tab, not hidden panel content. */
export async function goToTask(page: Page, label: string) {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const tab = page.getByRole("tab", {
    name: new RegExp(`^${escaped}(?:\\s|$)`),
  });
  // Advanced tabs stay behind a disclosure until asked for (PD-F001-B01-T02). Wait for either the
  // tab or the disclosure to exist: asking before the workflow has rendered found neither under
  // load and then waited for a tab that was still collapsed.
  const disclosure = page.locator(".cx-workflow__advanced:visible").first();
  await expect(tab.or(disclosure).first()).toBeVisible();
  if (!(await tab.isVisible()) && (await disclosure.isEnabled()))
    await disclosure.click();
  await tab.click();
  await expect(tab).toHaveAttribute("aria-selected", "true");
}

/** Select the real configured event identity; theme presets may rename seed events. */
export async function chooseWorkspaceEvent(page: Page) {
  const { name, status } = await eventIds(page);
  await page
    .getByRole("button", { name: `${name} (${status})`, exact: true })
    .click();
}
