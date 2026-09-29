// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { expect, it } from "vitest";
import { WorkflowSections } from "./WorkflowSections";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
it("supports manual keyboard activation and retains an edited draft across tasks", async () => {
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () =>
    root.render(
      <WorkflowSections
        label="Project tasks"
        sections={[
          {
            id: "draft",
            label: "Draft",
            content: <textarea aria-label="Draft notes" defaultValue="" />,
          },
          {
            id: "evidence",
            label: "Evidence",
            content: <p>Artifact checks</p>,
          },
        ]}
      />,
    ),
  );
  const tabs = container.querySelectorAll<HTMLButtonElement>('[role="tab"]');
  const draft = container.querySelector("textarea")!;
  draft.value = "Retain this work";
  tabs[0].focus();
  await act(async () =>
    tabs[0].dispatchEvent(
      new KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true }),
    ),
  );
  expect(document.activeElement).toBe(tabs[1]);
  expect(tabs[0].getAttribute("aria-selected")).toBe("true");
  await act(async () => tabs[1].click());
  expect(
    container.querySelectorAll<HTMLElement>('[role="tabpanel"]')[0].hidden,
  ).toBe(true);
  await act(async () => tabs[0].click());
  expect(container.querySelector("textarea")).toBe(draft);
  expect(draft.value).toBe("Retain this work");
  expect(tabs[0].getAttribute("aria-controls")).toBe(
    container.querySelector('[role="tabpanel"]')?.id,
  );
  await act(async () => root.unmount());
  container.remove();
});
