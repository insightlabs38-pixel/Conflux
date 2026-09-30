import { expect, request as pwRequest, test } from "@playwright/test";
import { authState } from "./auth-states";

// Release/nightly gate, last step of the lifecycle canary chain (PD-B03-T09). The lifecycle
// journey drives the UI; this reads the server state it left behind and checks that every
// stage landed consistently and in causal order — the integration failures that isolated,
// single-surface specs cannot see. Requires lifecycle.spec.ts to have run on this scenario.
test.describe.configure({ mode: "serial" });
test.skip(
  ({ isMobile }) => isMobile,
  "API/state verification; viewport independent",
);

const PROJECT = "Live Wire";
const LIVE = "participant-24";
const baseURL = process.env.E2E_BASE_URL ?? "http://localhost:8080";

type Json = Record<string, any>;
const api = async (label: string) =>
  pwRequest.newContext({ baseURL, storageState: await authState(label) });
const get = async (ctx: Awaited<ReturnType<typeof api>>, path: string) => {
  const response = await ctx.get(path);
  expect(response.ok(), `${path} -> HTTP ${response.status()}`).toBe(true);
  return (await response.json()) as any;
};

let scope: {
  base: string;
  event: string;
  workspace: string;
  plan: string;
  stage: string;
};

test.beforeAll(async () => {
  const organizer = await api("organizer");
  const me = await get(organizer, "/api/v1/accounts/me/");
  const workspace = me.memberships[0].workspace as string;
  const events = await get(
    organizer,
    `/api/v1/workspaces/${workspace}/events/`,
  );
  const event = events[0].public_id as string;
  const base = `/api/v1/workspaces/${workspace}/events/${event}/`;
  const stage = (await get(organizer, `${base}stages/`))[0].public_id as string;
  const plan = (
    await get(organizer, `${base}stages/${stage}/evaluation-plans/`)
  )[0].public_id as string;
  scope = { base, event, workspace, plan, stage };
  await organizer.dispose();
});

test("registration, submission and judging left consistent state", async () => {
  const organizer = await api("organizer");
  const applications: Json[] = await get(
    organizer,
    `${scope.base}applications/`,
  );
  expect(applications.length).toBeGreaterThanOrEqual(24);
  expect(applications.filter((a) => a.status !== "approved")).toEqual([]);
  expect(
    applications.some((a) => String(a.username).endsWith(`-${LIVE}`)),
  ).toBe(true);

  const plan = `${scope.base}stages/${scope.stage}/evaluation-plans/${scope.plan}/`;
  const progress = await get(organizer, `${plan}progress/`);
  expect(progress.submitted_ballots).toBe(3); // judges 01-03 scored the one live project
  expect(progress.results_published).toBe(true);
  expect(progress.latest_normalization_run.converged).toBe(true);

  const results: Json[] = await get(organizer, `${plan}results/`);
  expect(results.map((r) => r.project_name)).toEqual([PROJECT]);
  const provenance = await get(
    organizer,
    `${plan}provenance/${results[0].project}/`,
  );
  expect(new Set(provenance.ballots.map((b: Json) => b.judge)).size).toBe(3);
  expect(provenance.ballot_snapshot_available).toBe(true);
  await organizer.dispose();
});

test("the signed submission receipt belongs to the published project", async () => {
  const organizer = await api("organizer");
  const participant = await api(LIVE);
  const awards: Json[] = await get(organizer, `${scope.base}awards/`);
  const project = awards.find((a) => a.name === "Grand Prize")!.winners[0]
    .project as string;
  const { token } = await get(
    participant,
    `${scope.base}projects/${project}/submissions/${scope.stage}/receipt/`,
  );
  const [header, payload, signature] = String(token).split(".");
  expect(signature.length).toBeGreaterThan(40);
  expect(JSON.parse(Buffer.from(header, "base64url").toString()).alg).toBe(
    "EdDSA",
  );
  const claims = JSON.parse(Buffer.from(payload, "base64url").toString());
  expect(claims.kind).toBe("submission_receipt");
  expect(claims.subject.project).toBe(project);
  await organizer.dispose();
  await participant.dispose();
});

test("the award is published, deliberated, visible publicly and audited in causal order", async () => {
  const organizer = await api("organizer");
  const awards: Json[] = await get(organizer, `${scope.base}awards/`);
  const grand = awards.find((a) => a.name === "Grand Prize")!;
  expect(grand.published_at).toBeTruthy();
  expect(grand.winners.map((w: Json) => w.project_name)).toEqual([PROJECT]);
  expect(grand.winners[0].evidence.deliberation?.room).toBeTruthy();

  // Anonymous visitors see exactly the published winner (no cookies, separate context).
  const anonymous = await pwRequest.newContext({ baseURL });
  const published: Json[] = await get(
    anonymous,
    `/api/v1/events/${scope.event}/awards/`,
  );
  expect(
    published
      .find((a) => a.name === "Grand Prize")!
      .winners.map((w: Json) => w.project_name),
  ).toEqual([PROJECT]);
  await anonymous.dispose();

  const log: Json[] = await get(organizer, `/api/v1/audit/${scope.workspace}/`);
  const at = (action: string, pick: "first" | "last" = "first") => {
    const times = log
      .filter((e) => e.action === action)
      .map((e) => Date.parse(e.created_at));
    expect(times.length, `audit has ${action}`).toBeGreaterThan(0);
    return pick === "first" ? Math.min(...times) : Math.max(...times);
  };
  // Live Wire's own lifecycle, in order: submit -> score -> normalize -> publish -> deliberate -> award.
  const live = log.filter(
    (e) => e.action === "submission.finalized" && e.actor?.endsWith(LIVE),
  );
  expect(live.length, "participant-24 finalized a submission").toBe(1);
  const chain = [
    Date.parse(live[0].created_at),
    at("ballot.submitted"),
    at("normalization.run", "last"),
    at("results.published", "last"),
    at("deliberation.finalized", "last"),
    at("award.published", "last"),
  ];
  expect(chain, "audit events are causally ordered").toEqual(
    [...chain].sort((a, b) => a - b),
  );
  const scorers = new Set(
    log.filter((e) => e.action === "ballot.submitted").map((e) => e.actor),
  );
  for (const judge of ["judge-01", "judge-02", "judge-03"])
    expect(
      [...scorers].some((s) => String(s).endsWith(judge)),
      `${judge} ballot audited`,
    ).toBe(true);
  await organizer.dispose();
});

test("authorization holds after publication (negative)", async () => {
  const participant = await api("participant-01");
  for (const path of [
    `${scope.base}applications/`,
    `/api/v1/audit/${scope.workspace}/`,
  ]) {
    const response = await participant.get(path);
    expect([401, 403], `participant reading ${path}`).toContain(
      response.status(),
    );
  }
  const anonymous = await pwRequest.newContext({ baseURL });
  expect([401, 403]).toContain(
    (await anonymous.get(`${scope.base}applications/`)).status(),
  );
  await participant.dispose();
  await anonymous.dispose();
});
