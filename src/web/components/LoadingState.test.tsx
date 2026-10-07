// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { LoadingState, SLOW_AFTER_MS } from "./LoadingState";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

function mount(node: React.ReactNode) {
  const host = document.createElement("div");
  const root = createRoot(host);
  act(() => root.render(node));
  return { host, root };
}

it("announces the wait with a spinner and its words, and is quiet at first", () => {
  const { host } = mount(<LoadingState label="Loading people…" />);
  expect(host.querySelector("[role=status]")).not.toBeNull();
  expect(host.querySelector("svg")).not.toBeNull();
  expect(host.textContent).toBe("Loading people…");
});

it("says what is slow after eight seconds and offers Cancel only when the caller can stop the work", () => {
  expect(SLOW_AFTER_MS).toBe(8000);
  const cancel = vi.fn();
  const withCancel = mount(<LoadingState onCancel={cancel} />);
  act(() => {
    vi.advanceTimersByTime(7999);
  });
  expect(withCancel.host.textContent).not.toContain("longer than usual");
  act(() => {
    vi.advanceTimersByTime(1);
  });
  expect(withCancel.host.textContent).toContain("longer than usual");
  const button = withCancel.host.querySelector("button")!;
  expect(button.textContent).toBe("Cancel");
  act(() => button.click());
  expect(cancel).toHaveBeenCalledOnce();

  const without = mount(<LoadingState />);
  act(() => {
    vi.advanceTimersByTime(SLOW_AFTER_MS);
  });
  expect(without.host.textContent).toContain("longer than usual");
  expect(without.host.querySelector("button")).toBeNull();
});

it("stops its timer when it goes away", () => {
  const { root } = mount(<LoadingState />);
  act(() => root.unmount());
  expect(vi.getTimerCount()).toBe(0);
});
