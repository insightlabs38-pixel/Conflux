// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { OperationsCenter } from "./OperationsCenter";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  vi.unstubAllGlobals();
});

async function until(check: () => boolean) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (check()) return;
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 5));
    });
  }
  throw new Error("Operations center did not update");
}

describe("OperationsCenter", () => {
  it("shows the launch checklist status and a submission blocker with evidence", async () => {
    const checklist = {
      status: "blocked",
      items: [
        { id: "event_dates", severity: "blocker", passed: false, detail: "Set the event start and end dates." },
      ],
    };
    const summary = {
      participants: { participant_count: 2, unteamed: { items: ["alice"], total: 1 }, team_count: 1, teams_without_project: { items: [], total: 0 } },
      submissions: {
        project_count: 1,
        counts: { ready: 0, warning: 0, blocked: 1 },
        blocked_projects: { items: [{ project: "Demo", checks: ["Publish a version for: Submission."] }], total: 1 },
        missing_artifacts: { items: [], total: 0 },
      },
      judging: { plans: [] },
      stages: { stages: [] },
      publication: { event_public: false, page_configured: false, page_block_count: 0, award_count: 0, awards_published: 0 },
      moderation: { voting_configured: false, unresolved_signals: { items: [], total: 0 } },
    };
    const fetchMock = vi.fn().mockImplementation(async (input: unknown) => {
      const url = String(input);
      return { ok: true, json: async () => (url.endsWith("checklist/") ? checklist : summary) };
    });
    vi.stubGlobal("fetch", fetchMock);
    act(() => root.render(<OperationsCenter workspaceId="w1" eventId="e1" />));
    await until(() => container.textContent?.includes("Set the event start and end dates.") ?? false);
    expect(container.textContent).toContain("blocked");
    expect(container.textContent).toContain("alice");
    expect(container.textContent).toContain("Demo");
    expect(container.textContent).toContain("Publish a version for: Submission.");
  });
});
