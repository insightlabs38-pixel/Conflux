// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EventDashboard } from "./EventDashboard";
import { ProjectWorkspace } from "../artifacts/ProjectWorkspace";

vi.mock("./EventTemplatesPanel", () => ({ EventTemplatesPanel: () => null }));
vi.mock("../policy-builder/PolicyBuilder", () => ({
  PolicyBuilder: () => null,
}));
vi.mock("../stage-builder/StageBuilder", () => ({ StageBuilder: () => null }));
vi.mock("../teams/TeamPanel", () => ({ TeamPanel: () => null }));
vi.mock("../form-builder/FormBuilder", () => ({ FormBuilder: () => null }));
vi.mock("../page-builder/PageBuilder", () => ({ PageBuilder: () => null }));
vi.mock("../judging/EvaluationBuilder", () => ({
  EvaluationBuilder: () => null,
}));
vi.mock("../community-voting/CommunityVotingBuilder", () => ({
  CommunityVotingBuilder: () => null,
}));
vi.mock("../integrations/WebhooksPanel", () => ({ WebhooksPanel: () => null }));
vi.mock("../awards/AwardsPanel", () => ({ AwardsPanel: () => null }));
vi.mock("../operations/OperationsCenter", () => ({
  OperationsCenter: () => null,
}));
vi.mock("../operations/OperatorConsole", () => ({
  OperatorConsole: () => null,
}));
vi.mock("../communications/CommunicationsPanel", () => ({
  CommunicationsPanel: () => null,
}));

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: ReturnType<typeof createRoot>;

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

async function waitFor(check: () => boolean) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (check()) return;
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error("Workflow state did not update");
}

describe("workflow load states", () => {
  it("shows a retryable organizer list error before its true empty state", async () => {
    let attempts = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: unknown) => {
        const url = String(input);
        if (url.endsWith("/events/")) {
          attempts += 1;
          return attempts === 1
            ? {
                ok: false,
                status: 503,
                json: async () => ({ detail: "Unavailable" }),
              }
            : { ok: true, json: async () => [] };
        }
        return { ok: true, json: async () => [] };
      }),
    );
    act(() => root.render(<EventDashboard workspaceId="w" />));
    expect(container.textContent).toContain("Loading events");
    await waitFor(
      () => container.textContent?.includes("Unavailable") ?? false,
    );
    expect(container.textContent).not.toContain("No events yet");
    await act(async () =>
      [...container.querySelectorAll("button")]
        .find((button) => button.textContent === "Try again")
        ?.click(),
    );
    await waitFor(
      () => container.textContent?.includes("No events yet") ?? false,
    );
    expect(attempts).toBe(2);
  });

  it("does not show a false empty project list after a load failure", async () => {
    let attempts = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: unknown) => {
        const url = String(input);
        if (url.endsWith("/projects/")) {
          attempts += 1;
          if (attempts === 1)
            return {
              ok: false,
              status: 503,
              json: async () => ({ detail: "Unavailable" }),
            };
        }
        return { ok: true, json: async () => [] };
      }),
    );
    act(() => root.render(<ProjectWorkspace workspaceId="w" eventId="e" />));
    await waitFor(
      () => container.textContent?.includes("Unavailable") ?? false,
    );
    expect(container.textContent).not.toContain("No projects yet");
    await act(async () =>
      [...container.querySelectorAll("button")]
        .find((button) => button.textContent === "Try again")
        ?.click(),
    );
    await waitFor(
      () => container.textContent?.includes("No projects yet") ?? false,
    );
    expect(attempts).toBe(2);
  });

  it("keeps the latest selected event when detail requests finish out of order", async () => {
    const event = (id: string, name: string) => ({
      public_id: id,
      name,
      slug: id,
      description: "",
      timezone: "UTC",
      starts_at: null,
      ends_at: null,
      status: "draft",
      is_public: false,
      updated_at: id,
    });
    const first = event("e1", "First");
    const second = event("e2", "Second");
    const pending = new Map<string, (value: unknown) => void>();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: unknown) => {
        const url = String(input);
        if (url.endsWith("/events/"))
          return Promise.resolve({
            ok: true,
            json: async () => [first, second],
          });
        if (url.endsWith("/dashboard/"))
          return new Promise((resolve) =>
            pending.set(url.includes("/e1/") ? "e1" : "e2", resolve),
          );
        return Promise.resolve({ ok: true, json: async () => [] });
      }),
    );
    act(() => root.render(<EventDashboard workspaceId="w" />));
    await waitFor(
      () =>
        container.querySelectorAll('[aria-label="Workspace events"] button')
          .length === 2,
    );
    await act(async () =>
      (
        container.querySelectorAll(
          '[aria-label="Workspace events"] button',
        )[0] as HTMLButtonElement
      ).click(),
    );
    await act(async () =>
      (
        container.querySelectorAll(
          '[aria-label="Workspace events"] button',
        )[1] as HTMLButtonElement
      ).click(),
    );
    await act(async () =>
      pending.get("e2")?.({
        ok: true,
        json: async () => ({
          event: second,
          track_count: 0,
          base_prize_count: 0,
          configuration_checks: [],
        }),
      }),
    );
    await waitFor(
      () =>
        container.querySelector(".cx-page-header h1")?.textContent === "Second",
    );
    await act(async () =>
      pending.get("e1")?.({
        ok: true,
        json: async () => ({
          event: first,
          track_count: 0,
          base_prize_count: 0,
          configuration_checks: [],
        }),
      }),
    );
    expect(container.querySelector(".cx-page-header h1")?.textContent).toBe(
      "Second",
    );
  });
});
