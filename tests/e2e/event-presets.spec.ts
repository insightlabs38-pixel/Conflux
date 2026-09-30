import { expect, test } from "@playwright/test";
import {
  accessible,
  eventIds,
  goToDestination,
  noHorizontalOverflow,
  openWorkspace,
  signIn,
} from "./support";

// Real defaults (PD-F001-B01-T03): creating from a starter format yields an event that is complete
// except for what only the organizer knows. Mutating (creates events), so it runs on an isolated
// fixture; the explicit viewport matrix covers the canonical desktop and narrow layouts.
for (const width of [390, 1440]) {
  test(`a starter format creates an event with real defaults at ${width}`, async ({
    page,
  }, info) => {
    test.skip(info.project.name !== "desktop", "explicit viewport matrix");
    await page.setViewportSize({ width, height: 900 });
    await signIn(page, "organizer");
    await openWorkspace(page);
    const { workspace } = await eventIds(page);
    await goToDestination(page, "setup");
    // The disclosure is open while events load and closes once there are some: wait for that.
    await expect(
      page
        .getByRole("navigation", { name: "Workspace events" })
        .getByRole("button")
        .first(),
    ).toBeVisible();
    await page.getByText("Create a new event or start from a template").click();

    const format = page
      .getByRole("listitem")
      .filter({ hasText: "Hackathon" })
      .filter({ has: page.getByRole("button", { name: /^Create hackathon/ }) });
    // What the format starts with is visible before anything is created.
    await expect(format).toContainText(
      /Starts with: 2 days, open registration, teams of 1–5, required evidence: repository, published rubric: Innovation, Execution, Impact\./,
    );
    await expect(format).not.toContainText("Tracks:");
    await noHorizontalOverflow(page);

    const stamp = Date.now();
    const name = `Presets ${width} ${stamp}`;
    const slug = `presets-${width}-${stamp}`;
    await format.getByLabel("Event name").fill(name);
    await format.getByLabel("Event slug").fill(slug);
    await format.getByRole("button", { name: /^Create hackathon/ }).click();
    await expect(
      page
        .getByRole("navigation", { name: "Workspace events" })
        .getByRole("button", { name: `${name} (draft)` }),
    ).toBeVisible();

    // The persisted event, read back through the API: nothing to clean up but the dates and judges.
    const events = await (
      await page.request.get(`/api/v1/workspaces/${workspace}/events/`)
    ).json();
    const created = events.find((e: { slug: string }) => e.slug === slug);
    const base = `/api/v1/workspaces/${workspace}/events/${created.public_id}/`;
    const checklist = await (
      await page.request.get(base + "operations/checklist/")
    ).json();
    const failing = checklist.items
      .filter((item: { passed: boolean }) => !item.passed)
      .map((item: { id: string }) => item.id)
      .sort();
    expect(failing).toEqual(["event_dates", "judging_pools"]);
    const stages = await (await page.request.get(base + "stages/")).json();
    const plans = await (
      await page.request.get(
        base + `stages/${stages[1].public_id}/evaluation-plans/`,
      )
    ).json();
    expect(plans[0].current_rubric_version).toBe(1);
    await accessible(page);
  });
}
