import { expect, test } from "@playwright/test";
import {
  accessible,
  chooseWorkspaceEvent,
  eventIds,
  goToDestination,
  goToTask,
  noHorizontalOverflow,
  openWorkspace,
  settled,
  signIn,
  watch,
} from "./support";

// UIV2-B10: finalized / published / submitted (immutable) states. Requires the lifecycle
// journey to have run first. In a plain `make demo-e2e` run `video: "on"` places this file
// in the same late worker group as lifecycle/scenes (Playwright groups by fixture options);
// `scripts/e2e-fast` runs it as an explicit step after the stateful group.
test.use(process.env.E2E_GROUP ? {} : { video: "on" });

for (const width of [360, 390, 768, 1024, 1440, 1920]) {
  test(`finalized, published and submitted states at ${width}px`, async ({
    page,
    browser,
  }, info) => {
    test.skip(
      info.project.name !== "desktop",
      "explicit viewport matrix runs once",
    );
    await page.setViewportSize({ width, height: 960 });

    // Judge: a submitted ballot is read-only.
    await signIn(page, "judge-03");
    const problems = watch(page);
    await openWorkspace(page);
    const main = page.getByRole("region", { name: "Judging" });
    await main.getByLabel("Event").selectOption({ index: 1 });
    await main.getByLabel("Stage").selectOption({ index: 1 });
    await goToDestination(page, "queue");
    const list = page.getByRole("list", { name: "Assigned projects" });
    await list.getByRole("button", { name: "Live Wire", exact: true }).click();
    const scoring = page.locator("#judge-scoring");
    await expect(scoring.getByText("Ballot submitted.")).toBeVisible();
    await expect(
      scoring.getByRole("button", { name: "Submit ballot" }),
    ).toHaveCount(0);
    await expect(scoring.getByText(/recorded and locked/)).toBeVisible();
    await expect(scoring.getByLabel("Score")).toHaveCount(0);
    await settled(page);
    await accessible(page);
    await noHorizontalOverflow(page);
    if ([390, 1440].includes(width))
      await page.screenshot({
        path: `tests/e2e/artifacts/uiv2-b10-judge-submitted-${width}.png`,
        fullPage: true,
      });
    expect(problems.filter((p) => !p.includes("/accounts/me/"))).toEqual([]);

    // Organizer: the decision is final and publication is complete.
    const organizer = await (await browser.newContext()).newPage();
    await organizer.setViewportSize({ width, height: 960 });
    await signIn(organizer, "organizer");
    const organizerProblems = watch(organizer);
    await openWorkspace(organizer);
    await chooseWorkspaceEvent(organizer);
    await goToDestination(organizer, "results");
    const room = organizer.getByRole("region", {
      name: "Deliberation and finalization",
    });
    await room
      .getByLabel("Award")
      .selectOption({ label: "Grand Prize (decided)" });
    await expect(room.getByText("Finalized", { exact: true })).toBeVisible();
    await expect(room.getByText(/this decision is immutable/)).toBeVisible();
    await expect(room.getByLabel("Override reason")).toHaveCount(0);
    await accessible(organizer);
    await noHorizontalOverflow(organizer);
    if ([390, 1440].includes(width))
      await organizer.screenshot({
        path: `tests/e2e/artifacts/uiv2-b10-deliberation-final-${width}.png`,
        fullPage: true,
      });
    await goToTask(organizer, "Publication");
    await expect(
      organizer
        .getByRole("list", { name: "Publication pipeline" })
        .locator('[data-state="done"]'),
    ).not.toHaveCount(0);
    await accessible(organizer);
    await noHorizontalOverflow(organizer);

    // Public: published results are reachable and accessible.
    const { event } = await eventIds(organizer);
    await organizer.goto(`/e/${event}/results/`);
    await expect(organizer.getByText("Live Wire").first()).toBeVisible();
    await accessible(organizer);
    await noHorizontalOverflow(organizer);
    if ([390, 1440].includes(width))
      await organizer.screenshot({
        path: `tests/e2e/artifacts/uiv2-b10-results-published-${width}.png`,
        fullPage: true,
      });
    expect(
      organizerProblems.filter((p) => !p.includes("/accounts/me/")),
    ).toEqual([]);
  });
}
