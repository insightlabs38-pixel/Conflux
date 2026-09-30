// @vitest-environment happy-dom
import { act, useState } from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { WorkspaceNavigationProvider } from "../../components/WorkspaceNavigation";
import { jsonResponse } from "../../lib/test-http";
import { createTestQueryClient } from "../../lib/test-router";
import { FeaturesPanel } from "./FeaturesPanel";
import { ModuleGate } from "./ModuleGate";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());

type Mod = {
  key: string;
  label: string;
  description: string;
  destination: string | null;
  home: { destination: string; section: string };
  enabled: boolean;
  in_use: boolean;
  explicit: boolean | null;
  can_disable: boolean;
  reason: string;
};
const onsite = (over: Partial<Mod> = {}): Mod => ({
  key: "onsite",
  label: "On-site",
  description: "Locations and check-in.",
  destination: "onsite",
  home: { destination: "onsite", section: "" },
  enabled: false,
  in_use: false,
  explicit: null,
  can_disable: false,
  reason: "",
  ...over,
});
const list = (modules: Mod[]) => ({ scope: "event", event: "e1", modules });

function Harness({ children }: { children: React.ReactNode }) {
  const [client] = useState(createTestQueryClient);
  return (
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <Routes>
          <Route
            path="/w/:workspaceId/:view"
            element={
              <WorkspaceNavigationProvider role="organizer" workspaceId="w">
                {children}
              </WorkspaceNavigationProvider>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

async function mount(
  node: React.ReactNode,
  respond: (url: string, init?: RequestInit) => Response,
) {
  window.history.replaceState({}, "", "/w/w/onsite?event=e1");
  const fetchMock = vi.fn(async (input: unknown, init?: RequestInit) =>
    respond(String(input), init),
  );
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () => root.render(<Harness>{node}</Harness>));
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
  return { container, fetchMock, root };
}
const button = (container: HTMLElement, name: RegExp) =>
  [...container.querySelectorAll("button")].find((b) =>
    name.test(b.getAttribute("aria-label") ?? b.textContent ?? ""),
  ) as HTMLButtonElement;

describe("ModuleGate", () => {
  it("explains a module that is off and turns it on, then shows the content", async () => {
    let enabled = false;
    const { container, fetchMock, root } = await mount(
      <ModuleGate module="onsite" eventId="e1">
        <p>On-site tools</p>
      </ModuleGate>,
      (url, init) => {
        if (init?.method === "PATCH") {
          enabled = true;
          return jsonResponse(200, list([onsite({ enabled, explicit: true })]));
        }
        return jsonResponse(200, list([onsite({ enabled })]));
      },
    );
    expect(container.textContent).toContain(
      "On-site is not turned on for this event.",
    );
    expect(container.textContent).not.toContain("On-site tools");
    await act(async () => button(container, /turn on on-site/i).click());
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    const patch = fetchMock.mock.calls.find(
      ([, init]) => init?.method === "PATCH",
    )!;
    expect(String(patch[0])).toContain("/events/e1/modules/onsite/");
    expect(JSON.parse(String(patch[1]?.body))).toEqual({ enabled: true });
    expect(container.textContent).toContain("On-site tools");
    await act(async () => root.unmount());
  });

  it("shows the server's reason when turning on fails and keeps the gate", async () => {
    const { container, root } = await mount(
      <ModuleGate module="onsite" eventId="e1">
        <p>On-site tools</p>
      </ModuleGate>,
      (_url, init) =>
        init?.method === "PATCH"
          ? jsonResponse(400, {
              status: ["Archived event configuration cannot be edited."],
            })
          : jsonResponse(200, list([onsite()])),
    );
    await act(async () => button(container, /turn on on-site/i).click());
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    expect(container.querySelector('[role="alert"]')?.textContent).toContain(
      "Archived event",
    );
    expect(container.textContent).not.toContain("On-site tools");
    await act(async () => root.unmount());
  });

  it("renders the content while the module list is unknown, never a dead end", async () => {
    const { container, root } = await mount(
      <ModuleGate module="onsite" eventId="e1">
        <p>On-site tools</p>
      </ModuleGate>,
      () => jsonResponse(503, { detail: "down" }),
    );
    expect(container.textContent).toContain("On-site tools");
    await act(async () => root.unmount());
  });
});

describe("FeaturesPanel", () => {
  it("lists modules; a module with content cannot be turned off and says why", async () => {
    const reason =
      "On-site already has content for this event; remove it before turning it off.";
    const { container, root } = await mount(
      <FeaturesPanel eventId="e1" />,
      () =>
        jsonResponse(
          200,
          list([
            onsite({ enabled: true, in_use: true, reason }),
            {
              ...onsite(),
              key: "mentorship",
              label: "Mentorship",
              destination: null,
            },
          ]),
        ),
    );
    const off = button(container, /turn off on-site/i);
    expect(off.disabled).toBe(true);
    expect(container.textContent).toContain(reason);
    expect(container.textContent).toContain("in use");
    expect(button(container, /turn on mentorship/i).disabled).toBe(false);
    await act(async () => root.unmount());
  });
});
