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

it("keeps advanced sections behind a disclosure and never mounts hidden ones", async () => {
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  const mounted: string[] = [];
  function Probe({ id }: { id: string }) {
    mounted.push(id);
    return <p>{id} content</p>;
  }
  await act(async () =>
    root.render(
      <WorkflowSections
        label="Setup"
        sections={[
          { id: "base", label: "Base", content: <Probe id="base" /> },
          {
            id: "policies",
            label: "Policies",
            advanced: true,
            content: <Probe id="policies" />,
          },
          {
            id: "voting",
            label: "Voting",
            hidden: true,
            content: <Probe id="voting" />,
          },
        ]}
      />,
    ),
  );
  const tabs = () =>
    [...container.querySelectorAll('[role="tab"]')].map((t) =>
      t.textContent?.trim(),
    );
  // Base view: one tab; the advanced one is behind the disclosure; the hidden one is not mounted.
  expect(tabs()).toEqual(["Base"]);
  expect(mounted).not.toContain("voting");
  const disclosure = container.querySelector<HTMLButtonElement>(
    ".cx-workflow__advanced",
  )!;
  expect(disclosure.textContent?.replace(/^[+\u2212]\s*/, "")).toBe(
    "Advanced (1)",
  );
  expect(disclosure.getAttribute("aria-expanded")).toBe("false");
  // Advanced content stays mounted (drafts survive) even while collapsed.
  expect(mounted).toContain("policies");
  await act(async () => disclosure.click());
  expect(tabs()).toEqual(["Base", "Policies"]);
  expect(disclosure.getAttribute("aria-expanded")).toBe("true");
  // Opening an advanced section pins the disclosure open (it cannot collapse under its own tab).
  await act(async () =>
    container.querySelectorAll<HTMLButtonElement>('[role="tab"]')[1].click(),
  );
  expect(disclosure.disabled).toBe(true);
  expect(
    container.querySelector('[role="tabpanel"]:not([hidden])')?.textContent,
  ).toContain("policies content");
  await act(async () => root.unmount());
});

it("shows the section of a link even when it is advanced, and falls back when it is not offered", async () => {
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  const sections = (hidden: boolean) => [
    { id: "base", label: "Base", content: <p>base</p> },
    {
      id: "deep",
      label: "Deep",
      advanced: true,
      hidden,
      content: <p>deep</p>,
    },
  ];
  await act(async () =>
    root.render(<WorkflowSections label="S" sections={sections(false)} />),
  );
  // Hide the section that is selected later: the first offered section takes over.
  await act(async () =>
    container
      .querySelector<HTMLButtonElement>(".cx-workflow__advanced")!
      .click(),
  );
  await act(async () =>
    container.querySelectorAll<HTMLButtonElement>('[role="tab"]')[1].click(),
  );
  await act(async () =>
    root.render(<WorkflowSections label="S" sections={sections(true)} />),
  );
  expect(
    container.querySelector('[role="tab"][aria-selected="true"]')?.textContent,
  ).toContain("Base");
  expect(container.querySelector(".cx-workflow__advanced")).toBeNull();
  await act(async () => root.unmount());
});
