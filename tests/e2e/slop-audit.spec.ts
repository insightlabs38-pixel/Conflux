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
  "recordGrids",
  "alarmColors",
  "fakeAi",
  "precision",
  "opaqueIds",
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

test("the audit sees boxed records laid out three across", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "desktop", "explicit viewport matrix");
  await page.setViewportSize({ width: 1440, height: 900 });
  await open(page, "organizer");
  await goToDestination(page, "participants");
  await settled(page);
  await page.evaluate(() => {
    const list = document.createElement("ul");
    list.style.cssText =
      "display:grid;grid-template-columns:repeat(3,1fr);gap:8px;list-style:none;padding:0";
    list.innerHTML = [1, 2, 3]
      .map(
        (n) =>
          `<li style="border:1px solid #888;padding:8px;height:40px">Person ${n}</li>`,
      )
      .join("");
    document.querySelector("main")!.prepend(list);
  });
  const found = await slopProblems(page, ["recordGrids"]);
  expect(found.recordGrids).toHaveLength(1);
});

// The work the organizer does record by record (registrations, projects) is a sortable table, not a
// grid of boxed items (V-SLOP-14). Reference tables (permissions, extensions, completeness) are read,
// not worked through, and are the recorded exception.
for (const width of [390, 1440])
  for (const task of ["Registration", "Projects"])
    test(`organizer ${task} are rows of a sortable table at ${width}`, async ({
      page,
    }, info) => {
      test.skip(info.project.name !== "desktop", "explicit viewport matrix");
      await page.setViewportSize({ width, height: 900 });
      await open(page, "organizer");
      await goToDestination(page, "participants");
      await goToTask(page, task);
      await settled(page);
      await stable(page);
      const table = page.locator("main table").first();
      await expect(table.locator("tbody tr").nth(9)).toBeAttached();
      await expect(table.locator("th[aria-sort]").first()).toBeAttached();
      expect(await slopProblems(page, ["recordGrids", "kpiCards"])).toEqual({});
    });

test("the audit sees red outside a failure and a page of alarms", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "desktop", "explicit viewport matrix");
  await page.setViewportSize({ width: 1440, height: 900 });
  await open(page, "organizer");
  await goToDestination(page, "overview");
  await settled(page);
  const one = await page.evaluate(() => {
    const row = document.createElement("div");
    row.innerHTML =
      '<p style="color:var(--err)">Delete later</p><div role="alert"><p style="color:var(--err)">It failed</p></div><div class="cx-consequence"><button class="cx-button cx-button--danger" type="button">Remove</button></div><button class="cx-button cx-button--danger" type="button">Delete everything</button>';
    document.querySelector("main")!.prepend(row);
    return true;
  });
  expect(one).toBe(true);
  const found = await slopProblems(page, ["alarmColors"]);
  // the paragraph and the red button outside a confirmation are reported; the alert and the confirm are not
  expect(found.alarmColors).toHaveLength(2);
  await page.evaluate(() => {
    const row = document.createElement("div");
    row.innerHTML = Array.from(
      { length: 7 },
      (_, n) => `<p style="color:var(--err)">Warning ${n}</p>`,
    ).join("");
    document.querySelector("main")!.prepend(row);
  });
  const many = await slopProblems(page, ["alarmColors"]);
  expect(
    many.alarmColors?.some((p) => p.includes("red marks on one page")),
  ).toBe(true);
});

test("the audit sees an assistant look on a deterministic workflow", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "desktop", "explicit viewport matrix");
  await page.setViewportSize({ width: 1440, height: 900 });
  await open(page, "organizer");
  await goToDestination(page, "judging");
  await settled(page);
  await page.evaluate(() => {
    const row = document.createElement("div");
    row.innerHTML =
      '<button type="button">\u2728 Suggest scores</button><button type="button" aria-label="Ask AI about this stage">Ask</button><button type="button">Email magic link</button><a href="#x">AI Tutor</a>';
    document.querySelector("main")!.prepend(row);
  });
  const found = await slopProblems(page, ["fakeAi"]);
  // the sparkle button and the AI-named control; a real magic-link sign-in and a project link are not
  expect(found.fakeAi).toHaveLength(2);
});

test("the audit sees a figure with false precision", async ({ page }, info) => {
  test.skip(info.project.name !== "desktop", "explicit viewport matrix");
  await page.setViewportSize({ width: 1440, height: 900 });
  await open(page, "organizer");
  await goToDestination(page, "results");
  await settled(page);
  await page.evaluate(() => {
    const row = document.createElement("div");
    row.innerHTML =
      "<p>Score 0.8333333 of 5</p><p>Mean 4.25 and version 1.2.3 at 10:04:05.123</p><code>0.123456</code>";
    document.querySelector("main")!.prepend(row);
  });
  const found = await slopProblems(page, ["precision"]);
  expect(found.precision).toHaveLength(1);
  expect(found.precision?.[0]).toContain("0.8333333");
});

test("the audit sees a box that asks for an opaque id", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "desktop", "explicit viewport matrix");
  await page.setViewportSize({ width: 1440, height: 900 });
  await open(page, "organizer");
  await goToDestination(page, "results");
  await settled(page);
  await page.evaluate(() => {
    const row = document.createElement("div");
    row.innerHTML = `
      <input placeholder="User public ID" />
      <label>Team ID <input /></label>
      <input aria-label="Reference" value="3f2b8c1e-5a4d-4e0a-9b7c-1d2e3f405162" />
      <label>Field id <input data-authored-key /></label>
      <label>Find person <input type="search" /></label>
      <label>Valid ID check <input readonly /></label>
      <select aria-label="Project id"><option>Alpha</option></select>`;
    document.querySelector("main")!.prepend(row);
  });
  const found = await slopProblems(page, ["opaqueIds"]);
  // the placeholder, the labelled box and the box holding a uuid; the authored key, a name search,
  // a read-only box and a select (a choice by name) are not reported
  expect(found.opaqueIds).toHaveLength(3);
});
