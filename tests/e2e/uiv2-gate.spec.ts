import { expect, test, type Page } from "@playwright/test";
import {
  accessible,
  chooseWorkspaceEvent,
  goToDestination,
  noHorizontalOverflow,
  openWorkspace,
  settled,
  signIn,
  watch,
} from "./support";

// UIV2-B10 release gate: states, long content, focus visibility, themes and landmarks.
// Read-only: every state is produced with route interception, never server writes.
const WIDTHS = [360, 390, 768, 1024, 1440, 1920];
const desktopOnly = (info: { project: { name: string } }) =>
  test.skip(
    info.project.name !== "desktop",
    "explicit viewport matrix runs once",
  );

async function judgeQueue(page: Page) {
  await openWorkspace(page);
  const main = page.getByRole("region", { name: "Judging" });
  await main.getByLabel("Event").selectOption({ index: 1 });
  await main.getByLabel("Stage").selectOption({ index: 1 });
  await goToDestination(page, "queue");
}

const long = (n: number) =>
  `Extraordinarily-long-project-title-${"x".repeat(n)}`;

for (const width of [360, 390, 768, 1440]) {
  test(`judge queue copes with many long-named projects at ${width}px`, async ({
    page,
  }, info) => {
    desktopOnly(info);
    await page.setViewportSize({ width, height: 900 });
    await page.route("**/evaluation-plans/*/candidates/", (route) =>
      route.fulfill({
        json: Array.from({ length: 60 }, (_, i) => ({
          project: `p${i}`,
          name: `${long(90)} ${i}`,
          status:
            i % 3 === 0 ? "submitted" : i % 3 === 1 ? "drafted" : "pending",
        })),
      }),
    );
    await signIn(page, "judge-01");
    await judgeQueue(page);
    await expect(
      page.getByRole("list", { name: "Assigned projects" }),
    ).toBeVisible();
    await expect(
      page
        .getByRole("region", { name: "Review queue", exact: true })
        .getByText(/20 of 60/),
    ).toBeVisible();
    await accessible(page);
    await noHorizontalOverflow(page);
  });
}

test("error, empty, loading and denied states are explicit and accessible", async ({
  page,
  browser,
}, info) => {
  desktopOnly(info);
  await page.setViewportSize({ width: 390, height: 900 });
  await signIn(page, "organizer");
  await openWorkspace(page);
  // Error: one overview metric fails independently; the rest still render.
  await page.route("**/eligibility-reviews/", (route) =>
    route.fulfill({ status: 500, json: { detail: "boom" } }),
  );
  // Loading: judging progress answers slowly.
  await page.route("**/judge-workload/", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 1500));
    await route.continue();
  });
  await chooseWorkspaceEvent(page);
  const eligibility = page.getByRole("region", {
    name: "Eligibility workload",
  });
  await expect(eligibility.getByRole("alert")).toContainText("could not load");
  await expect(
    page
      .getByRole("region", { name: "Judging progress" })
      .getByText("Loading…"),
  ).toBeVisible();
  await accessible(page);
  await expect(
    page
      .getByRole("region", { name: "Judging progress" })
      .getByText(/ballots submitted/),
  ).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Registrations" }),
  ).toContainText("applications");
  await noHorizontalOverflow(page);

  // Denied: a judge whose events request is refused sees a message, not a blank page.
  const judge = await (await browser.newContext()).newPage();
  await judge.setViewportSize({ width: 390, height: 900 });
  await judge.route("**/judge-events/", (route) =>
    route.fulfill({
      status: 403,
      json: { detail: "You do not have permission." },
    }),
  );
  await signIn(judge, "judge-01");
  await openWorkspace(judge);
  await expect(judge.getByRole("alert")).toContainText("permission");
  await accessible(judge);

  // Empty: no candidates.
  const empty = await (await browser.newContext()).newPage();
  await empty.setViewportSize({ width: 390, height: 900 });
  await empty.route("**/evaluation-plans/*/candidates/", (route) =>
    route.fulfill({ json: [] }),
  );
  await signIn(empty, "judge-01");
  await judgeQueue(empty);
  await expect(
    empty.getByText("You have no projects assigned to review right now."),
  ).toBeVisible();
  await accessible(empty);
  await noHorizontalOverflow(empty);
});

test("judge scoring: keyboard focus stays visible and is never hidden by the sticky action bar", async ({
  page,
}, info) => {
  desktopOnly(info);
  await page.setViewportSize({ width: 390, height: 700 });
  await signIn(page, "judge-01");
  await judgeQueue(page);
  await page
    .getByRole("list", { name: "Assigned projects" })
    .getByRole("button")
    .first()
    .click();
  await expect(
    page.locator("#judge-scoring").getByRole("status").getByText("Draft saved"),
  ).toBeVisible();
  await page
    .locator("#judge-scoring")
    .getByRole("button", { name: "Recuse or report a conflict" })
    .focus();
  let visited = 0;
  for (let i = 0; i < 40; i++) {
    await page.keyboard.press("Tab");
    const state = await page.evaluate(() => {
      const element = document.activeElement as HTMLElement;
      if (!element || !element.closest("#judge-scoring")) return null;
      const box = element.getBoundingClientRect();
      const hit = document.elementFromPoint(
        box.x + box.width / 2,
        Math.min(box.y + box.height / 2, window.innerHeight - 1),
      );
      return {
        covered: !(hit && (hit === element || element.contains(hit))),
        outline: getComputedStyle(element).outlineStyle,
        offscreen: box.bottom > window.innerHeight || box.top < 0,
        name:
          element.textContent?.trim() ||
          element.getAttribute("aria-label") ||
          element.tagName,
      };
    });
    if (!state) break;
    visited++;
    expect(state.covered, `${state.name} obscured by sticky content`).toBe(
      false,
    );
    expect(state.offscreen, `${state.name} scrolled out of view`).toBe(false);
    expect(state.outline, `${state.name} focus indicator`).not.toBe("none");
  }
  expect(visited).toBeGreaterThan(4);
});

test("authenticated shell honours alternate themes, landmarks and reduced motion", async ({
  page,
}, info) => {
  desktopOnly(info);
  await page.setViewportSize({ width: 768, height: 900 });
  for (const role of ["organizer", "participant-01", "judge-01"]) {
    await signIn(page, role);
    const problems = watch(page);
    await openWorkspace(page);
    if (role === "organizer") await chooseWorkspaceEvent(page);
    else
      await page
        .getByRole("combobox", { name: "Event", exact: true })
        .selectOption({ index: 1 });
    await settled(page);
    await expect(page.getByRole("main")).toHaveCount(1);
    await expect(page.getByRole("heading", { level: 1 })).toHaveCount(1);
    await expect(
      page.getByRole("navigation", { name: /workspace|navigation/i }).first(),
    ).toBeVisible();
    const motion = await page.evaluate(() => {
      const button = document.querySelector("button, a") as HTMLElement;
      return getComputedStyle(button).transitionDuration;
    });
    expect(parseFloat(motion)).toBeLessThanOrEqual(0.01);
    for (const theme of ["dark", "minimal"]) {
      await page.evaluate((theme) => {
        document.documentElement.dataset.theme =
          theme === "dark" ? "dark" : "light";
        document.body.classList.toggle("theme-minimal", theme === "minimal");
      }, theme);
      await accessible(page);
      await noHorizontalOverflow(page);
    }
    await page.evaluate(() => {
      document.documentElement.dataset.theme = "light";
      document.body.classList.remove("theme-minimal");
    });
    expect(problems.filter((p) => !p.includes("/accounts/me/"))).toEqual([]);
    await page.request.post("/api/v1/accounts/logout/");
    await page.goto("/app/");
  }
});

for (const width of WIDTHS) {
  test(`skip link and sign-in landmarks at ${width}px`, async ({
    page,
  }, info) => {
    desktopOnly(info);
    await page.setViewportSize({ width, height: 800 });
    await page.goto("/app/");
    await page.keyboard.press("Tab");
    const first = page.locator(":focus");
    await expect(first).toBeVisible();
    await expect(page.getByRole("main")).toHaveCount(1);
    await accessible(page);
    await noHorizontalOverflow(page);
  });
}
