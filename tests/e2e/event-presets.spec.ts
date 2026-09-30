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

    const form = page.locator("form").filter({
      has: page.getByRole("heading", { name: "Create event", exact: true }),
    });
    await form.getByRole("radio", { name: /^Hackathon/ }).check();
    // What the format starts with is visible before anything is created.
    await expect(form).toContainText(
      /Starts with: 2 days, open registration, teams of 1–5, required evidence: repository, published rubric: Innovation, Execution, Impact\./,
    );
    await expect(form).not.toContainText("Tracks:");
    await noHorizontalOverflow(page);

    // A name is enough: the address is derived, and a base decision (registration) is one field.
    const stamp = Date.now();
    const name = `Presets ${width} ${stamp}`;
    const slug = `presets-${width}-${stamp}`;
    await form.getByLabel("Name", { exact: true }).fill(name);
    await form.getByLabel("Registration").selectOption("invite_only");
    await form.getByRole("button", { name: /^Create hackathon/ }).click();
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
    // Invite-only registration adds its own item: someone has to be invited.
    expect(failing).toEqual([
      "event_dates",
      "judging_pools",
      "registration_invites",
    ]);
    // Derived address, the chosen mode, and everything else from the format.
    const registration = await (
      await page.request.get(base + "configuration/?key=registration.mode")
    ).json();
    expect(registration.settings[0]).toMatchObject({
      value: "invite_only",
      baseline: "open",
      source: "overridden",
    });
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

// Edge states of the create form (PD-F001-B01-T01): when the list of formats cannot load the form
// says so, offers a retry, keeps the blank draft possible, and recovers without a reload.
test("the create form explains a failed format list and recovers on retry", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "desktop", "explicit viewport matrix");
  await page.setViewportSize({ width: 1440, height: 900 });
  await signIn(page, "organizer");
  let fail = true;
  await page.route("**/event-templates/library/", (route) =>
    fail
      ? route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ detail: "Formats unavailable" }),
        })
      : route.continue(),
  );
  await openWorkspace(page);
  await eventIds(page); // the workspace has loaded
  await goToDestination(page, "setup");
  await expect(
    page
      .getByRole("navigation", { name: "Workspace events" })
      .getByRole("button")
      .first(),
  ).toBeVisible();
  await page.getByText("Create a new event or start from a template").click();
  const form = page.locator("form").filter({
    has: page.getByRole("heading", { name: "Create event", exact: true }),
  });
  await expect(form.getByRole("alert")).toBeVisible();
  await expect(form.getByRole("radio", { name: /^No format/ })).toBeChecked();
  fail = false;
  await form.getByRole("button", { name: "Try again" }).click();
  await expect(form.getByRole("radio", { name: /^Hackathon/ })).toBeVisible();
  await expect(form.getByRole("alert")).toHaveCount(0);
  await accessible(page);
});
