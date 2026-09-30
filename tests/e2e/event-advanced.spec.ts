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
} from "./support";

// Advanced configuration stays collapsed until a feature requiring it is turned on
// (PD-F001-B01-T02): expert tabs sit behind an Advanced disclosure, the tabs of modules that are
// off are not offered, and their panels are never mounted, so merely looking at an event loads and
// creates nothing (the community voting panel used to create a voting plan on first view).
// Mutating (turns a module on), so it runs on an isolated fixture.
test("advanced tabs and optional module panels appear only when asked for or turned on", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "desktop", "explicit viewport matrix");
  const votingPlanRequests: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("/voting-plan/"))
      votingPlanRequests.push(request.method());
  });
  await page.setViewportSize({ width: 390, height: 900 });
  await signIn(page, "organizer");
  await openWorkspace(page);
  await chooseWorkspaceEvent(page);
  const { workspace, event } = await eventIds(page);
  const plan = async () =>
    (
      await page.request.get(
        `/api/v1/workspaces/${workspace}/modules/?event=${event}`,
      )
    ).json();
  const voting = (await plan()).modules.find(
    (m: { key: string }) => m.key === "community_voting",
  );
  expect(
    [voting.in_use, voting.explicit],
    "voting starts off and empty",
  ).toEqual([false, null]);

  // Setup: the base tabs only; Policies waits behind Advanced (narrow layout).
  await goToDestination(page, "setup");
  const setup = page.getByRole("tablist", { name: "Event setup" });
  await expect(setup.getByRole("tab", { name: /^Settings/ })).toBeVisible();
  await expect(setup.getByRole("tab", { name: /^Policies/ })).toHaveCount(0);
  const advanced = page.getByRole("button", { name: /^Advanced \(2\)$/ });
  await expect(advanced).toHaveAttribute("aria-expanded", "false");
  await noHorizontalOverflow(page);
  await accessible(page);
  await advanced.click();
  await expect(setup.getByRole("tab", { name: /^Policies/ })).toBeVisible();
  await noHorizontalOverflow(page);
  await accessible(page);

  // Judging: no Community voting tab, and looking at it created nothing.
  await goToDestination(page, "judging");
  await settled(page);
  const judging = page.getByRole("tablist", { name: "Judging tools" });
  await expect(
    judging.getByRole("tab", { name: /^Community voting/ }),
  ).toHaveCount(0);
  expect(votingPlanRequests).toEqual([]);
  expect(
    (await plan()).modules.find(
      (m: { key: string }) => m.key === "community_voting",
    ).in_use,
  ).toBe(false);

  // Turn it on from Features: the tab appears and the link opens it (wide layout).
  await page.setViewportSize({ width: 1440, height: 900 });
  await goToDestination(page, "setup");
  await goToTask(page, "Features");
  await page
    .getByRole("button", { name: /^Turn on community voting$/i })
    .click();
  await page.getByRole("link", { name: /^Open community voting$/i }).click();
  await expect(page).toHaveURL(/\/judging\?.*section=CommunityVotingBuilder/);
  await expect(
    judging.getByRole("tab", { name: /^Community voting/, selected: true }),
  ).toBeVisible();
  await expect(page.getByText("Identity mode")).toBeVisible();
  await settled(page);
  await accessible(page);
  // Only now does the panel load (and, as it always did, create the plan with its defaults).
  expect(votingPlanRequests).toContain("GET");
  expect(
    (await plan()).modules.find(
      (m: { key: string }) => m.key === "community_voting",
    ),
  ).toMatchObject({ enabled: true, in_use: true });
});
