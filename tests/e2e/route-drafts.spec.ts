import { expect, test, type Page } from "@playwright/test";
import {
  account,
  eventIds,
  goToDestination,
  goToTask,
  openWorkspace,
  PASSWORD,
  settled,
  signIn,
} from "./support";

// Route and draft preservation across the major workflows (PD-B04-T08): direct links, browser
// Back/Forward, refresh, role changes and unsaved drafts. Mutating (judge autosave, ballots), so it
// runs on an isolated fixture.
test.skip(
  ({ isMobile }) => isMobile,
  "history/draft contract; viewport independent",
);

const path = (page: Page) => new URL(page.url()).pathname;
const search = (page: Page) => new URL(page.url()).search;

async function openParticipantProject(page: Page) {
  await signIn(page, "participant-01");
  await openWorkspace(page);
  await page
    .getByRole("combobox", { name: "Event", exact: true })
    .selectOption({ index: 1 });
  await goToDestination(page, "project");
  await page
    .getByRole("combobox", { name: "Project", exact: true })
    .selectOption({ index: 1 });
  return page.getByLabel("Project description", { exact: true });
}

test("participant: an unsaved project draft survives moving between views and browser history", async ({
  page,
}) => {
  const story = await openParticipantProject(page);
  await story.fill("Unsaved draft that must survive navigation.");
  const projectUrl = page.url();

  await goToDestination(page, "team");
  await goToDestination(page, "overview");
  await page.goBack(); // team
  await expect(page).toHaveURL(/\/team\?/);
  await page.goBack(); // project
  await expect(page).toHaveURL(projectUrl);
  await expect(story).toHaveValue(
    "Unsaved draft that must survive navigation.",
  );
  await page.goForward();
  await page.goForward(); // overview
  await expect(page).toHaveURL(/\/overview\?/);
  await goToDestination(page, "project");
  await expect(story).toHaveValue(
    "Unsaved draft that must survive navigation.",
  );
});

test("participant: refresh and a shared link keep the event and view; a foreign view is replaced", async ({
  page,
}) => {
  await openParticipantProject(page);
  const here = page.url();
  await page.reload();
  await expect(page).toHaveURL(here);
  await expect(
    page.getByRole("combobox", { name: "Event", exact: true }),
  ).toBeVisible();
  // A view this role does not have is replaced by the overview (no history entry).
  await page.goto(here.replace("/project", "/operations"));
  await expect(page).toHaveURL(/\/overview\?/);
  const before = await page.evaluate(() => history.length);
  await page.goBack();
  expect(await page.evaluate(() => history.length)).toBe(before);
  await expect(page).not.toHaveURL(/\/operations/);
});

test("organizer: an unsaved form survives view changes and history, and the event context follows links", async ({
  page,
}) => {
  await signIn(page, "organizer");
  await openWorkspace(page);
  const { event, name, status } = await eventIds(page);
  await page
    .getByRole("navigation", { name: "Workspace events" })
    .getByRole("button", { name: `${name} (${status})` })
    .click();
  await expect(page).toHaveURL(new RegExp(`event=${event}`));
  await goToDestination(page, "setup");
  await page.getByText("Create a new event or start from a template").click();
  const form = page.locator("form", {
    has: page.getByRole("heading", { name: "Create event" }),
  });
  await form.getByLabel("Name", { exact: true }).fill("Draft event name");
  await form.getByText("Web address").click();
  await form.getByLabel("Slug").fill("draft-event-slug");

  await goToDestination(page, "judging");
  expect(search(page)).toContain(`event=${event}`);
  await goToDestination(page, "results");
  await page.goBack(); // judging
  await page.goBack(); // setup
  await expect(page).toHaveURL(/\/setup\?/);
  await expect(form.getByLabel("Name", { exact: true })).toHaveValue(
    "Draft event name",
  );
  await expect(form.getByLabel("Slug")).toHaveValue("draft-event-slug");
  await page.goForward();
  await page.goForward();
  await expect(page).toHaveURL(/\/results\?/);
  expect(search(page)).toContain(`event=${event}`);
});

async function openJudgeBallot(page: Page, label = "judge-01") {
  await signIn(page, label);
  await openWorkspace(page);
  const main = page.getByRole("region", { name: "Judging" });
  await main.getByLabel("Event").selectOption({ index: 1 });
  await main.getByLabel("Stage").selectOption({ index: 1 });
  await goToDestination(page, "queue");
  const candidate = page
    .getByRole("list", { name: "Assigned projects" })
    .getByRole("button")
    .first();
  await candidate.click();
  return page.getByLabel("Comment");
}

test("judge: an unsaved comment survives view changes and history; the autosaved draft survives a refresh", async ({
  page,
}) => {
  const comment = await openJudgeBallot(page);
  const queueUrl = page.url();
  await comment.fill("Draft comment written before leaving the queue.");

  await goToDestination(page, "overview");
  await page.goBack();
  await expect(page).toHaveURL(queueUrl);
  await expect(comment).toHaveValue(
    "Draft comment written before leaving the queue.",
  );
  await goToDestination(page, "schedule");
  await page.goBack();
  await expect(comment).toHaveValue(
    "Draft comment written before leaving the queue.",
  );

  // Autosave writes the draft on the server; a refresh brings it back.
  await expect(page.getByText("Draft saved")).toBeVisible();
  await page.reload();
  await expect(page).toHaveURL(queueUrl);
  const candidate = page
    .getByRole("list", { name: "Assigned projects" })
    .getByRole("button")
    .first();
  await candidate.click();
  await expect(page.getByLabel("Comment")).toHaveValue(
    "Draft comment written before leaving the queue.",
  );
});

async function signOut(page: Page) {
  await page.locator(".cx-account summary").click();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page.getByLabel("Username")).toBeVisible();
}

async function signInInPlace(page: Page, label: string) {
  await page.getByLabel("Username").fill(account(label));
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(
    page.getByRole("navigation", { name: "Your workspaces" }),
  ).toBeVisible();
}

test("role change in one tab: nothing from the previous account, and its view URL is replaced", async ({
  page,
}) => {
  const comment = await openJudgeBallot(page);
  await comment.fill("Judge-only draft.");
  const judgeQueue = page.url();
  await signOut(page);
  await expect(page.getByText("Judge-only draft.")).toHaveCount(0);
  await signInInPlace(page, "participant-01");

  // The judge's queue URL is not a participant view: it is replaced by the overview.
  await page.goto(judgeQueue);
  await expect(page).toHaveURL(/\/overview\?/);
  await expect(page.getByRole("region", { name: "Judging" })).toHaveCount(0);
  await expect(page.getByText("Judge-only draft.")).toHaveCount(0);
  await settled(page);
});

test("judge offline: a queued ballot survives a refresh, is never replayed under or shown to another judge, and syncs for its owner", async ({
  page,
}) => {
  let ballotPosts = 0;
  await page.route("**/ballots/", (route) => {
    if (route.request().method() !== "POST") return route.continue();
    ballotPosts++;
    return route.abort(); // the network is unreachable for ballots
  });
  const comment = await openJudgeBallot(page);
  const queueUrl = page.url();
  for (const input of await page.locator('input[type="number"]').all())
    await input.fill("5");
  await comment.fill("Scored while unreachable.");
  await page.getByRole("button", { name: "Submit ballot" }).click();
  await expect(page.getByText(/1 ballot queued/)).toBeVisible();
  const keys = await page.evaluate(() =>
    Object.keys(localStorage).filter((k) =>
      k.startsWith("conflux.judge-outbox."),
    ),
  );
  expect(keys).toHaveLength(1);
  // Scoped by account, not only by plan: conflux.judge-outbox.<user>.<plan>.
  expect(keys[0]).toMatch(/^conflux\.judge-outbox\.[^./]+\.\/api\//);

  // A refresh keeps the queue: the same account gets it back from its own scoped storage.
  await page.reload();
  await expect(page).toHaveURL(queueUrl);
  await expect(page.getByText(/1 ballot queued/)).toBeVisible();

  // Another judge on the same browser and plan neither sees it nor replays it.
  await signOut(page);
  const before = ballotPosts;
  await signInInPlace(page, "judge-02");
  await page.goto(queueUrl);
  await expect(page.getByRole("region", { name: "Judging" })).toBeVisible();
  await settled(page);
  await expect(page.getByText(/ballot queued/)).toHaveCount(0);
  expect(ballotPosts).toBe(before);

  // The owner signs back in with the network reachable: their queue syncs.
  await signOut(page);
  await page.unroute("**/ballots/");
  await signInInPlace(page, "judge-01");
  await page.goto(queueUrl);
  await expect(page.getByRole("region", { name: "Judging" })).toBeVisible();
  await expect(page.getByText(/ballot queued/)).toHaveCount(0);
  await expect
    .poll(async () => {
      const outbox = await page.evaluate(() =>
        Object.entries(localStorage).filter(([k]) =>
          k.startsWith("conflux.judge-outbox."),
        ),
      );
      return outbox.every(([, v]) => JSON.parse(v as string).length === 0);
    })
    .toBe(true);
});
