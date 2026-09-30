import { expect } from "@playwright/test";
import { disposeFixture, isolatedTest, provisionFixture } from "./fixtures";
import {
  account,
  chooseWorkspaceEvent,
  eventIds,
  openWorkspace,
  PASSWORD,
  SEED,
  signIn,
} from "./support";

// Proves the PD-B03 isolation contract end to end: a fixture has its own accounts, event and
// workspace; mutating it leaves the shared reference (seed 7) untouched; disposal is scoped.
const test = isolatedTest("iso-min");
test.describe.configure({ mode: "serial" });
test.skip(
  ({ isMobile }) => isMobile,
  "API/identity contract; viewport independent",
);

test("a fixture organizer mutates only the fixture event", async ({
  page,
  browser,
  fixture,
}) => {
  await signIn(page, "organizer", fixture);
  const own = await eventIds(page);
  expect(own.event).toBe(fixture.event);
  expect(own.workspace).toBe(fixture.workspace);

  const renamed = await page.request.patch(
    `/api/v1/workspaces/${own.workspace}/events/${own.event}/`,
    { data: { name: `Isolated ${fixture.seed}` } },
  );
  expect(renamed.ok()).toBe(true);
  await page.reload();
  await openWorkspace(page);
  await page
    .getByRole("button", { name: new RegExp(`^Isolated ${fixture.seed}`) })
    .click();

  const reference = await (await browser.newContext()).newPage();
  await signIn(reference, "organizer");
  const shared = await eventIds(reference);
  expect(shared.event).not.toBe(fixture.event);
  expect(shared.name).not.toBe(`Isolated ${fixture.seed}`);
  await openWorkspace(reference);
  await chooseWorkspaceEvent(reference); // still lists its own, unrenamed event

  // negative: the fixture organizer cannot reach the reference event.
  const denied = await page.request.get(
    `/api/v1/workspaces/${shared.workspace}/events/${shared.event}/`,
  );
  expect([403, 404]).toContain(denied.status());
  await reference.context().close();
});

test("a fixture lives on a reserved seed and addresses the labels specs use", async ({
  fixture,
}) => {
  for (const label of [
    "organizer",
    "judge-03",
    "participant-05",
    "mentor",
    "volunteer",
    "sponsor",
  ])
    expect(fixture.account(label)).toBe(
      `demo-hackathon-${fixture.seed}-${label}`,
    );
  expect(fixture.seed).toBeGreaterThanOrEqual(10_000_000);
});

test("disposal removes the fixture's accounts; the reference and non-fixtures are refused", async ({
  page,
}) => {
  const temp = provisionFixture("iso-min");
  disposeFixture(temp.slug);
  await page.goto("/app/");
  await page.getByLabel("Username").fill(temp.account("organizer"));
  await page.getByLabel("Password").fill(temp.password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(
    page.getByRole("navigation", { name: "Your workspaces" }),
  ).toHaveCount(0);

  // negative: the shared reference can never be disposed through the fixture tool.
  expect(() => disposeFixture(`demo-hackathon-${SEED}`)).toThrow(
    /not an e2e fixture/,
  );
  // and it still signs in.
  await signIn(page, "organizer", { seed: SEED, password: PASSWORD });
  expect(account("organizer")).toContain(`-${SEED}-`);
});
