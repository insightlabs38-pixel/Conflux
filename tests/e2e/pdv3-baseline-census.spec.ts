import fs from "node:fs";
import path from "node:path";
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import {
  account,
  eventIds,
  goToDestination,
  openWorkspace,
  PASSWORD,
  settled,
  signIn,
  watch,
} from "./support";

/**
 * PD-B00-T05 visual baseline census. Measurement only: nothing here asserts on layout quality.
 * Opt-in (`E2E_CENSUS=1`) so it never changes the regular suite. Writes JPEGs plus manifest.json
 * to docs/verification/PD-B00/ui-census/ with per-surface console/HTTP problems, horizontal
 * overflow and axe (WCAG 2.2 AA) violation counts. Run after `scripts/demo-reset`.
 */
const OUT = path.resolve("docs/verification/PD-B00/ui-census");
const VIEWPORTS = {
  desktop: { width: 1280, height: 800 },
  mobile: { width: 390, height: 844 },
} as const;
type Row = {
  id: string;
  role: string;
  viewport: string;
  problems: string[];
  overflowPx: number;
  axe: string[];
  note?: string;
};
const rows: Row[] = [];

async function capture(
  page: Page,
  id: string,
  role: string,
  viewport: string,
  problems: string[],
  note?: string,
) {
  await settled(page).catch(() => undefined);
  await page.waitForTimeout(700); // let post-selection requests start
  await settled(page).catch(() => undefined);
  const overflowPx = await page.evaluate(
    () =>
      document.documentElement.scrollWidth -
      document.documentElement.clientWidth,
  );
  const { violations } = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .analyze();
  await page.screenshot({
    path: path.join(OUT, `${viewport}-${id}.jpg`),
    type: "jpeg",
    quality: 55,
    fullPage: true,
  });
  rows.push({
    id,
    role,
    viewport,
    problems: problems.splice(0),
    overflowPx,
    axe: violations.map((v) => `${v.id}×${v.nodes.length}`),
    note,
  });
}

const ROLE_VIEWS: Record<string, string[]> = {
  organizer: [
    "overview",
    "setup",
    "participants",
    "eligibility",
    "judging",
    "results",
    "communications",
    "onsite",
    "integrations",
    "operations",
    "profile",
  ],
  "judge-01": ["overview", "queue", "schedule", "profile", "messages"],
  "participant-01": [
    "overview",
    "team",
    "project",
    "resources",
    "messages",
    "profile",
  ],
  // Real empty states: approved participant with no team/project yet.
  "participant-23": ["overview", "team", "project"],
  mentor: ["overview"],
  volunteer: ["overview"],
};

test.describe("pd-b00 ui census", () => {
  test.skip(!process.env.E2E_CENSUS, "opt-in census (E2E_CENSUS=1)");
  test.describe.configure({ mode: "serial" });
  test.beforeAll(() => fs.mkdirSync(OUT, { recursive: true }));
  test.afterAll(() => {
    // Skipped projects (mobile) also run hooks; never overwrite with an empty manifest.
    if (rows.length)
      fs.writeFileSync(
        path.join(OUT, "manifest.json"),
        JSON.stringify(rows, null, 1) + "\n",
      );
  });

  for (const [vpName, vp] of Object.entries(VIEWPORTS)) {
    test(`public + sign-in @${vpName}`, async ({ page }, info) => {
      test.skip(info.project.name !== "desktop", "viewport looped internally");
      test.setTimeout(240000);
      await page.setViewportSize(vp);
      const problems = watch(page);
      await page.goto("/app/");
      await capture(page, "signin", "anonymous", vpName, problems);
      // Discover the event through the API as the organizer, then visit public pages signed out.
      await signIn(page, "organizer");
      const { event } = await eventIds(page);
      await page.request.post("/api/v1/accounts/logout/");
      for (const [id, sub] of [
        ["public-landing", ""],
        ["public-gallery", "gallery/"],
        ["public-results", "results/"],
        ["public-agenda", "agenda/"],
        ["public-map", "map/"],
      ]) {
        await page.goto(`/e/${event}/${sub}`);
        await capture(page, id, "anonymous", vpName, problems);
      }
    });

    for (const [label, views] of Object.entries(ROLE_VIEWS)) {
      test(`${label} workspace @${vpName}`, async ({ page }, info) => {
        test.skip(
          info.project.name !== "desktop",
          "viewport looped internally",
        );
        test.setTimeout(300000);
        await page.setViewportSize(vp);
        const problems: string[] = [];
        await signIn(page, label);
        const w = watch(page);
        await capture(page, `selector-${label}`, label, vpName, w);
        await openWorkspace(page);
        const eventButton = page
          .getByRole("button", { name: /\((open|draft|closed|archived)/i })
          .first();
        if (await eventButton.isVisible().catch(() => false))
          await eventButton.click();
        for (const view of views) {
          try {
            await goToDestination(page, view);
          } catch (e) {
            rows.push({
              id: `${label}-${view}`,
              role: label,
              viewport: vpName,
              problems,
              overflowPx: -1,
              axe: [],
              note: `navigation failed: ${String(e).slice(0, 120)}`,
            });
            continue;
          }
          const picker = page.getByRole("combobox", { name: "Event" });
          if (
            (await picker.isVisible().catch(() => false)) &&
            !(await picker.inputValue())
          ) {
            await picker.selectOption({ index: 1 });
            await settled(page).catch(() => undefined);
          }
          const stage = page.getByRole("combobox", { name: "Stage" });
          if (
            (await stage.isVisible().catch(() => false)) &&
            !(await stage.inputValue())
          ) {
            await stage.selectOption({ index: 1 }).catch(() => undefined);
            await settled(page).catch(() => undefined);
          }
          await capture(page, `${label}-${view}`, label, vpName, w);
        }
      });
    }
  }

  test("synthetic loading / error / denied states", async ({ page }, info) => {
    test.skip(info.project.name !== "desktop", "single viewport");
    test.setTimeout(240000);
    await page.setViewportSize(VIEWPORTS.desktop);
    const problems: string[] = [];
    // Loading: hold the identity request open, capture the pending shell.
    let release: () => void = () => undefined;
    const held = new Promise<void>((resolve) => (release = resolve));
    await page.route("**/api/v1/accounts/me/", async (route) => {
      await held;
      await route.continue().catch(() => undefined);
    });
    const nav = page.goto("/app/");
    await page.waitForTimeout(1500);
    await page.screenshot({
      path: path.join(OUT, "desktop-state-loading.jpg"),
      type: "jpeg",
      quality: 55,
    });
    rows.push({
      id: "state-loading",
      role: "anonymous",
      viewport: "desktop",
      problems: [],
      overflowPx: 0,
      axe: [],
      note: "synthetic: /accounts/me held open while the shell renders",
    });
    release();
    await nav;
    await settled(page);
    await page.unrouteAll({ behavior: "wait" });

    // Error: fail the events list for the organizer workspace.
    await signIn(page, "organizer");
    await page.route("**/api/v1/workspaces/*/events/**", (route) =>
      route.fulfill({ status: 500, body: '{"detail":"synthetic failure"}' }),
    );
    await openWorkspace(page);
    await capture(
      page,
      "state-error-events",
      "organizer",
      "desktop",
      problems,
      "synthetic: events list 500",
    );
    await page.unroute("**/api/v1/workspaces/*/events/**");

    // Denied: participant requests an organizer view by URL.
    await page.request.post("/api/v1/accounts/logout/");
    await page.goto("/app/");
    await page.getByLabel("Username").fill(account("participant-01"));
    await page.getByLabel("Password").fill(PASSWORD);
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(
      page.getByRole("navigation", { name: "Your workspaces" }),
    ).toBeVisible();
    await openWorkspace(page);
    await page.goto(page.url().replace(/\/[^/?]+(\?.*)?$/, "/setup"));
    await capture(
      page,
      "state-denied-organizer-view",
      "participant-01",
      "desktop",
      problems,
      "participant requesting /setup (no denied state: the URL is replaced by the overview)",
    );
  });
});
