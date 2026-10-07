import { expect, test, type Page } from "@playwright/test";
import {
  chooseWorkspaceEvent,
  eventIds,
  goToDestination,
  goToTask,
  openWorkspace,
  settled,
  signIn,
} from "./support";
import { slopProblems, stable, type SlopRule } from "./slop";

// The anti-slop gate of spec 004 (V-SLOP-1..) measured on the live pages of every role and on the
// public site, at 390 and 1440. Read-only. One test per page and width: pages are large and each
// is measured on its own. A rule is added to RULES by the task that implements it.
const RULES: SlopRule[] = [
  "gradient",
  "iconTile",
  "kpiCards",
  "operatorCopy",
  "pills",
  "nestedCards",
  "repeatedLabels",
  "hiddenActions",
];

const SETUP_TASKS = [
  "Settings",
  "Stages",
  "Policies",
  "Rules",
  "Forms",
  "Public page",
];
const PAGES: Record<string, string[]> = {
  organizer: [
    "overview",
    "setup",
    "participants",
    "eligibility",
    "judging",
    "results",
    "communications",
    "onsite",
    "operations",
    "profile",
  ],
  "participant-01": [
    "overview",
    "team",
    "project",
    "resources",
    "messages",
    "profile",
  ],
  "judge-01": ["overview", "queue", "schedule", "profile", "messages"],
};
const PUBLIC = ["", "gallery/", "results/"];

async function open(page: Page, role: string) {
  await signIn(page, role);
  await openWorkspace(page);
  if (role === "organizer") await chooseWorkspaceEvent(page);
  else {
    await page
      .getByRole("combobox", { name: "Event", exact: true })
      .selectOption({ index: 1 });
    if (role === "judge-01")
      await page
        .getByRole("combobox", { name: "Stage", exact: true })
        .selectOption({ index: 1 });
  }
  await settled(page);
}

test.describe.configure({ mode: "parallel" });
for (const width of [390, 1440]) {
  for (const [role, destinations] of Object.entries(PAGES)) {
    for (const id of destinations) {
      test(`${role} ${id} follows the anti-slop rules at ${width}`, async ({
        page,
      }, info) => {
        test.skip(info.project.name !== "desktop", "explicit viewport matrix");
        await page.setViewportSize({ width, height: 900 });
        await open(page, role);
        await goToDestination(page, id);
        await settled(page);
        await stable(page);
        const found: Record<string, unknown> = {};
        const here = await slopProblems(page, RULES);
        if (Object.keys(here).length) found[`${id}`] = here;
        // every other task of the destination too: a nested box or a pill row hides in a second tab
        const labels = await page.evaluate(() =>
          [...document.querySelectorAll("main [role=tab]")]
            .filter((tab) => (tab as HTMLElement).offsetParent !== null)
            .map((tab) => tab.firstElementChild?.textContent?.trim() ?? "")
            .filter(Boolean),
        );
        for (const label of labels.slice(1)) {
          await goToTask(page, label);
          await settled(page);
          await stable(page);
          const problems = await slopProblems(page, RULES);
          if (Object.keys(problems).length)
            found[`${id} / ${label}`] = problems;
        }
        expect(found).toEqual({});
      });
    }
  }
  for (const task of SETUP_TASKS) {
    test(`organizer setup, ${task} follows the anti-slop rules at ${width}`, async ({
      page,
    }, info) => {
      test.skip(info.project.name !== "desktop", "explicit viewport matrix");
      await page.setViewportSize({ width, height: 900 });
      await open(page, "organizer");
      await goToDestination(page, "setup");
      await goToTask(page, task);
      await settled(page);
      await stable(page);
      expect(await slopProblems(page, RULES)).toEqual({});
    });
  }
  for (const path of PUBLIC) {
    test(`public /${path} follows the anti-slop rules at ${width}`, async ({
      page,
    }, info) => {
      test.skip(info.project.name !== "desktop", "explicit viewport matrix");
      await page.setViewportSize({ width, height: 900 });
      await signIn(page, "organizer");
      const { event } = await eventIds(page);
      await page.goto(`/e/${event}/${path}`);
      await page.waitForLoadState("networkidle");
      await stable(page);
      expect(await slopProblems(page, RULES)).toEqual({});
    });
  }
}

// The gate must be able to fail: each rule is shown a page that breaks it.
test("the audit sees a gradient and an icon in a coloured square", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "desktop", "explicit viewport matrix");
  await signIn(page, "organizer");
  const { event } = await eventIds(page);
  await page.goto(`/e/${event}/`);
  await page.addStyleTag({
    content:
      ".cx-hero h1::after{content:'';display:block;height:4px;background:linear-gradient(red,blue)}",
  });
  await page.evaluate(() => {
    const tile = document.createElement("span");
    tile.style.cssText =
      "display:inline-block;width:32px;height:32px;background:rgb(30,80,200)";
    tile.innerHTML =
      '<svg width="16" height="16" viewBox="0 0 24 24"><path d="M5 12h14"/></svg>';
    document.querySelector("main")!.prepend(tile);
  });
  const found = await slopProblems(page, ["gradient", "iconTile"]);
  expect(Object.keys(found).sort()).toEqual(["gradient", "iconTile"]);
});

test("the audit sees a row of cards", async ({ page }, info) => {
  test.skip(info.project.name !== "desktop", "explicit viewport matrix");
  await page.setViewportSize({ width: 1440, height: 900 });
  await open(page, "organizer");
  await goToDestination(page, "overview");
  await settled(page);
  await page.evaluate(() => {
    const row = document.createElement("div");
    row.style.cssText = "display:flex;gap:8px";
    row.innerHTML = [1, 2, 3]
      .map(
        (n) =>
          `<div style="width:200px;height:80px;border:1px solid #888">Card ${n}</div>`,
      )
      .join("");
    document.querySelector("main")!.prepend(row);
  });
  const found = await slopProblems(page, ["kpiCards"]);
  expect(found.kpiCards?.[0]).toContain("3 cards in a row");
});

test("the audit sees oversized and tagline copy in an operator page", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "desktop", "explicit viewport matrix");
  await page.setViewportSize({ width: 1440, height: 900 });
  await open(page, "organizer");
  await goToDestination(page, "overview");
  await settled(page);
  await page.evaluate(() => {
    const big = document.createElement("p");
    big.style.fontSize = "40px";
    big.textContent = "Welcome back";
    const tagline = document.createElement("p");
    tagline.className = "cx-page-header__description";
    tagline.textContent =
      "Manage the event, review what needs attention, and bring every result to publication today.";
    document.querySelector("main")!.prepend(big, tagline);
  });
  const found = await slopProblems(page, ["operatorCopy"]);
  expect(found.operatorCopy).toHaveLength(2);
});

test("the audit sees a pill around words and two tags in one row", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "desktop", "explicit viewport matrix");
  await page.setViewportSize({ width: 1440, height: 900 });
  await open(page, "organizer");
  await goToDestination(page, "overview");
  await settled(page);
  await page.evaluate(() => {
    const pill = document.createElement("span");
    pill.style.cssText =
      "display:inline-block;padding:2px 12px;border:1px solid #888;border-radius:999px";
    pill.textContent = "Design review";
    const row = document.createElement("ul");
    row.innerHTML =
      '<li><span class="cx-tag">AI</span> <span class="cx-tag">Open data</span></li>';
    document.querySelector("main")!.prepend(pill, row);
  });
  const found = await slopProblems(page, ["pills"]);
  expect(found.pills?.some((p) => p.startsWith("pill around"))).toBe(true);
  expect(found.pills?.some((p) => p.includes("2 tags in one li"))).toBe(true);
});

test("the audit sees a card inside a card", async ({ page }, info) => {
  test.skip(info.project.name !== "desktop", "explicit viewport matrix");
  await page.setViewportSize({ width: 1440, height: 900 });
  await open(page, "organizer");
  await goToDestination(page, "overview");
  await settled(page);
  await page.evaluate(() => {
    const outer = document.createElement("div");
    outer.style.cssText = "border:1px solid #888;padding:16px;width:400px";
    outer.innerHTML =
      '<div style="border:1px solid #aaa;padding:12px;height:60px">Inner card</div>';
    document.querySelector("main")!.prepend(outer);
  });
  const found = await slopProblems(page, ["nestedCards"]);
  expect(found.nestedCards).toHaveLength(1);
});

test("the audit sees a label said twice and a crumb that repeats the title", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "desktop", "explicit viewport matrix");
  await page.setViewportSize({ width: 1440, height: 900 });
  await open(page, "organizer");
  await goToDestination(page, "overview");
  await settled(page);
  await page.evaluate(() => {
    const main = document.querySelector("main")!;
    const title = main.querySelector("h1")?.textContent ?? "Overview";
    const nav = document.createElement("nav");
    nav.className = "cx-breadcrumbs";
    nav.innerHTML = `<span>${title}</span>`;
    const twice = document.createElement("div");
    twice.innerHTML = "<h3>Same words</h3><h4>Same words</h4>";
    main.prepend(nav, twice);
  });
  const found = await slopProblems(page, ["repeatedLabels"]);
  expect(
    found.repeatedLabels?.some((p) => p.includes('"same words" appears 2')),
  ).toBe(true);
  expect(found.repeatedLabels?.some((p) => p.startsWith("breadcrumb"))).toBe(
    true,
  );
});

test("the audit sees actions hidden behind three dots", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "desktop", "explicit viewport matrix");
  await page.setViewportSize({ width: 1440, height: 900 });
  await open(page, "organizer");
  await goToDestination(page, "overview");
  await settled(page);
  await page.evaluate(() => {
    const row = document.createElement("div");
    row.innerHTML =
      '<button type="button">\u22ef</button><button type="button" aria-haspopup="menu">Row</button><button type="button" aria-label="More actions"><svg width="12" height="12"></svg></button>';
    document.querySelector("main")!.prepend(row);
  });
  const found = await slopProblems(page, ["hiddenActions"]);
  expect(found.hiddenActions).toHaveLength(3);
});
