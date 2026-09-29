// @vitest-environment happy-dom
import { act, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import {
  DeliberationPanel,
  OnsiteOperationsPanel,
  OrganizerJudgingLogisticsPanel,
} from ".";
import { EligibilityReviewPanel } from "./EligibilityPanels";
import { OrganizerOverview } from "../event-builder/OrganizerOverview";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

afterEach(() => vi.unstubAllGlobals());

type Call = { url: string; method: string; body: unknown };

function stubApi(routes: Record<string, unknown>) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown, init?: RequestInit) => {
      const call = {
        url: String(input),
        method: init?.method ?? "GET",
        body: init?.body ? JSON.parse(String(init.body)) : undefined,
      };
      calls.push(call);
      const key = Object.keys(routes).find((suffix) =>
        `${call.method} ${call.url}`.endsWith(suffix),
      );
      if (!key)
        return {
          ok: false,
          status: 404,
          json: async () => ({ detail: "No." }),
        };
      return { ok: true, status: 200, json: async () => routes[key] };
    }),
  );
  return calls;
}

async function mount(node: ReactNode) {
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () => root.render(node));
  return container;
}

async function until(check: () => boolean, what = "UI update") {
  for (let attempt = 0; attempt < 80; attempt++) {
    if (check()) return;
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error(`Timed out waiting for ${what}`);
}

const button = (root: HTMLElement, label: string) =>
  [...root.querySelectorAll("button")].find((b) =>
    (b.getAttribute("aria-label") ?? b.textContent ?? "").includes(label),
  ) as HTMLButtonElement;

async function type(input: HTMLInputElement, value: string) {
  await act(async () => {
    Object.getOwnPropertyDescriptor(
      HTMLInputElement.prototype,
      "value",
    )?.set?.call(input, value);
    input.dispatchEvent(new Event("input", { bubbles: true }));
  });
}

it("organizer overview surfaces workload and issues that need action", async () => {
  stubApi({
    "/applications/": [{ status: "approved" }, { status: "pending" }],
    "/eligibility-reviews/": [
      { status: "pending", open_findings: 1 },
      { status: "cleared", open_findings: 0 },
    ],
    "/judge-workload/": [
      { assigned_count: 4, submitted_count: 4 },
      { assigned_count: 4, submitted_count: 1 },
    ],
    "/result-publication-requests/": [{ status: "pending" }],
    "/onsite-summary/": {
      participants: 10,
      checked_in: 3,
      projects: 5,
      projects_placed: 4,
    },
  });
  const root = await mount(
    <OrganizerOverview
      workspaceId="w"
      eventId="e"
      starts="2026-10-01T09:00:00Z"
      ends={null}
      status="open"
      checks={["Add a rubric"]}
    />,
  );
  await until(() => root.textContent?.includes("5 of 8") ?? false);
  const text = root.textContent ?? "";
  expect(text).toContain("1 project need eligibility review");
  expect(text).toContain("1 judge has unscored assignments");
  expect(text).toContain("1 publication request awaiting approval");
  expect(text).toContain("1 project without a table or booth");
  expect(text).toContain("Add a rubric");
  expect(text).toContain("3 of 10");
});

it("eligibility queue shows status counts and filters the review list", async () => {
  stubApi({
    "eligibility-reviews/": [
      {
        project: "a",
        project_name: "Alpha",
        status: "pending",
        open_findings: 0,
        addressed_findings: 0,
        revision: 1,
      },
      {
        project: "b",
        project_name: "Bravo",
        status: "cleared",
        open_findings: 0,
        addressed_findings: 0,
        revision: 1,
      },
    ],
    "/portfolio/projects/?event=e&limit=100": { results: [] },
  });
  const root = await mount(
    <EligibilityReviewPanel workspaceId="w" eventId="e" />,
  );
  await until(() => root.textContent?.includes("Alpha") ?? false);
  expect(button(root, "All").textContent).toContain("2");
  expect(button(root, "Cleared").textContent).toContain("1");
  await act(async () => button(root, "Cleared").click());
  expect(root.textContent).toContain("Bravo");
  expect(root.textContent).not.toContain("Alpha");
  expect(button(root, "Cleared").getAttribute("aria-pressed")).toBe("true");
});

it("on-site desk searches and filters attendance for touch check-in", async () => {
  stubApi({
    "onsite-summary/": {
      participants: 2,
      rsvp: { in_person: 2, remote: 0, not_attending: 0 },
      no_response: 0,
      checked_in: 1,
      projects: 0,
      projects_placed: 0,
      slots: 0,
      slots_free: 0,
    },
    "attendance/": [
      { person: "1", username: "ada", mode: "in_person", checked_in: true },
      { person: "2", username: "grace", mode: "in_person", checked_in: false },
    ],
    "locations/": [],
    "project-locations/": [],
  });
  const root = await mount(
    <OnsiteOperationsPanel workspaceId="w" eventId="e" canManage />,
  );
  await until(() => root.textContent?.includes("grace") ?? false);
  await type(root.querySelector('input[type="search"]')!, "ada");
  expect(root.textContent).not.toContain("grace");
  await type(root.querySelector('input[type="search"]')!, "");
  await act(async () => button(root, "Not checked in").click());
  expect(root.querySelector("table")?.textContent).toContain("grace");
  expect(root.querySelector("table")?.textContent).not.toContain("ada");
});

it("deliberation explains selection, overrides and award conflicts, then finalizes", async () => {
  const calls = stubApi({
    "GET /api/v1/workspaces/w/events/e/awards/": [
      {
        public_id: "a1",
        name: "Grand Prize",
        evaluation_plan: "pl",
        winner_count: 1,
        published_at: null,
        winners: [],
      },
      {
        public_id: "a2",
        name: "Best Design",
        evaluation_plan: "pl",
        winner_count: 1,
        published_at: null,
        winners: [{ project: "p2" }],
      },
    ],
    "/stages/": [{ public_id: "s" }],
    "/stages/s/evaluation-plans/": [{ public_id: "pl" }],
    "/awards/a1/deliberation/": {
      public_id: "r",
      status: "open",
      quorum: 2,
      notes: [],
      stances: [],
      tally: [
        {
          project: "p1",
          project_name: "One",
          endorse: 2,
          object: 0,
          abstain: 0,
          recommended: true,
        },
        {
          project: "p2",
          project_name: "Two",
          endorse: 0,
          object: 2,
          abstain: 0,
          recommended: false,
        },
      ],
      finalization: {},
    },
    "/results/": [
      {
        rank: 1,
        project: "p1",
        project_name: "One",
        raw_score: 8,
        final_score: 8.1,
      },
      {
        rank: 2,
        project: "p2",
        project_name: "Two",
        raw_score: 7,
        final_score: 7.2,
      },
    ],
    "/agreement/": { criteria: [] },
    "/close-calls/": { projects: [] },
    "/progress/": {
      candidate_count: 2,
      pool_judge_count: 3,
      conflict_count: 1,
      expected_ballots: 6,
      submitted_ballots: 6,
      completion_ratio: 1,
    },
    "POST /api/v1/workspaces/w/events/e/awards/a1/deliberation/finalize/": {},
  });
  const root = await mount(<DeliberationPanel workspaceId="w" eventId="e" />);
  await until(() => root.querySelector("select") !== null);
  const select = root.querySelector("select")!;
  await act(async () => {
    select.value = "a1";
    select.dispatchEvent(new Event("change", { bubbles: true }));
  });
  await until(() => root.textContent?.includes("Finalist comparison") ?? false);
  expect(
    root.querySelector('[aria-label="Deliberation progress"]'),
  ).not.toBeNull();
  expect(root.textContent).toContain("Also wins Best Design");
  expect(root.textContent).toContain("2 endorse · 0 object");
  expect(root.textContent).toContain("Conflicts excluded");
  const two = root.querySelector(
    'input[aria-label="Select Two as winner"]',
  ) as HTMLInputElement;
  await act(async () => two.click());
  expect(root.textContent).toContain("Selected 1 of 1");
  expect(root.textContent).toContain("was not recommended by the panel");
  await act(async () => two.click());
  const one = root.querySelector(
    'input[aria-label="Select One as winner"]',
  ) as HTMLInputElement;
  await act(async () => one.click());
  expect(root.textContent).toContain("all recommended by the panel");
  await act(async () => button(root, "Finalize").click());
  await until(() => calls.some((c) => c.url.endsWith("/finalize/")));
  expect(calls.find((c) => c.url.endsWith("/finalize/"))?.body).toEqual({
    winners: ["p1"],
    override_reason: "",
  });
});

it("logistics simulates dropout impact before an explicit rebalance", async () => {
  const calls = stubApi({
    "/stages/": [{ public_id: "s", name: "Final" }],
    "/stages/s/evaluation-plans/": [{ public_id: "pl", name: "Plan" }],
    "/routes/": {
      judges: [
        {
          judge: "j1",
          username: "ada",
          stops: [],
          total_distance: 0,
          baseline_distance: 0,
          unplaced: [],
          already_evaluated: 0,
        },
      ],
      total_distance: 0,
      baseline_distance: 0,
    },
    "/assignment-responses/": {
      counts: { pending: 1, accepted: 2, declined: 1 },
      declined: [],
    },
    "POST /api/v1/workspaces/w/events/e/stages/s/evaluation-plans/pl/assignments/dropout-simulation/":
      {
        scenarios: [
          { pending_removed: 3, assignments_added: 3, coverage_gaps: [] },
        ],
      },
    "POST /api/v1/workspaces/w/events/e/stages/s/evaluation-plans/pl/assignments/rebalance/":
      {},
  });
  const root = await mount(
    <OrganizerJudgingLogisticsPanel workspaceId="w" eventId="e" />,
  );
  await until(() => root.querySelector("select") !== null);
  await act(async () => {
    const select = root.querySelector("select")!;
    select.value = "s";
    select.dispatchEvent(new Event("change", { bubbles: true }));
  });
  await until(
    () => root.textContent?.includes("Rebalance judge workload") ?? false,
  );
  expect(root.textContent).toContain("Declined or recused");
  expect(button(root, "Simulate dropout").disabled).toBe(true);
  await act(async () =>
    (
      root.querySelector('fieldset input[type="checkbox"]') as HTMLInputElement
    ).click(),
  );
  await act(async () => button(root, "Simulate dropout").click());
  await until(
    () =>
      root.textContent?.includes("3 pending assignments would move") ?? false,
  );
  expect(button(root, "Apply rebalance").disabled).toBe(true);
  expect(calls.some((c) => c.url.endsWith("/rebalance/"))).toBe(false);
  const confirm = [...root.querySelectorAll('input[type="checkbox"]')].find(
    (i) =>
      i.parentElement?.textContent?.includes(
        "freezes a new assignment version",
      ),
  ) as HTMLInputElement;
  await act(async () => confirm.click());
  await act(async () => button(root, "Apply rebalance").click());
  await until(() => calls.some((c) => c.url.endsWith("/rebalance/")));
  expect(calls.find((c) => c.url.endsWith("/rebalance/"))?.body).toEqual({
    drop_judges: ["j1"],
  });
});
