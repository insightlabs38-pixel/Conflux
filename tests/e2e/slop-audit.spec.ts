import { expect, test, type Page } from "@playwright/test";
import {
  chooseWorkspaceEvent,
  eventIds,
  goToDestination,
  openWorkspace,
  settled,
  signIn,
} from "./support";
import { slopProblems, type SlopRule } from "./slop";

// The anti-slop gate of spec 004 (V-SLOP-1..) measured on the live pages of every role and on the
// public site, at 390 and 1440. Read-only. One test per page and width: pages are large and each
// is measured on its own. A rule is added to RULES by the task that implements it.
const RULES: SlopRule[] = ["gradient", "iconTile"];

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
        expect(await slopProblems(page, RULES)).toEqual({});
      });
    }
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
