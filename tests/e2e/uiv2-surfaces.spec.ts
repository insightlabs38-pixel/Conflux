import { expect, test } from "@playwright/test";
import {
  accessible,
  chooseWorkspaceEvent,
  goToDestination,
  goToTask,
  noHorizontalOverflow,
  openWorkspace,
  settled,
  signIn,
  watch,
  capture,
} from "./support";

// Read-only tour of secondary/developer/builder surfaces (UIV2-B09). One test per surface and
// width: the event pages are large (about 10,000 elements, an axe scan of about 1.8 s each), so a
// single walk over nine surfaces needed 21 s of the shared 30 s budget alone and timed out under
// the parallel read-only tier. Every assertion is kept; each test signs in and opens the event
// itself (QUESTIONS.md 2026-10-07T04:10Z and 2026-10-07T09:05Z).
test.describe.configure({ mode: "parallel" }); // independent surfaces: workers share the file
const TASKS = [
  "Settings",
  "Stages",
  "Policies",
  "Rules",
  "Forms",
  "Public page",
];
// Integrations is an optional module, off on the reference event; its tour is in
// event-modules.spec.ts, which turns it on on an isolated fixture.
const DESTINATIONS = ["communications", "operations"];

for (const width of [390, 768, 1024, 1440]) {
  test(`developer and builder surfaces at ${width}px: API explorer`, async ({
    page,
  }, info) => {
    test.skip(
      info.project.name !== "desktop",
      "explicit viewport matrix runs once",
    );
    await page.setViewportSize({ width, height: 960 });
    await signIn(page, "organizer");
    const problems = watch(page);

    await page.goto("/app/?api=explorer");
    await expect(
      page.getByRole("heading", { name: "API explorer" }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Check service health" }).click();
    await expect(page.locator(".cx-api-endpoint")).toBeVisible();
    await page.getByRole("button", { name: "Send request" }).click();
    await expect(
      page.getByRole("region", { name: "API response" }),
    ).toBeVisible();
    await settled(page);
    await accessible(page);
    await noHorizontalOverflow(page);
    await capture(page, {
      path: `tests/e2e/artifacts/uiv2-b09-api-${width}.png`,
      fullPage: true,
    });

    expect(problems.filter((p) => !p.includes("/accounts/me/"))).toEqual([]);
  });

  for (const task of TASKS) {
    test(`developer and builder surfaces at ${width}px: ${task}`, async ({
      page,
    }, info) => {
      test.skip(
        info.project.name !== "desktop",
        "explicit viewport matrix runs once",
      );
      await page.setViewportSize({ width, height: 960 });
      await signIn(page, "organizer");
      const problems = watch(page);
      await page.goto("/app/");
      await openWorkspace(page);
      await chooseWorkspaceEvent(page);
      await goToDestination(page, "setup");
      await goToTask(page, task);
      await settled(page);
      await accessible(page);
      await noHorizontalOverflow(page);
      if (task === "Public page")
        await capture(page, {
          path: `tests/e2e/artifacts/uiv2-b09-page-builder-${width}.png`,
          fullPage: true,
        });
      expect(problems.filter((p) => !p.includes("/accounts/me/"))).toEqual([]);
    });
  }

  for (const dest of DESTINATIONS) {
    test(`developer and builder surfaces at ${width}px: ${dest}`, async ({
      page,
    }, info) => {
      test.skip(
        info.project.name !== "desktop",
        "explicit viewport matrix runs once",
      );
      await page.setViewportSize({ width, height: 960 });
      await signIn(page, "organizer");
      const problems = watch(page);
      await page.goto("/app/");
      await openWorkspace(page);
      await chooseWorkspaceEvent(page);
      await goToDestination(page, dest);
      await settled(page);
      await accessible(page);
      await noHorizontalOverflow(page);
      await capture(page, {
        path: `tests/e2e/artifacts/uiv2-b09-${dest}-${width}.png`,
        fullPage: true,
      });
      expect(problems.filter((p) => !p.includes("/accounts/me/"))).toEqual([]);
    });
  }
}
