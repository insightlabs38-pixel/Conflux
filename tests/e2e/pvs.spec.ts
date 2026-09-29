import { expect, test, type Page } from "@playwright/test";
import {
  account,
  goToDestination,
  accessible,
  noHorizontalOverflow,
  openWorkspace,
  PASSWORD,
  settled,
  signIn,
  watch,
} from "./support";

/**
 * Human-facing PVS workflows, reached through the normal role workspaces.
 * Run after `scripts/demo-reset` (any checkpoint); every step tolerates
 * being repeated on already-changed state where practical.
 */

test.beforeEach(({ isMobile }, info) => {
  // Workflows mutate state and are recorded on desktop; mobile only checks layout.
  test.skip(isMobile && !/never overflow/.test(info.title));
});

const quiet = (problems: string[]) =>
  problems.filter((p) => !p.includes("/accounts/me/"));

async function chooseEvent(page: Page) {
  await page
    .locator("select")
    .filter({ has: page.locator("option", { hasText: "Choose an event" }) })
    .first()
    .selectOption({ index: 1 });
}

async function organizerEvent(page: Page) {
  await signIn(page, "organizer");
  await openWorkspace(page);
  await page.getByRole("button", { name: /^Demo \(/ }).click();
  await goToDestination(page, "eligibility");
  await expect(
    page.getByRole("region", { name: "Eligibility review queue" }),
  ).toBeVisible();
}

test("mentor claims and resolves a help request from the mentor desk", async ({
  page,
}) => {
  await signIn(page, "mentor");
  const problems = watch(page);
  await openWorkspace(page);
  await chooseEvent(page);
  const desk = page.getByRole("region", { name: "Mentor desk" });
  await expect(desk).toBeVisible();
  await desk.getByLabel("Headline").fill("Deployments and demos");
  await desk.getByRole("button", { name: "Save", exact: true }).click();
  await expect(desk.getByText("Availability saved.")).toBeVisible();
  const request = desk.locator(".cx-card", { hasText: "Deploying the demo" });
  if (await request.getByRole("button", { name: "Claim" }).count()) {
    await request.getByRole("button", { name: "Claim" }).click();
  }
  await request
    .getByLabel("Resolution note")
    .fill("Walked through the deploy.");
  await request.getByRole("button", { name: "Resolve" }).click();
  await expect(desk.getByText("Request resolved.")).toBeVisible();
  await settled(page);
  expect(quiet(problems)).toEqual([]);
});

test("volunteer checks a participant in by scanning their pass", async ({
  page,
  browser,
}) => {
  const who = await (await browser.newContext()).newPage();
  await signIn(who, "participant-05");
  const me = await (await who.request.get("/api/v1/accounts/me/")).json();
  const ws = me.memberships[0].workspace as string;
  const events = await (
    await who.request.get(`/api/v1/workspaces/${ws}/participant-events/`)
  ).json();
  const ev = events[0].public_id as string;
  await who.request.put(
    `/api/v1/workspaces/${ws}/events/${ev}/my-attendance/`,
    {
      data: { mode: "in_person" },
    },
  );
  const { token } = await (
    await who.request.get(`/api/v1/workspaces/${ws}/events/${ev}/my-pass/`)
  ).json();

  await signIn(page, "volunteer");
  const problems = watch(page);
  await openWorkspace(page);
  await chooseEvent(page);
  const ops = page.getByRole("region", { name: "On-site operations" });
  await ops.getByLabel("Scan or paste a participant pass").fill(token);
  await ops.getByRole("button", { name: "Check in" }).click();
  await expect(ops.getByText(account("participant-05"))).toBeVisible();
  await expect(ops.getByText(/checked in\.|already checked in/)).toBeVisible();
  // A volunteer gets the desk, not the organizer's layout controls.
  await expect(ops.getByText("Auto-assign")).toHaveCount(0);
  await ops.getByLabel("Scan or paste a participant pass").fill("not-a-pass");
  await ops.getByRole("button", { name: "Check in" }).click();
  await expect(ops.getByRole("alert")).toContainText(/Invalid pass/);
  expect(quiet(problems).filter((p) => !p.includes("400"))).toEqual([]);
});

test("participant RSVPs, books office hours and asks for a mentor", async ({
  page,
}) => {
  await signIn(page, "participant-01");
  const problems = watch(page);
  await openWorkspace(page);
  await chooseEvent(page);
  await goToDestination(page, "resources");
  const attending = page.getByRole("region", { name: "Attending in person" });
  await attending.getByLabel("Your RSVP").selectOption("remote");
  await expect(attending.getByText("RSVP saved: Remote.")).toBeVisible();
  await attending.getByLabel("Your RSVP").selectOption("in_person");
  await expect(attending.getByAltText("Check-in QR code")).toBeVisible();

  await goToDestination(page, "project");
  await page
    .getByRole("region", { name: "My projects" })
    .locator("select")
    .filter({ has: page.locator("option", { hasText: "Choose a project" }) })
    .selectOption({ index: 1 });
  const mentorship = page.getByRole("region", { name: "Mentorship" });
  await mentorship
    .getByLabel("What do you need help with?")
    .fill("Scaling the demo");
  await mentorship.getByRole("button", { name: "Request a mentor" }).click();
  await expect(mentorship.getByText("Scaling the demo")).toBeVisible();
  const book = mentorship.getByRole("button", { name: "Book" }).first();
  if (await book.count()) {
    await book.click();
    await expect(
      mentorship.getByRole("button", { name: "Cancel booking" }).first(),
    ).toBeVisible();
  }
  await settled(page);
  expect(quiet(problems)).toEqual([]);
});

test("participant requests a deadline exception and the organizer decides it", async ({
  page,
  browser,
}) => {
  await signIn(page, "participant-02");
  await openWorkspace(page);
  await chooseEvent(page);
  await goToDestination(page, "project");
  await page
    .getByRole("region", { name: "My projects" })
    .locator("select")
    .filter({ has: page.locator("option", { hasText: "Choose a project" }) })
    .selectOption({ index: 1 });
  const exception = page.getByRole("region", { name: "Deadline exception" });
  await exception
    .getByLabel("Why do you need more time?")
    .fill("Venue Wi-Fi outage.");
  await exception.getByRole("button", { name: "Request exception" }).click();
  await expect(
    exception.locator(".cx-badge", { hasText: "pending" }),
  ).toBeVisible();

  const org = await (await browser.newContext()).newPage();
  await organizerEvent(org);
  const queue = org.getByRole("region", {
    name: "Deadline exception requests",
  });
  const card = queue
    .locator(".cx-card", { hasText: "Venue Wi-Fi outage." })
    .first();
  await card.getByLabel("Note").fill("Approved for one hour.");
  await card.getByRole("button", { name: "Approve" }).click();
  await expect(
    card.locator(".cx-badge", { hasText: "approved" }),
  ).toBeVisible();
});

test("organizer publishes rules, participants acknowledge, counts update", async ({
  page,
  browser,
}) => {
  await organizerEvent(page);
  const problems = watch(page);
  await goToDestination(page, "setup");
  const rules = page.getByRole("region", { name: "Event rules" });
  const title = `Rules ${Date.now()}`;
  await rules.getByLabel("Title").fill(title);
  await rules.getByLabel("Rules text").fill("Ship it. Cite everything.");
  await rules.getByRole("button", { name: "Publish rules" }).click();
  await expect(
    rules.getByText(new RegExp(`${title} \\(v\\d+\\)`)),
  ).toBeVisible();
  await expect(rules.getByText(/0 acknowledged/)).toBeVisible();

  const part = await (await browser.newContext()).newPage();
  await signIn(part, "participant-03");
  await openWorkspace(part);
  await chooseEvent(part);
  await goToDestination(part, "resources");
  await part.getByRole("button", { name: /I have read and accept/ }).click();
  await expect(part.getByText("Acknowledged", { exact: true })).toBeVisible();

  await page.reload();
  await page.getByRole("button", { name: /^Demo \(/ }).click();
  await expect(
    page
      .getByRole("region", { name: "Event rules" })
      .getByText(/1 acknowledged/),
  ).toBeVisible();
  expect(quiet(problems)).toEqual([]);
});

test("organizer operations panels load, are labelled, and never overflow", async ({
  page,
}) => {
  await organizerEvent(page);
  const problems = watch(page);
  for (const name of [
    "Eligibility review queue",
    "On-site operations",
    "Judging logistics",
    "Deliberation and finalization",
    "Publication approval and corrections",
    "Deadline exception requests",
    "Mentor desk",
    "Post-event continuation",
  ]) {
    const destination = (
      {
        "Eligibility review queue": "eligibility",
        "On-site operations": "onsite",
        "Judging logistics": "judging",
        "Deliberation and finalization": "results",
        "Publication approval and corrections": "results",
        "Deadline exception requests": "eligibility",
        "Mentor desk": "participants",
        "Post-event continuation": "operations",
      } as Record<string, string>
    )[name];
    await goToDestination(page, destination);
    const panel = page.getByRole("region", { name });
    await panel.scrollIntoViewIfNeeded();
    await expect(panel).toBeVisible();
  }
  await settled(page);
  await noHorizontalOverflow(page);
  await accessible(page);
  expect(quiet(problems)).toEqual([]);
  void PASSWORD;
});

for (const role of ["participant-01", "judge-01", "mentor", "volunteer"]) {
  test(`${role}: PVS panels never overflow and are accessible`, async ({
    page,
  }) => {
    await signIn(page, role);
    const problems = watch(page);
    await openWorkspace(page);
    await chooseEvent(page);
    if (role === "participant-01") {
      await goToDestination(page, "project");
      await page
        .getByRole("region", { name: "My projects" })
        .locator("select")
        .filter({
          has: page.locator("option", { hasText: "Choose a project" }),
        })
        .selectOption({ index: 1 });
      await expect(
        page.getByRole("region", { name: "Mentorship" }),
      ).toBeVisible();
      await expect(
        page.getByRole("region", { name: "After the event" }),
      ).toBeVisible();
    }
    if (role === "judge-01") {
      const main = page.getByRole("region", { name: "Judging" });
      await main.getByLabel("Stage").selectOption({ index: 1 });
      await goToDestination(page, "schedule");
      await expect(
        page.getByRole("region", { name: "Your judging route" }),
      ).toBeVisible();
    }
    await settled(page);
    await noHorizontalOverflow(page);
    await accessible(page);
    expect(quiet(problems)).toEqual([]);
  });
}
