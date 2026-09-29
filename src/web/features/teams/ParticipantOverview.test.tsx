// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import {
  DestinationLink,
  WorkspaceNavigationProvider,
} from "../../components/WorkspaceNavigation";
import { ParticipantOverview } from "./ParticipantOverview";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());
it("derives the next action and progress from the participant's actual records", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => ({
      ok: true,
      json: async () => {
        if (url.endsWith("my-team/"))
          return {
            team: { name: "Actual team", members: [{}, {}] },
            my_role: "captain",
          };
        if (url.endsWith("projects/"))
          return [{ public_id: "p", name: "Actual project" }];
        if (url.endsWith("submissions/"))
          return [{ name: "Build", submission: { status: "draft" } }];
        if (url.endsWith("eligibility/"))
          return {
            status: "needs_remediation",
            findings: [{ state: "open", severity: "blocking" }],
          };
        return {
          name: "Actual event",
          ends_at: null,
          timezone: "UTC",
          status: "open",
        };
      },
    })),
  );
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () =>
    root.render(<ParticipantOverview workspaceId="w" eventId="e" />),
  );
  expect(container.textContent).toContain("Resolve your eligibility findings");
  expect(container.textContent).toContain("Actual team");
  expect(container.textContent).toContain("2 members");
  expect(container.textContent).toContain("0 / 1 stage submissions finalized");
  expect(container.textContent).toContain("1 open findings require attention");
  expect(container.textContent).toContain("No event deadline configured");
  await act(async () => root.unmount());
});
it("reports failed overview reads instead of showing zero counts", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: false,
      status: 503,
      json: async () => ({ detail: "Status unavailable" }),
    })),
  );
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () =>
    root.render(<ParticipantOverview workspaceId="w" eventId="e" />),
  );
  expect(container.querySelector('[role="alert"]')?.textContent).toContain(
    "Status unavailable",
  );
  expect(container.textContent).not.toContain("0 projects");
  await act(async () => root.unmount());
});

it("settles a deferred overview without leaving a hidden loading indicator", async () => {
  const original = window.location.href;
  window.history.replaceState({}, "", "/app/?view=team");
  const fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () =>
    root.render(
      <WorkspaceNavigationProvider role="participant">
        <ParticipantOverview workspaceId="w" eventId="e" />
      </WorkspaceNavigationProvider>,
    ),
  );
  expect(fetchMock).not.toHaveBeenCalled();
  expect(container.textContent).not.toContain("Loading your event status");
  await act(async () => root.unmount());
  window.history.replaceState({}, "", original);
});

it("clears loading when navigation cancels an in-flight overview", async () => {
  const original = window.location.href;
  window.history.replaceState({}, "", "/app/?view=overview");
  const fetchMock = vi.fn(() => new Promise(() => {}));
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () =>
    root.render(
      <WorkspaceNavigationProvider role="participant">
        <DestinationLink id="team">Team</DestinationLink>
        <ParticipantOverview workspaceId="w" eventId="e" />
      </WorkspaceNavigationProvider>,
    ),
  );
  expect(fetchMock).toHaveBeenCalledTimes(3);
  expect(container.textContent).toContain("Loading your event status");
  await act(async () =>
    container
      .querySelector("a")!
      .dispatchEvent(
        new MouseEvent("click", { bubbles: true, cancelable: true }),
      ),
  );
  expect(container.textContent).not.toContain("Loading your event status");
  await act(async () => root.unmount());
  window.history.replaceState({}, "", original);
});
