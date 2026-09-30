// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { Loaded } from "../../hooks/useLoad";
import type { Readiness, ReadinessItem } from "../../hooks/useReadiness";
import { withRouter } from "../../lib/test-router";
import { ReadinessPanel } from "./ReadinessPanel";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());

const item = (
  id: string,
  severity: ReadinessItem["severity"],
  passed: boolean,
  detail: string,
): ReadinessItem => ({
  id,
  severity,
  passed,
  detail,
  module: "core",
  fix: { destination: "setup", section: "settings" },
});
const loaded = (
  data: Readiness | null,
  error: Loaded<Readiness>["error"] = null,
  reload = vi.fn(async () => {}),
): Loaded<Readiness> => ({
  data,
  error,
  loading: data === null && error === null,
  reload,
  update: () => {},
});

function render(load: Loaded<Readiness>) {
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(withRouter(<ReadinessPanel load={load} />)));
  return { container, root };
}

describe("ReadinessPanel", () => {
  it("lists blockers before warnings with a fix link and keeps passed checks collapsed", () => {
    const { container, root } = render(
      loaded({
        status: "blocked",
        items: [
          item(
            "gate_windows",
            "warning",
            false,
            "A gate is outside the dates.",
          ),
          item(
            "event_dates",
            "blocker",
            false,
            "Set the event start and end dates.",
          ),
          item(
            "forms_published",
            "blocker",
            true,
            "All forms have a published version.",
          ),
        ],
      }),
    );
    expect(container.textContent).toContain("Not ready: blockers remain");
    const open = [...container.querySelectorAll("section > ul > li")].map(
      (li) => li.textContent,
    );
    expect(open[0]).toContain("Set the event start and end dates.");
    expect(open[1]).toContain("A gate is outside the dates.");
    expect(container.querySelectorAll("a")).toHaveLength(2);
    const passed = container.querySelector("details")!;
    expect(passed.open).toBe(false);
    expect(passed.textContent).toContain("1 check passed");
    act(() => root.unmount());
  });

  it("says plainly when nothing is missing", () => {
    const { container, root } = render(
      loaded({
        status: "ready",
        items: [
          item("event_dates", "blocker", true, "Start and end dates are set."),
        ],
      }),
    );
    expect(container.textContent).toContain("Ready to launch");
    expect(container.textContent).toContain("Nothing is missing.");
    expect(container.querySelectorAll("a")).toHaveLength(0);
    act(() => root.unmount());
  });

  it("shows loading, and an error with Try again that reloads", () => {
    const loading = render(loaded(null));
    expect(loading.container.textContent).toContain("Checking readiness");
    act(() => loading.root.unmount());
    const reload = vi.fn(async () => {});
    const failed = render(
      loaded(
        null,
        { message: "down", status: 503 } as Loaded<Readiness>["error"],
        reload,
      ),
    );
    expect(
      failed.container.querySelector('[role="alert"]')?.textContent,
    ).toContain("Readiness could not load.");
    act(() => failed.container.querySelector("button")!.click());
    expect(reload).toHaveBeenCalledOnce();
    act(() => failed.root.unmount());
  });

  it("re-checks on request", () => {
    const reload = vi.fn(async () => {});
    const { container, root } = render(
      loaded({ status: "ready", items: [] }, null, reload),
    );
    const button = [...container.querySelectorAll("button")].find(
      (b) => b.textContent === "Check again",
    )!;
    act(() => button.click());
    expect(reload).toHaveBeenCalledOnce();
    act(() => root.unmount());
  });
});
