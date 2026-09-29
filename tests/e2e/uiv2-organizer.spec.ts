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
} from "./support";

// Read-only tour of the organizer operations surfaces. It runs after the
// lifecycle (alphabetical order) so results and the finalized decision exist.
for (const width of [390, 768, 1024, 1440]) {
  test(`organizer operations at ${width}px`, async ({ page }, info) => {
    test.skip(
      info.project.name !== "desktop",
      "explicit viewport matrix runs once",
    );
    await page.setViewportSize({ width, height: 960 });
    await signIn(page, "organizer");
    const problems = watch(page);
    await openWorkspace(page);
    await chooseWorkspaceEvent(page);
    await expect(
      page.getByRole("region", { name: "Needs action" }),
    ).toBeVisible();
    for (const metric of [
      "Registrations",
      "Eligibility workload",
      "Judging progress",
      "Results and publication",
      "On-site readiness",
    ])
      await expect(page.getByRole("region", { name: metric })).toBeVisible();
    await settled(page);
    await accessible(page);
    await noHorizontalOverflow(page);
    await page.screenshot({
      path: `tests/e2e/artifacts/uiv2-b08-overview-${width}.png`,
      fullPage: true,
    });

    await goToDestination(page, "eligibility");
    const queue = page.getByRole("region", {
      name: "Eligibility review queue",
    });
    await expect(
      queue.getByRole("group", { name: "Filter reviews by status" }),
    ).toBeVisible();
    await accessible(page);
    await noHorizontalOverflow(page);
    await page.screenshot({
      path: `tests/e2e/artifacts/uiv2-b08-eligibility-${width}.png`,
      fullPage: true,
    });

    await goToDestination(page, "judging");
    await goToTask(page, "Logistics");
    await expect(
      page.getByRole("region", { name: "Judging logistics" }),
    ).toBeVisible();
    await accessible(page);
    await noHorizontalOverflow(page);

    await goToDestination(page, "results");
    const room = page.getByRole("region", {
      name: "Deliberation and finalization",
    });
    await room
      .getByLabel("Award")
      .selectOption({ label: "Grand Prize (decided)" });
    await expect(
      room.getByRole("list", { name: "Deliberation progress" }),
    ).toBeVisible();
    await accessible(page);
    await noHorizontalOverflow(page);
    await page.screenshot({
      path: `tests/e2e/artifacts/uiv2-b08-deliberation-${width}.png`,
      fullPage: true,
    });
    await goToTask(page, "Publication");
    await expect(
      page.getByRole("list", { name: "Publication pipeline" }),
    ).toBeVisible();
    await accessible(page);
    await noHorizontalOverflow(page);
    await page.screenshot({
      path: `tests/e2e/artifacts/uiv2-b08-publication-${width}.png`,
      fullPage: true,
    });

    await goToDestination(page, "onsite");
    const desk = page.getByRole("region", { name: "On-site operations" });
    await expect(desk.getByLabel("Search participants")).toBeVisible();
    await desk.getByLabel("Search participants").fill("participant-01");
    await expect(
      desk.getByRole("group", { name: "Filter attendance" }),
    ).toBeVisible();
    await accessible(page);
    await noHorizontalOverflow(page);
    await page.screenshot({
      path: `tests/e2e/artifacts/uiv2-b08-onsite-${width}.png`,
      fullPage: true,
    });
    expect(problems.filter((p) => !p.includes("/accounts/me/"))).toEqual([]);
  });
}
