// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { OperatorConsole } from "./OperatorConsole";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

afterEach(() => vi.unstubAllGlobals());

describe("OperatorConsole", () => {
  it("shows workspace health, archive links, templates, activity, and event navigation", async () => {
    const data = {
      event_total: 1,
      events: [
        {
          public_id: "event-1",
          name: "Demo",
          status: "draft",
          is_public: false,
          health: "blocked",
          blocker_count: 1,
          warning_count: 0,
        },
      ],
      template_total: 1,
      templates: [
        { public_id: "template-1", name: "Starter", source_event_name: "Demo" },
      ],
      activity: [
        {
          action: "event.updated",
          actor: "operator",
          target_type: "Event",
          created_at: "2026-09-27T00:00:00Z",
        },
      ],
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => data }),
    );
    const node = document.createElement("div");
    document.body.appendChild(node);
    const root = createRoot(node);
    const onChooseEvent = vi.fn();
    await act(async () =>
      root.render(
        <OperatorConsole
          workspaceId="workspace-1"
          onChooseEvent={onChooseEvent}
        />,
      ),
    );
    expect(node.textContent).toContain("Demo");
    expect(node.textContent).toContain("1 blockers");
    expect(node.textContent).toContain("Starter");
    expect(node.textContent).toContain("event.updated");
    expect(
      node.querySelector(
        'a[href="/api/v1/workspaces/workspace-1/events/event-1/archive/signed/"]',
      ),
    ).not.toBeNull();
    act(() => node.querySelector("button")?.click());
    expect(onChooseEvent).toHaveBeenCalledWith("event-1");
    act(() => root.unmount());
    node.remove();
  });
});
