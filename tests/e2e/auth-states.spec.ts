import fs from "node:fs";
import { expect } from "@playwright/test";
import { authState, stats } from "./auth-states";
import { isolatedTest } from "./fixtures";
import { eventIds } from "./support";

// Storage states by role (PD-B03-T03) against an isolated fixture, so revoking sessions here
// never disturbs the shared reference scenario.
const test = isolatedTest("iso-min");
test.describe.configure({ mode: "serial" });
test.skip(
  ({ isMobile }) => isMobile,
  "identity contract; viewport independent",
);

const ROLES = [
  "organizer",
  "judge-01",
  "participant-01",
  "mentor",
  "volunteer",
];

test("each role opens its workspace without the sign-in form", async ({
  as,
  fixture,
}) => {
  for (const role of ROLES) {
    const page = await as(role);
    await page.goto("/app/");
    await expect(
      page.getByRole("navigation", { name: "Your workspaces" }),
    ).toBeVisible();
    await expect(page.getByLabel("Username")).toHaveCount(0);
    const me = await (await page.request.get("/api/v1/accounts/me/")).json();
    expect(me.username).toBe(fixture.account(role));
    await page.close();
  }
});

test("states are reused, not re-issued, until they stop validating", async ({
  as,
  fixture,
}) => {
  const first = await authState("organizer", fixture);
  const before = { ...stats, mtime: fs.statSync(first).mtimeMs };
  await (await as("organizer")).close();
  await (await as("organizer")).close();
  expect(stats.logins).toBe(before.logins);
  expect(stats.reuses).toBeGreaterThanOrEqual(before.reuses + 2);
  expect(fs.statSync(first).mtimeMs).toBe(before.mtime);
});

test("signing out revokes the session behind a state; the next use re-issues it", async ({
  as,
  fixture,
}) => {
  const page = await as("participant-01");
  await page.goto("/app/");
  expect((await page.request.post("/api/v1/accounts/logout/")).status()).toBe(
    204,
  );
  // Why sign-out specs must not use states: the stored cookie is now dead.
  const before = stats.logins;
  const file = await authState("participant-01", fixture);
  expect(stats.logins).toBe(before + 1);
  const again = await as("participant-01");
  expect((await again.request.get("/api/v1/accounts/me/")).ok()).toBe(true);
  expect(stats.logins).toBe(before + 1);
  expect(fs.existsSync(file)).toBe(true);
});

test("two identities at once stay separate", async ({ as, fixture }) => {
  const organizer = await as("organizer");
  const judge = await as.other("judge-01");
  const [o, j] = await Promise.all(
    [organizer, judge].map(
      async (p) =>
        (await (await p.request.get("/api/v1/accounts/me/")).json()).username,
    ),
  );
  expect([o, j]).toEqual([
    fixture.account("organizer"),
    fixture.account("judge-01"),
  ]);
  expect((await eventIds(organizer)).event).toBe(fixture.event);
});

test("a wrong password fails with a diagnostic and writes no state", async ({
  fixture,
}) => {
  const file = `artifacts/e2e-auth/${fixture.seed}/sponsor.json`;
  await expect(
    authState("sponsor", { ...fixture, password: "nope" }),
  ).rejects.toThrow(/sponsor.*sign-in failed \(HTTP 401\).*demo-reset/);
  expect(fs.existsSync(file)).toBe(false);
  await expect(authState("sponsor", fixture)).resolves.toMatch(
    /sponsor\.json$/,
  );
});
