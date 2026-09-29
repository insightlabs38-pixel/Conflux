import { chooseWorkspaceEvent } from "./support";
import { goToDestination, goToTask } from "./support";
import path from "node:path";
import { expect, test, type Page } from "@playwright/test";
import {
  account,
  openWorkspace,
  PASSWORD,
  settled,
  signIn,
  watch,
} from "./support";

/**
 * The recorded demo lifecycle — create → submit → judge → publish — driven only
 * through the UI and addressed by semantic identities (usernames, names).
 * Precondition: `scripts/demo-reset submitted` (participant-24 is a "live"
 * participant: approved, no team). Re-run the reset before repeating.
 */
test.describe.configure({ mode: "serial" });
test.use({ video: "on" });
const shot = async (page: Page, name: string, region?: string) => {
  const target = region
    ? page.getByRole("region", { name: region, exact: true })
    : page;
  await target.screenshot({
    path: path.join(__dirname, "artifacts/scenes", `${name}.png`),
  });
};
test.skip(({ isMobile }) => isMobile, "desktop-only recorded journey");

const LIVE = "participant-24";
const PROJECT = "Live Wire";

async function chooseEvent(page: Page) {
  const select = page
    .locator("select")
    .filter({ has: page.locator("option", { hasText: "Choose an event" }) })
    .first();
  await select.selectOption({ index: 1 });
}

test("participant creates a team, submits, and receives a signed receipt", async ({
  page,
}) => {
  await signIn(page, LIVE);
  const problems = watch(page);
  await openWorkspace(page);
  await chooseEvent(page);
  await goToDestination(page, "resources");
  await goToTask(page, "Sponsor challenges");
  await expect(
    page.getByRole("region", { name: "Sponsor challenges" }),
  ).toContainText("Sponsor API documentation");
  await goToDestination(page, "team");
  await page.getByLabel("Team name").fill("Team Live Wire");
  await page.getByRole("button", { name: "Create team" }).click();
  await expect(page.getByRole("region", { name: "My team" })).toContainText(
    "Team Live Wire",
  );
  await goToDestination(page, "project");
  await page.getByLabel("Project name").fill(PROJECT);
  await page.getByRole("button", { name: "Create project" }).click();

  await goToTask(page, "Evidence & checks");
  const evidence = page.getByRole("region", { name: "Project artifacts" });
  await evidence
    .getByLabel("Title", { exact: true })
    .first()
    .fill("Live Wire technical brief");
  await evidence
    .getByRole("combobox", { name: "Kind", exact: true })
    .first()
    .selectOption("document");
  await evidence
    .getByRole("combobox", { name: "Visibility", exact: true })
    .first()
    .selectOption("public");
  await evidence.getByLabel("File", { exact: true }).setInputFiles({
    name: "technical-brief.txt",
    mimeType: "text/plain",
    buffer: Buffer.from(
      "Live Wire connects local volunteers with neighborhood needs.\nStack: Django REST API and an accessible web client.\nDemo evidence: offline operation, auditable submissions and isolated judging.\n",
    ),
  });
  await evidence.getByRole("button", { name: "Upload", exact: true }).click();
  await expect(
    evidence.getByText("Evidence uploaded and ready."),
  ).toBeVisible();
  // Re-open the project so the submission picker loads the newly uploaded evidence.
  const projects = page
    .getByRole("region", { name: "My projects" })
    .locator("select")
    .filter({
      has: page.locator("option", { hasText: "Choose a project" }),
    });
  await projects.selectOption("");
  await projects.selectOption({ label: PROJECT });
  await goToTask(page, "Submission");
  const submission = page.getByRole("region", {
    name: "Submission",
    exact: true,
  });
  await submission.getByLabel("Stage").selectOption({ index: 1 });
  await submission.getByLabel("Live Wire technical brief").check();
  await submission
    .getByLabel("Submission notes")
    .fill("Built live during the demo.");
  await expect(submission.getByText("Draft saved")).toBeVisible();
  await submission.getByRole("button", { name: "Finalize submission" }).click();
  await expect(submission.getByText(/Submission finalized/)).toBeVisible();
  await expect(submission.getByText("Signed submission receipt")).toBeVisible();
  await submission
    .getByText("Signature and technical proof", { exact: true })
    .click();
  await expect(
    submission.getByRole("textbox", { name: "Receipt token", exact: true }),
  ).toBeVisible();
  await expect(
    submission.getByRole("textbox", { name: "Receipt token", exact: true }),
  ).toHaveValue(/.{20,}/);
  await submission
    .getByText("Signature and technical proof", { exact: true })
    .click();
  // Support workflows stay reachable through the project task navigation.
  await goToTask(page, "Support");
  await expect(
    page.getByRole("region", { name: "Deadline exception" }),
  ).toBeVisible();
  await expect(page.getByRole("region", { name: "Mentorship" })).toBeVisible();
  await goToTask(page, "Submission");
  await shot(page, "participant-submission-receipt", "Submission");
  await settled(page);
  expect(problems.filter((p) => !p.includes("/accounts/me/"))).toEqual([]);
});

test("organizer requests changes; participant remediates; organizer approves", async ({
  browser,
}) => {
  const org = await (
    await browser.newContext({
      recordVideo: { dir: test.info().outputPath("clips") },
    })
  ).newPage();
  await signIn(org, "organizer");
  await openWorkspace(org);
  await chooseWorkspaceEvent(org);
  await goToDestination(org, "eligibility");
  const queue = org.getByRole("region", { name: "Eligibility review queue" });
  await queue.getByLabel("Open a project").selectOption({ label: PROJECT });
  await queue.getByLabel("Finding").fill("Describe what the project does.");
  await queue.getByRole("button", { name: "Add finding" }).click();
  await queue.getByLabel("Outcome").selectOption("needs_remediation");
  await queue.getByRole("button", { name: "Record decision" }).click();
  await expect(
    queue.locator(".cx-badge", { hasText: "Changes requested" }).first(),
  ).toBeVisible();

  const part = await (
    await browser.newContext({
      recordVideo: { dir: test.info().outputPath("clips") },
    })
  ).newPage();
  await signIn(part, LIVE);
  await openWorkspace(part);
  await chooseEvent(part);
  await goToDestination(part, "project");
  await part
    .getByRole("region", { name: "My projects" })
    .locator("select")
    .filter({ has: part.locator("option", { hasText: "Choose a project" }) })
    .selectOption({ label: PROJECT });
  await goToTask(part, "Project story");
  await part
    .getByLabel("Project description", { exact: true })
    .fill(
      "Live Wire connects local volunteers with neighborhood needs. Built with a Django REST API and an accessible web client.",
    );
  await part
    .getByRole("button", { name: "Save project story", exact: true })
    .click();
  await expect(
    part.getByText("Project story saved.", { exact: true }),
  ).toBeVisible();
  await goToTask(part, "Eligibility");
  const findings = part.getByRole("region", { name: "Eligibility review" });
  await expect(findings).toContainText("Describe what the project does.");
  await findings
    .getByLabel("What did you change?")
    .fill("Added a description.");
  await findings
    .getByRole("button", { name: "Mark as fixed and resubmit for review" })
    .click();
  await expect(findings).toContainText("Pending review");

  await org.reload(); // the workspace and event survive a refresh via the URL
  await chooseWorkspaceEvent(org);
  const again = org.getByRole("region", { name: "Eligibility review queue" });
  await again.getByRole("button", { name: `Review ${PROJECT}` }).click();
  await again.getByRole("button", { name: "Mark resolved" }).click();
  await expect(
    again.locator(".cx-badge", { hasText: "resolved" }).first(),
  ).toBeVisible();
  await again.getByLabel("Outcome").selectOption("cleared");
  await again.getByRole("button", { name: "Record decision" }).click();
  await expect(
    again.locator(".cx-badge", { hasText: "Cleared" }).first(),
  ).toBeVisible();
  await shot(part, "participant-remediation", "Eligibility review");
  await shot(org, "organizer-eligibility", "Eligibility review queue");
  await part.reload();
  await chooseEvent(part);
  await goToDestination(part, "project");
  await part
    .getByRole("region", { name: "My projects" })
    .locator("select")
    .filter({ has: part.locator("option", { hasText: "Choose a project" }) })
    .selectOption({ label: PROJECT });
  await goToTask(part, "Eligibility");
  await expect(
    part.getByRole("region", { name: "Eligibility review" }),
  ).toContainText("cleared", { ignoreCase: true });
  await org.context().close();
  await part.context().close();
  for (const [name, page] of [
    ["remediation-organizer", org],
    ["remediation-participant", part],
  ] as const) {
    await test.info().attach(name, {
      path: await page.video()!.path(),
      contentType: "video/webm",
    });
  }
});

for (const judge of ["judge-01", "judge-02", "judge-03"]) {
  test(`${judge} inspects and scores ${PROJECT}`, async ({ page }) => {
    await signIn(page, judge);
    const problems = watch(page);
    await openWorkspace(page);
    const main = page.getByRole("region", { name: "Judging" });
    await main.getByLabel("Event").selectOption({ index: 1 });
    await main.getByLabel("Stage").selectOption({ index: 1 });
    await goToDestination(page, "queue");
    await expect(
      page.getByRole("region", { name: "Your assignments" }),
    ).toBeVisible();
    await goToDestination(page, "schedule");
    await expect(
      page.getByRole("region", { name: "Your judging route" }),
    ).toBeVisible();
    await goToDestination(page, "queue");
    await page.getByRole("button", { name: PROJECT }).click();
    await expect(
      page.getByRole("region", { name: "Submitted artifacts" }),
    ).toBeVisible();
    const scores = page.getByLabel("Score");
    const count = await scores.count();
    for (let i = 0; i < count; i++)
      await scores.nth(i).fill(String(6 + (i % 3)));
    if (judge === "judge-01") {
      const inspector = page.getByRole("region", {
        name: "Submitted artifacts",
      });
      await inspector.getByRole("button", { name: "Inspect safely" }).click();
      await expect(
        inspector.getByText("Detected type:", { exact: false }),
      ).toBeVisible();
      await shot(page, "judge-artifact-inspector", "Submitted artifacts");
      await scores.first().scrollIntoViewIfNeeded();
      await shot(page, "judge-scoring");
    }
    await page.getByRole("button", { name: "Submit ballot" }).click();
    await expect(
      page
        .getByRole("region", { name: "Review queue", exact: true })
        .locator("li")
        .filter({
          has: page.getByRole("button", { name: PROJECT, exact: true }),
        })
        .getByText("submitted", { exact: true }),
    ).toBeVisible();
    await settled(page);
    expect(problems.filter((p) => !p.includes("/accounts/me/"))).toEqual([]);
  });
}

test("organizer publishes results and the public results page shows them", async ({
  page,
}) => {
  await signIn(page, "organizer");
  await openWorkspace(page);
  await chooseWorkspaceEvent(page);
  await goToDestination(page, "judging");
  const judging = page.locator(".cx-card").filter({
    has: page.getByRole("heading", { name: "Judging", exact: true }),
  });
  await judging.getByLabel("Stage").selectOption({ index: 1 });
  const publish = page.getByRole("button", {
    name: "Compute normalization and publish results",
  });
  await publish.scrollIntoViewIfNeeded();
  await publish.click();
  await expect(page.getByText("Results published.").first()).toBeVisible();

  await goToDestination(page, "results");
  // Deliberation: finalist comparison → finalize the winner → publish the award.
  const room = page.getByRole("region", {
    name: "Deliberation and finalization",
  });
  await room.getByLabel("Award").selectOption({ label: "Grand Prize" });
  await room.getByRole("button", { name: "Open deliberation room" }).click();
  await expect(room.getByText("Finalist comparison")).toBeVisible();
  await expect(room.getByText("Max judge disagreement")).toBeVisible();
  await room.getByLabel(`Select ${PROJECT} as winner`).check();
  await room
    .getByLabel("Override reason")
    .fill("Only project scored in the live demo.");
  await shot(page, "organizer-deliberation", "Deliberation and finalization");
  await room.getByRole("button", { name: "Finalize", exact: true }).click();
  await expect(room.getByText(/Finalized/)).toBeVisible();
  const awards = page.getByRole("region", { name: "Awards" }).first();
  void awards;
  await page.getByLabel("Manage award").selectOption({ label: "Grand Prize" });
  await page.getByRole("button", { name: "Publish winners" }).click();
  await expect(
    page
      .getByRole("region", { name: "Award operations", exact: true })
      .getByText(/Published/),
  ).toBeVisible();
  const { event } = await (async () => {
    const me = await (await page.request.get("/api/v1/accounts/me/")).json();
    const ws = me.memberships[0].workspace as string;
    const events = await (
      await page.request.get(`/api/v1/workspaces/${ws}/events/`)
    ).json();
    return { event: events[0].public_id as string };
  })();
  const results = await page.request.get(`/e/${event}/results/`);
  expect(results.status()).toBe(200);
  expect(await results.text()).toContain(PROJECT);
});
