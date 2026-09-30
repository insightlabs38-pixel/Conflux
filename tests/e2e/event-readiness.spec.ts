import { expect, test } from "@playwright/test";
import {
  accessible,
  eventIds,
  goToDestination,
  noHorizontalOverflow,
  openWorkspace,
  settled,
  signIn,
} from "./support";

// One readiness surface (PD-F001-B01-T05): Setup, the overview and the operations center show the
// same server list, every open item links to where it is fixed, and fixing it is reflected. Mutating
// (creates an event and edits its dates), so it runs on an isolated fixture.
for (const width of [390, 1440]) {
  test(`readiness explains what is missing and where to fix it at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    await openWorkspace(page);
    const { workspace } = await eventIds(page);

    // A fresh event from a format: complete except the dates and the judges.
    const stamp = Date.now();
    const created = await page.request.post(
      `/api/v1/workspaces/${workspace}/event-templates/library/hackathon/instantiate/`,
      {
        data: {
          name: `Ready ${width} ${stamp}`,
          slug: `ready-${width}-${stamp}`,
        },
      },
    );
    expect(created.status()).toBe(201);
    const event = (await created.json()).public_id as string;
    await page.goto(`/app/w/${workspace}/setup?event=${event}`);
    await settled(page);

    const readiness = page.getByRole("region", { name: "Event readiness" });
    await expect(readiness).toContainText("Not ready: blockers remain");
    await expect(readiness).toContainText("Set the event start and end dates.");
    // Warnings follow blockers; passed checks are collapsed.
    await expect(readiness).toContainText("No judges assigned for:");
    await expect(readiness.locator("details")).not.toHaveAttribute("open", "");
    await noHorizontalOverflow(page);
    await accessible(page);

    // The overview lists the same unresolved items as actions, each linking to its fix.
    await goToDestination(page, "overview");
    const needsAction = page.getByRole("region", { name: "Needs action" });
    await expect(needsAction).toContainText(
      "Set the event start and end dates.",
    );
    await needsAction
      .getByRole("link", { name: /Set the event start and end dates/ })
      .click();
    await expect(page).toHaveURL(/\/setup\?.*section=settings/);
    await expect(page.getByLabel("Start", { exact: true })).toBeVisible();

    // Fixing it is reflected after checking again (dates are the only blocker).
    await page.getByLabel("Start", { exact: true }).fill("2027-03-05T09:00");
    await page.getByLabel("End", { exact: true }).fill("2027-03-07T09:00");
    await page.getByRole("button", { name: "Save settings" }).click();
    await expect(readiness).not.toContainText("Not ready: blockers remain");
    await expect(readiness).toContainText("Can launch, with warnings");
    await expect(readiness).not.toContainText(
      "Set the event start and end dates.",
    );

    // The judging fix link opens the tab that holds it.
    await readiness.getByRole("link", { name: /Fix judging pools/ }).click();
    await expect(page).toHaveURL(/\/judging\?.*section=EvaluationBuilder/);
    await expect(
      page.getByRole("tab", { name: /Rubrics and plans/, selected: true }),
    ).toBeVisible();

    // Operations shows the same list, from the same server answer.
    await goToDestination(page, "operations");
    await expect(
      page.getByRole("region", { name: "Event readiness" }),
    ).toContainText("Can launch, with warnings");
    await accessible(page);
    const body = await (
      await page.request.get(
        `/api/v1/workspaces/${workspace}/events/${event}/readiness/`,
      )
    ).json();
    // No blocker is left, and the judge pool is still open (only the organizer can name judges).
    const open = body.items
      .filter((i: { passed: boolean }) => !i.passed)
      .map((i: { id: string }) => i.id);
    expect(body.status).toBe("warning");
    expect(open).toContain("judging_pools");
    expect(
      body.items.filter(
        (i: { passed: boolean; severity: string }) =>
          !i.passed && i.severity === "blocker",
      ),
    ).toEqual([]);
  });
}
