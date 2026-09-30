// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { describe, expect, it, vi } from "vitest";
import { OperationStatus } from "./OperationStatus";
import type { OperationState } from "../hooks/useOperation";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

function render(node: React.ReactElement) {
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(node));
  return container;
}
const button = (container: HTMLElement, label: string) =>
  [...container.querySelectorAll("button")].find(
    (b) => b.textContent === label,
  );

describe("OperationStatus", () => {
  it("renders nothing while idle", () => {
    expect(
      render(<OperationStatus state={{ status: "idle" }} />).innerHTML,
    ).toBe("");
  });

  it("announces a pending operation politely, with its own label and a cancel", () => {
    const onCancel = vi.fn();
    const container = render(
      <OperationStatus
        state={{ status: "pending", progress: null, cancellable: true }}
        pendingLabel="Saving…"
        onCancel={onCancel}
      />,
    );
    const status = container.querySelector('[role="status"]')!;
    expect(status.getAttribute("aria-busy")).toBe("true");
    expect(status.textContent).toContain("Saving…");
    expect(container.querySelector("progress")).toBeNull();
    act(() => button(container, "Cancel")?.click());
    expect(onCancel).toHaveBeenCalled();
  });

  it("shows determinate progress only when done and total are known, and no cancel after commit", () => {
    const known: OperationState<string> = {
      status: "pending",
      progress: { label: "Part 2 of 4…", done: 1, total: 4 },
      cancellable: false,
    };
    const container = render(
      <OperationStatus state={known} onCancel={() => {}} />,
    );
    const bar = container.querySelector("progress")!;
    expect([bar.value, bar.max]).toEqual([1, 4]);
    expect(container.textContent).toContain("Part 2 of 4…");
    expect(button(container, "Cancel")).toBeUndefined();
    const unknown = render(
      <OperationStatus
        state={{
          status: "pending",
          progress: { label: "Verifying…" },
          cancellable: true,
        }}
      />,
    );
    expect(unknown.querySelector("progress")).toBeNull();
  });

  it("raises a failure as an alert with the message and a retry", () => {
    const onRetry = vi.fn();
    const container = render(
      <OperationStatus
        state={{ status: "failed", error: "Upload failed (403)." }}
        onRetry={onRetry}
      />,
    );
    expect(container.querySelector('[role="alert"]')?.textContent).toContain(
      "Upload failed (403).",
    );
    act(() => button(container, "Try again")?.click());
    expect(onRetry).toHaveBeenCalled();
  });

  it("reports success and cancellation as status messages with their follow-ups", () => {
    const onDismiss = vi.fn();
    const ok = render(
      <OperationStatus
        state={{ status: "success", result: "Saved 3." }}
        successMessage={(result: string) => `Done: ${result}`}
        onDismiss={onDismiss}
      />,
    );
    expect(ok.querySelector('[role="status"]')?.textContent).toContain(
      "Done: Saved 3.",
    );
    act(() => button(ok, "Dismiss")?.click());
    expect(onDismiss).toHaveBeenCalled();
    const cancelled = render(
      <OperationStatus
        state={{ status: "cancelled" }}
        onRetry={() => {}}
        onDismiss={() => {}}
      />,
    );
    expect(cancelled.textContent).toContain("Cancelled");
    expect(button(cancelled, "Start again")).toBeDefined();
  });
});
