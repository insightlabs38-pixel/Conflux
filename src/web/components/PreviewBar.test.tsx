// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { PreviewBar } from "./PreviewBar";
import {
  LIVE,
  fromLocalInput,
  isLive,
  toLocalInput,
  type PreviewContext,
} from "../lib/previewContext";
import type { VersionInfo } from "../lib/versions";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: Root;
beforeEach(() => {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});
afterEach(() => {
  act(() => root.unmount());
  container.remove();
});

const VERSIONS: VersionInfo[] = [
  {
    id: "v1",
    label: "Version 1",
    at: "2027-03-01T09:00:00Z",
    by: null,
    current: false,
  },
  { id: "draft", label: "Current draft", at: null, by: null, current: true },
];

function mount(
  value: PreviewContext,
  extra: Partial<Parameters<typeof PreviewBar>[0]> = {},
) {
  const changes: PreviewContext[] = [];
  act(() =>
    root.render(
      <PreviewBar
        roles={["participant", "judge"]}
        versions={VERSIONS}
        value={value}
        onChange={(next) => changes.push(next)}
        summary="Previewing the live view. Nothing is saved or sent."
        {...extra}
      />,
    ),
  );
  return changes;
}
const select = (label: string) =>
  [...container.querySelectorAll("label")]
    .find((l) => l.textContent?.startsWith(label))!
    .querySelector("select, input") as HTMLSelectElement | HTMLInputElement;
function choose(element: HTMLSelectElement | HTMLInputElement, value: string) {
  act(() => {
    const proto =
      element instanceof HTMLSelectElement
        ? HTMLSelectElement
        : HTMLInputElement;
    Object.getOwnPropertyDescriptor(proto.prototype, "value")!.set!.call(
      element,
      value,
    );
    element.dispatchEvent(
      new Event(element instanceof HTMLSelectElement ? "change" : "input", {
        bubbles: true,
      }),
    );
  });
}

describe("PreviewBar", () => {
  it("says in words what is being previewed and that nothing is saved", () => {
    mount(LIVE);
    const status = container.querySelector('[role="status"]')!;
    expect(status.textContent).toContain("Preview.");
    expect(status.textContent).toContain("Nothing is saved or sent.");
    expect(container.querySelector("legend")!.textContent).toBe("Preview as");
  });

  it("offers the person, the versions and a time, with the live view as the default", () => {
    mount(LIVE);
    const person = select("Person") as HTMLSelectElement;
    expect([...person.options].map((o) => o.textContent)).toEqual([
      "Myself (all fields)",
      "participant",
      "judge",
    ]);
    const version = select("Version") as HTMLSelectElement;
    expect([...version.options].map((o) => o.textContent)).toEqual([
      "Live",
      expect.stringContaining("Version 1 ("),
      "Current draft",
    ]);
    expect((select("As of") as HTMLInputElement).type).toBe("datetime-local");
  });

  it("changes only the part that was chosen", () => {
    const changes = mount(LIVE);
    choose(select("Person"), "judge");
    expect(changes.at(-1)).toEqual({ role: "judge", at: null, version: null });
  });

  it("choosing a version clears the time and choosing a time clears the version", () => {
    const withTime: PreviewContext = {
      role: null,
      at: "2027-03-02T10:00:00.000Z",
      version: null,
    };
    const changes = mount(withTime);
    choose(select("Version"), "v1");
    expect(changes.at(-1)).toEqual({ role: null, at: null, version: "v1" });
    const withVersion = mount({ role: "judge", at: null, version: "v1" });
    choose(select("As of"), "2027-03-05T08:30");
    expect(withVersion.at(-1)).toEqual({
      role: "judge",
      at: new Date("2027-03-05T08:30").toISOString(),
      version: null,
    });
  });

  it("returns to the live view with one button that is disabled when already live", () => {
    let changes = mount(LIVE);
    const back = () =>
      [...container.querySelectorAll("button")].find(
        (b) => b.textContent === "Back to live",
      )!;
    expect(back().disabled).toBe(true);
    changes = mount({ role: "judge", at: null, version: null });
    expect(back().disabled).toBe(false);
    act(() => back().click());
    expect(changes.at(-1)).toEqual(LIVE);
  });

  it("shows notices as a list and marks itself busy while the server is asked", () => {
    mount(LIVE, {
      notices: [
        {
          code: "unpublished",
          message: "Nothing has been published yet; this is the draft.",
        },
      ],
      busy: true,
    });
    expect(container.querySelector("li")!.textContent).toContain(
      "this is the draft",
    );
    expect(container.querySelector("fieldset")!.getAttribute("aria-busy")).toBe(
      "true",
    );
  });

  it("leaves out controls the surface cannot use", () => {
    mount(LIVE, { roles: [], versions: [] });
    expect(container.querySelectorAll("select, input")).toHaveLength(0);
  });
});

describe("context helpers", () => {
  it("knows the live context", () => {
    expect(isLive(LIVE)).toBe(true);
    expect(isLive({ ...LIVE, role: "judge" })).toBe(false);
  });

  it("round-trips a time through the control in the browser's zone, to the minute", () => {
    const iso = "2027-03-08T09:00:00.000Z";
    expect(fromLocalInput(toLocalInput(iso))).toBe(iso);
    expect(toLocalInput(null)).toBe("");
    expect(toLocalInput("not a time")).toBe("");
    expect(fromLocalInput("")).toBeNull();
    expect(fromLocalInput("garbage")).toBeNull();
  });
});
