// @vitest-environment happy-dom
import { act, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import {
  ArtifactInspector,
  ChallengesPanel,
  JudgeAssignmentsPanel,
  MyOnsitePanel,
  OnsiteOperationsPanel,
  ProjectContinuationPanel,
  ProjectEligibilityPanel,
  RulesPanel,
} from ".";
import { EligibilityReviewPanel } from "./EligibilityPanels";
import { guarded } from "./Guarded";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

afterEach(() => vi.unstubAllGlobals());

type Call = { url: string; method: string; body: unknown };
type Route = (call: Call) => unknown;

/** Routes fetches by URL suffix; unknown URLs answer 404 so gaps fail loudly. */
function stubApi(routes: Record<string, Route | unknown>) {
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
      const route = routes[key];
      const body = typeof route === "function" ? (route as Route)(call) : route;
      return { ok: true, status: 200, json: async () => body };
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
  for (let attempt = 0; attempt < 60; attempt++) {
    if (check()) return;
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error(`Timed out waiting for ${what}`);
}

const buttonNamed = (root: HTMLElement, label: string) =>
  [...root.querySelectorAll("button")].find((b) =>
    (b.getAttribute("aria-label") ?? b.textContent ?? "").includes(label),
  ) as HTMLButtonElement;

async function type(
  input: HTMLInputElement | HTMLTextAreaElement,
  value: string,
) {
  await act(async () => {
    const proto =
      input instanceof HTMLTextAreaElement
        ? HTMLTextAreaElement.prototype
        : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, "value")?.set?.call(input, value);
    input.dispatchEvent(new Event("input", { bubbles: true }));
  });
}

const review = (over: object = {}) => ({
  project: "p1",
  status: "needs_remediation",
  decision_note: "One fix needed.",
  revision: 2,
  findings: [
    {
      public_id: "f1",
      code: "manual",
      automated: false,
      severity: "blocking",
      message: "Add a repository link.",
      state: "open",
      participant_response: "",
      resolution_note: "",
    },
  ],
  ...over,
});

it("participant sees structured findings and resubmits a remediation", async () => {
  const calls = stubApi({
    "GET /api/v1/workspaces/w/events/e/projects/p1/eligibility/": review(),
    "POST /api/v1/workspaces/w/events/e/projects/p1/eligibility/findings/f1/respond/":
      {},
  });
  const root = await mount(
    <ProjectEligibilityPanel workspaceId="w" eventId="e" projectId="p1" />,
  );
  await until(
    () => root.textContent?.includes("Add a repository link.") ?? false,
  );
  expect(root.textContent).toContain("Changes requested");
  await type(root.querySelector("textarea")!, "Linked the repo.");
  await act(async () => buttonNamed(root, "Mark as fixed").click());
  await until(() => calls.some((c) => c.method === "POST"));
  expect(calls.find((c) => c.method === "POST")?.body).toEqual({
    response: "Linked the repo.",
  });
});

it("participant sees a cleared project without remediation controls", async () => {
  stubApi({
    "eligibility/": review({ status: "cleared", findings: [] }),
  });
  const root = await mount(
    <ProjectEligibilityPanel workspaceId="w" eventId="e" projectId="p1" />,
  );
  await until(() => root.textContent?.includes("Cleared") ?? false);
  expect(root.querySelector("textarea")).toBeNull();
});

it("organizer records a decision and can request changes from the review queue", async () => {
  const calls = stubApi({
    "eligibility-reviews/": [
      {
        project: "p1",
        project_name: "Bright Garden",
        status: "needs_remediation",
        open_findings: 1,
        addressed_findings: 0,
        revision: 2,
      },
    ],
    "/portfolio/projects/?event=e&limit=100": { results: [] },
    "projects/p1/eligibility/": review(),
    "POST /api/v1/workspaces/w/events/e/projects/p1/eligibility/decision/":
      review({ status: "cleared" }),
  });
  const root = await mount(
    <EligibilityReviewPanel workspaceId="w" eventId="e" />,
  );
  await until(() => root.textContent?.includes("Bright Garden") ?? false);
  await act(async () => buttonNamed(root, "Review Bright Garden").click());
  await until(() => root.textContent?.includes("Record decision") ?? false);
  const outcome = [...root.querySelectorAll("select")].find((s) =>
    s.textContent?.includes("Approve"),
  ) as HTMLSelectElement;
  expect([...outcome.options].map((o) => o.value)).toEqual([
    "cleared",
    "needs_remediation",
    "ineligible",
    "pending",
  ]);
  await act(async () => buttonNamed(root, "Record decision").click());
  await until(() => calls.some((c) => c.url.endsWith("/decision/")));
  expect(calls.find((c) => c.url.endsWith("/decision/"))?.body).toEqual({
    decision: "cleared",
    note: "",
  });
});

it("volunteer scans a pass but gets no manual check-in or layout controls", async () => {
  const calls = stubApi({
    "onsite-summary/": {
      participants: 4,
      rsvp: { in_person: 3, remote: 1, not_attending: 0 },
      no_response: 0,
      checked_in: 1,
      projects: 2,
      projects_placed: 1,
      slots: 2,
      slots_free: 1,
    },
    "attendance/": [],
    "locations/": [],
    "project-locations/": [],
    "POST /api/v1/workspaces/w/events/e/checkins/scan/": {
      username: "ada",
      already_checked_in: false,
    },
  });
  const root = await mount(
    <OnsiteOperationsPanel workspaceId="w" eventId="e" canManage={false} />,
  );
  await until(() => root.textContent?.includes("1 of 4 participants") ?? false);
  expect(root.textContent).not.toContain("Auto-assign");
  expect(root.querySelector("table")).toBeNull();
  await type(root.querySelector("input")!, "cfx1.token");
  await act(async () => buttonNamed(root, "Check in").click());
  await until(() => root.textContent?.includes("ada checked in.") ?? false);
  expect(calls.find((c) => c.url.endsWith("scan/"))?.body).toEqual({
    token: "cfx1.token",
  });
});

it("organizer checks in an RSVP'd participant manually", async () => {
  const calls = stubApi({
    "onsite-summary/": {
      participants: 1,
      rsvp: { in_person: 1, remote: 0, not_attending: 0 },
      no_response: 0,
      checked_in: 0,
      projects: 0,
      projects_placed: 0,
      slots: 0,
      slots_free: 0,
    },
    "attendance/": [
      { person: "u1", username: "grace", mode: "in_person", checked_in: false },
    ],
    "locations/": [
      {
        public_id: "l1",
        kind: "table",
        name: "T1",
        capacity: 2,
        assigned: 0,
        parent: null,
      },
    ],
    "project-locations/": [],
    "POST /api/v1/workspaces/w/events/e/check-ins/": {},
  });
  const root = await mount(
    <OnsiteOperationsPanel workspaceId="w" eventId="e" canManage />,
  );
  await until(() => root.textContent?.includes("grace") ?? false);
  expect(root.textContent).toContain("T1");
  await act(async () => buttonNamed(root, "Check in grace").click());
  await until(() => calls.some((c) => c.url.endsWith("/check-ins/")));
  expect(calls.find((c) => c.url.endsWith("/check-ins/"))?.body).toEqual({
    participant: "u1",
  });
});

it("participant RSVPs and only then sees the check-in pass", async () => {
  let mode: string | null = null;
  const calls = stubApi({
    "GET /api/v1/workspaces/w/events/e/my-attendance/": () => ({ mode }),
    "PUT /api/v1/workspaces/w/events/e/my-attendance/": (call: Call) => {
      mode = (call.body as { mode: string }).mode;
      return { mode };
    },
    "my-pass/": { token: "cfx1.pass" },
  });
  const root = await mount(<MyOnsitePanel workspaceId="w" eventId="e" />);
  await until(() => root.querySelector("select") !== null);
  expect(root.querySelector("img")).toBeNull();
  const select = root.querySelector("select") as HTMLSelectElement;
  await act(async () => {
    select.value = "in_person";
    select.dispatchEvent(new Event("change", { bubbles: true }));
  });
  await until(() => root.querySelector("img") !== null, "QR code");
  expect(calls.some((c) => c.method === "PUT")).toBe(true);
  expect(root.textContent).toContain("cfx1.pass");
});

it("judge declines an assignment with a reason", async () => {
  const calls = stubApi({
    "GET /plans/p/my-assignments/": [
      { project: "p1", name: "Quiet Ledger", status: "pending", reason: "" },
    ],
    "POST /plans/p/my-assignments/p1/respond/": {},
  });
  const root = await mount(<JudgeAssignmentsPanel planBase="/plans/p/" />);
  await until(() => root.textContent?.includes("Quiet Ledger") ?? false);
  await type(root.querySelector("input")!, "Conflict of interest");
  await act(async () => buttonNamed(root, "Decline Quiet Ledger").click());
  await until(() => calls.some((c) => c.method === "POST"));
  expect(calls.find((c) => c.method === "POST")?.body).toEqual({
    status: "declined",
    reason: "Conflict of interest",
  });
});

it("participant acknowledges rules; organizers publish instead", async () => {
  const rules = {
    current: { number: 3, title: "Rules", body: "Be kind.", published_at: "" },
    acknowledged: false,
    versions: [],
  };
  const calls = stubApi({
    "GET /api/v1/workspaces/w/events/e/rules/": rules,
    "POST /api/v1/workspaces/w/events/e/rules/acknowledge/": {},
  });
  const root = await mount(
    <RulesPanel workspaceId="w" eventId="e" canPublish={false} />,
  );
  await until(() => root.textContent?.includes("Be kind.") ?? false);
  expect(root.querySelector("textarea")).toBeNull();
  await act(async () => buttonNamed(root, "I have read").click());
  await until(() => calls.some((c) => c.method === "POST"));
  expect(calls.find((c) => c.method === "POST")?.body).toEqual({ number: 3 });
});

it("shows sponsor resources with safe links only", async () => {
  stubApi({
    "challenges/": [
      {
        public_id: "a1",
        name: "Grand Prize",
        description: "",
        components: [],
        resources: [
          {
            public_id: "r1",
            kind: "api",
            title: "Docs",
            url: "https://x.test/",
            body: "",
          },
          {
            public_id: "r2",
            kind: "other",
            title: "Sneaky",
            url: "javascript:alert(1)",
            body: "",
          },
        ],
      },
    ],
  });
  const root = await mount(<ChallengesPanel workspaceId="w" eventId="e" />);
  await until(() => root.textContent?.includes("Grand Prize") ?? false);
  expect(root.querySelector('a[href="https://x.test/"]')).not.toBeNull();
  expect(root.querySelector('a[href^="javascript"]')).toBeNull();
  expect(root.textContent).toContain("Sneaky");
});

it("judge runs the artifact inspector and sees its verdict", async () => {
  let inspected = false;
  const calls = stubApi({
    "GET /api/v1/workspaces/w/events/e/projects/p1/review-artifacts/": () => [
      {
        public_id: "a1",
        kind: "document",
        visibility: "judge",
        title: "Notes.pdf",
        external_url: "",
        status: "ready",
        byte_size: 10,
        download_url: null,
        inspection: inspected
          ? {
              verdict: "warnings",
              detected_type: "pdf",
              findings: [
                {
                  severity: "warning",
                  code: "pdf_active_content",
                  detail: "Has JavaScript.",
                },
              ],
              facts: { pages: 2 },
              preview: "<script>alert(1)</script>",
              inspected_at: "",
            }
          : null,
      },
    ],
    "POST /api/v1/workspaces/w/events/e/projects/p1/review-artifacts/a1/inspection/":
      () => {
        inspected = true;
        return {};
      },
  });
  const root = await mount(
    <ArtifactInspector workspaceId="w" eventId="e" projectId="p1" />,
  );
  await until(() => root.textContent?.includes("Not inspected yet") ?? false);
  await act(async () => buttonNamed(root, "Inspect safely").click());
  await until(() => root.textContent?.includes("Has JavaScript.") ?? false);
  expect(calls.some((c) => c.method === "POST")).toBe(true);
  // Preview is rendered as inert text, never as markup.
  expect(root.querySelector("pre")?.textContent).toBe(
    "<script>alert(1)</script>",
  );
  expect(root.querySelector("pre script")).toBeNull();
});

it("a panel that receives an unexpected payload degrades instead of crashing", async () => {
  vi.spyOn(console, "error").mockImplementation(() => undefined);
  const Broken = guarded(() => {
    throw new Error("boom");
  }, "Broken panel");
  const root = await mount(<Broken />);
  expect(root.textContent).toContain("This section could not be displayed.");
  expect(buttonNamed(root, "Try again")).toBeTruthy();
});

it("continuation is not probed until the event has closed", async () => {
  const portfolio = (status: string) => ({
    events: 1,
    projects: [
      {
        project: "p1",
        name: "P",
        event: { public_id: "e", name: "E", status },
        submissions: [],
        awards: [],
      },
    ],
  });
  let status = "open";
  const calls = stubApi({
    "portfolio/me/": () => portfolio(status),
    "projects/p1/continuation/": {
      project: "p1",
      name: "P",
      summary: "Next steps",
      url: "",
      seeking: [],
      is_public: false,
      updates: [],
    },
  });
  const open = await mount(
    <ProjectContinuationPanel workspaceId="w" eventId="e" projectId="p1" />,
  );
  await until(
    () => open.textContent?.includes("Once the event has closed") ?? false,
  );
  expect(calls.some((c) => c.url.endsWith("/continuation/"))).toBe(false);
  status = "closed";
  const closed = await mount(
    <ProjectContinuationPanel workspaceId="w" eventId="e" projectId="p1" />,
  );
  await until(
    () => closed.querySelector("textarea")?.value === "Next steps",
    "continuation form",
  );
});
