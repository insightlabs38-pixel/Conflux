// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { expect, it, vi } from "vitest";
import { ErrorState } from "./ErrorState";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

function mount(node: React.ReactNode) {
  const host = document.createElement("div");
  act(() => createRoot(host).render(node));
  return host;
}

it("is an alert with the message, an icon and nothing claimed when nothing is known", () => {
  const host = mount(<ErrorState message="It broke." />);
  expect(host.querySelector("[role=alert]")).not.toBeNull();
  expect(host.querySelector("svg")).not.toBeNull();
  expect(host.textContent).toContain("It broke.");
  expect(host.querySelector(".cx-state__kept")).toBeNull();
  expect(host.querySelector("button")).toBeNull();
});

it("a failed read says nothing was changed and describes the retry button", () => {
  const retry = vi.fn();
  const host = mount(
    <ErrorState kind="read" message="No list." onRetry={retry} />,
  );
  expect(host.querySelector(".cx-state__kept")?.textContent).toBe(
    "Nothing was changed.",
  );
  const button = host.querySelector("button")!;
  const note = host.querySelector(".cx-state__retry")!;
  expect(button.getAttribute("aria-describedby")).toBe(note.id);
  expect(note.textContent).toContain("loads it again");
  act(() => button.click());
  expect(retry).toHaveBeenCalledOnce();
});

it("shows what the caller knows about a write, and a server reference when there is one", () => {
  const host = mount(
    <ErrorState
      message="Could not save."
      kept="We could not confirm whether the change was saved."
      retry="Try again sends the same change again."
      reference="e_7f3a91"
      onRetry={() => {}}
    />,
  );
  expect(host.textContent).toContain("could not confirm");
  expect(host.querySelector("code")?.textContent).toBe("e_7f3a91");
});
