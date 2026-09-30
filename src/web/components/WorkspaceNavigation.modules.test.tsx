// @vitest-environment happy-dom
import { act, useState } from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { jsonResponse } from "../lib/test-http";
import { createTestQueryClient } from "../lib/test-router";
import { AppShell } from "./AppShell";
import { WorkspaceNavigationProvider } from "./WorkspaceNavigation";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());

const module = (key: string, destination: string | null, enabled: boolean) => ({
  key,
  label: key,
  description: "",
  destination,
  enabled,
  in_use: false,
  explicit: null,
  can_disable: enabled,
  reason: "",
});
const offModules = (event: string | null) => ({
  scope: event ? "event" : "workspace",
  event,
  modules: [
    module("eligibility_review", "eligibility", false),
    module("onsite", "onsite", false),
    module("integrations", "integrations", false),
    module("mentorship", null, false),
  ],
});

function Harness({ role }: { role: string }) {
  const [client] = useState(createTestQueryClient);
  return (
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <Routes>
          <Route
            path="/w/:workspaceId/:view"
            element={
              <WorkspaceNavigationProvider role={role} workspaceId="w">
                <AppShell role={role}>content</AppShell>
              </WorkspaceNavigationProvider>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

async function render(role: string, body: unknown, url = "/w/w/overview") {
  window.history.replaceState({}, "", url);
  const fetchMock = vi.fn(async (input: unknown) =>
    body instanceof Error
      ? jsonResponse(503, { detail: "down" })
      : jsonResponse(200, body),
  );
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () => root.render(<Harness role={role} />));
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
  return { container, fetchMock, root };
}
const labels = (container: HTMLElement) =>
  [...container.querySelectorAll('nav[aria-label="Primary"] a')].map(
    (a) => a.textContent,
  );
const headings = (container: HTMLElement) =>
  [...container.querySelectorAll(".cx-sidebar__group")].map(
    (p) => p.textContent,
  );

describe("organizer navigation follows the event's enabled modules", () => {
  it("hides destinations of modules that are off and moves the group heading", async () => {
    const { container, fetchMock, root } = await render(
      "organizer",
      offModules(null),
    );
    expect(String(fetchMock.mock.calls[0][0])).toContain(
      "/workspaces/w/modules/",
    );
    expect(labels(container)).toEqual([
      "Overview",
      "Event setup",
      "Participants & teams",
      "Judging",
      "Results & publication",
      "Communications",
      "Operations & audit",
      "Profile",
    ]);
    // "Advanced" belonged to Integrations; Operations & audit now carries it.
    expect(headings(container)).toEqual([
      "Manage event",
      "Advanced",
      "Account",
    ]);
    await act(async () => root.unmount());
  });

  it("asks for the selected event and shows destinations whose module is on", async () => {
    const body = offModules("e1");
    body.modules[1] = module("onsite", "onsite", true);
    const { container, fetchMock, root } = await render(
      "organizer",
      body,
      "/w/w/overview?event=e1",
    );
    expect(String(fetchMock.mock.calls[0][0])).toContain("modules/?event=e1");
    expect(labels(container)).toContain("On-site");
    expect(labels(container)).not.toContain("Integrations");
    expect(headings(container)).toEqual([
      "Manage event",
      "Advanced",
      "Account",
    ]);
    await act(async () => root.unmount());
  });

  it("shows every destination while unknown or when the list cannot load", async () => {
    const { container, root } = await render("organizer", new Error("down"));
    expect(labels(container)).toContain("Integrations");
    expect(labels(container)).toContain("On-site");
    expect(labels(container)).toContain("Projects & eligibility");
    await act(async () => root.unmount());
  });

  it("a view whose module is off stays a valid place", async () => {
    const { container, root } = await render(
      "organizer",
      offModules(null),
      "/w/w/onsite",
    );
    expect(window.location.pathname).toBe("/w/w/onsite");
    expect(labels(container)).not.toContain("On-site");
    await act(async () => root.unmount());
  });

  it("makes no module request for other roles", async () => {
    const { container, fetchMock, root } = await render(
      "participant",
      offModules(null),
    );
    expect(fetchMock).not.toHaveBeenCalled();
    expect(labels(container)).toContain("Team");
    await act(async () => root.unmount());
  });
});
