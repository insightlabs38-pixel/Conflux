// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CompletenessPanel } from "./CompletenessPanel";
import { jsonResponse } from "../../lib/test-http";
import { withQuery } from "../../lib/test-router";
import {
  factText,
  stateLabel,
  stateList,
  transitionLines,
  type Completeness,
  type CompletenessFeature,
} from "../../lib/completeness";

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
  vi.unstubAllGlobals();
});

const EVENT: CompletenessFeature = {
  key: "event",
  label: "Event",
  model: "events.Event",
  id_field: "public_id",
  id_type: "UUIDField",
  states: [
    { value: "draft", label: "Draft" },
    { value: "open", label: "Open" },
    { value: "closed", label: "Closed" },
  ],
  lifecycle: {
    kind: "choice",
    field: "status",
    initial: ["draft"],
    terminal: ["closed"],
    via: ["events.views.EventStatusView"],
    note: "",
    transitions: { draft: ["open"], open: ["closed"] },
  },
  claims: {
    identity: {
      state: "provided",
      refs: ["field:public_id"],
      reason: "",
      owner: "",
    },
  },
  problems: [],
};
const TRACK: CompletenessFeature = {
  ...EVENT,
  key: "track",
  label: "Track",
  model: "events.Track",
  states: [],
  lifecycle: {
    kind: "none",
    field: "",
    initial: [],
    terminal: [],
    via: [],
    note: "Edited in place and deleted.",
    transitions: {},
  },
};
const REPORT: Completeness = {
  properties: [
    {
      key: "identity",
      label: "Identity and lifecycle",
      batch: "PD-F003-B01",
      landed: true,
    },
    {
      key: "rest",
      label: "REST representation",
      batch: "PD-F003-B01",
      landed: false,
    },
    { key: "cli", label: "CLI", batch: "PD-F003-B02", landed: false },
  ],
  features: [EVENT, TRACK],
  totals: {},
  problems: [],
  ok: true,
};

const settle = () => act(async () => new Promise((r) => setTimeout(r, 0)));
async function mount(response: () => Response) {
  const urls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      urls.push(String(url));
      return response();
    }),
  );
  await act(async () =>
    root.render(withQuery(<CompletenessPanel workspaceId="w" />)),
  );
  await settle();
  return urls;
}

describe("CompletenessPanel", () => {
  it("lists each feature with its identity and lifecycle and says the claims agree", async () => {
    const urls = await mount(() => jsonResponse(200, REPORT));
    expect(urls).toEqual(["/api/v1/workspaces/w/completeness/"]);
    const text = container.textContent!;
    expect(text).toContain("Consistent");
    expect(text).toContain("2 features");
    expect(text).toContain("Event");
    expect(text).toContain("Provided · public id (public_id)");
    expect(text).toContain("Draft, Open, Closed");
    expect(text).toContain("No states");
    expect(container.querySelectorAll("tbody tr")).toHaveLength(2);
  });

  it("opens a lifecycle to its transitions, or to why there is none", async () => {
    await mount(() => jsonResponse(200, REPORT));
    const details = [...container.querySelectorAll("details")];
    expect(details[0].textContent).toContain(
      "Starts as draft; ends at closed.",
    );
    const transitions = [
      ...details[0].querySelectorAll(
        'ul[aria-label="Transitions of Event"] li',
      ),
    ].map((li) => li.textContent);
    expect(transitions).toEqual(["Draft → Open", "Open → Closed"]);
    expect(details[1].textContent).toContain("Edited in place and deleted.");
  });

  it("names the properties that are not checked yet and keeps them closed", async () => {
    await mount(() => jsonResponse(200, REPORT));
    const closed = [...container.querySelectorAll("summary")].find((s) =>
      s.textContent?.includes("2 properties are not checked yet"),
    )!;
    expect(closed).toBeDefined();
    expect(closed.parentElement!.textContent).toContain("CLI (PD-F003-B02)");
  });

  it("shows a finding as an alert with the feature that carries it", async () => {
    await mount(() =>
      jsonResponse(200, {
        ...REPORT,
        ok: false,
        problems: [
          {
            code: "route_missing",
            feature: "event",
            property: "identity",
            message: "There is no route named 'nope'.",
          },
        ],
      }),
    );
    const alert = container.querySelector('[role="alert"]')!;
    expect(alert.textContent).toContain("Inconsistent");
    expect(alert.textContent).toContain("1 finding.");
    expect(alert.textContent).toContain(
      "event: There is no route named 'nope'.",
    );
    expect(container.textContent).not.toContain("Consistent");
  });

  it("adds a column for each property that has landed", async () => {
    await mount(() =>
      jsonResponse(200, {
        ...REPORT,
        properties: [
          ...REPORT.properties.slice(0, 1),
          {
            key: "rest",
            label: "REST representation",
            batch: "PD-F003-B01",
            landed: true,
          },
        ],
        features: [
          {
            ...EVENT,
            claims: {
              ...EVENT.claims,
              rest: {
                state: "planned",
                refs: [],
                reason: "",
                owner: "PD-F003-B01-T06",
              },
            },
          },
          TRACK,
        ],
      }),
    );
    const headers = [...container.querySelectorAll("thead th")].map(
      (th) => th.textContent,
    );
    expect(headers).toContain("REST representation");
    const cells = [...container.querySelectorAll("tbody tr")].map(
      (tr) => tr.lastElementChild!.textContent,
    );
    expect(cells[0]).toContain("Planned");
    expect(cells[0]).toContain("Owned by PD-F003-B01-T06.");
    expect(cells[1]).toBe("Not claimed");
  });

  it("shows a failure with Try again", async () => {
    let fail = true;
    await mount(() =>
      fail ? jsonResponse(403, { detail: "No." }) : jsonResponse(200, REPORT),
    );
    expect(container.querySelector('[role="alert"]')!.textContent).toContain(
      "No.",
    );
    fail = false;
    const retry = [...container.querySelectorAll("button")].find(
      (b) => b.textContent === "Try again",
    )!;
    await act(async () => retry.click());
    await settle();
    expect(container.textContent).toContain("Consistent");
  });
});

describe("claim details", () => {
  it("shows how a claim is provided and what the system itself shows, closed by default", async () => {
    await mount(() =>
      jsonResponse(200, {
        ...REPORT,
        properties: [
          ...REPORT.properties.slice(0, 1),
          {
            key: "validation",
            label: "Validation and invariants",
            batch: "PD-F003-B01",
            landed: true,
          },
        ],
        features: [
          {
            ...EVENT,
            claims: {
              ...EVENT.claims,
              validation: {
                state: "provided",
                refs: [
                  "check:events.models.Event.clean",
                  "test:tests/x.py::test_y",
                ],
                reason: "",
                owner: "",
              },
            },
            facts: {
              validation: {
                blank_refused: ["name", "slug"],
                constraints: [],
                own_clean: true,
              },
            },
          },
        ],
      }),
    );
    const cell = container.querySelector("tbody tr")!.lastElementChild!;
    expect(cell.querySelector("details")!.open).toBe(false);
    const refs = [...cell.querySelectorAll("code")].map((c) => c.textContent);
    expect(refs).toEqual([
      "check:events.models.Event.clean",
      "test:tests/x.py::test_y",
    ]);
    const facts = [
      ...cell.querySelectorAll('ul[aria-label^="What the system"] li'),
    ].map((li) => li.textContent);
    expect(facts).toEqual([
      "A blank record is refused for: name, slug",
      "Constraints: none",
      "Model checks its own rules: yes",
    ]);
  });

  it("writes a not-applicable claim with its reason", async () => {
    await mount(() =>
      jsonResponse(200, {
        ...REPORT,
        properties: [
          ...REPORT.properties.slice(0, 1),
          {
            key: "rest",
            label: "REST representation",
            batch: "PD-F003-B01",
            landed: true,
          },
        ],
        features: [
          {
            ...EVENT,
            claims: {
              ...EVENT.claims,
              rest: {
                state: "not_applicable",
                refs: [],
                reason: "Internal only.",
                owner: "",
              },
            },
          },
        ],
      }),
    );
    expect(
      container.querySelector("tbody tr")!.lastElementChild!.textContent,
    ).toContain("Not applicableInternal only.");
  });
});

describe("completeness helpers", () => {
  it("reads states and transitions in words", () => {
    expect(stateList(EVENT)).toBe("Draft, Open, Closed");
    expect(stateLabel(EVENT, "open")).toBe("Open");
    expect(stateLabel(EVENT, "ghost")).toBe("ghost");
    expect(transitionLines(EVENT)).toEqual(["Draft → Open", "Open → Closed"]);
    expect(transitionLines(TRACK)).toEqual([]);
    expect(factText("constraints", ["a", "b"])).toBe("Constraints: a, b");
    expect(factText("own_clean", false)).toBe("Model checks its own rules: no");
    expect(factText("odd_key", 3)).toBe("odd key: 3");
    expect(factText("writers", "admin,organizer")).toBe(
      "Who can change: admin,organizer",
    );
    expect(factText("scope_path", ["Track", "Event"])).toBe(
      "Scoped through: Track → Event",
    );
    expect(factText("scope_path", [])).toBe("Scoped through: no chain");
    expect(factText("lists", ["GET track-list: array of Track"])).toBe(
      "Lists: GET track-list: array of Track",
    );
    expect(factText("paging", "unpaged")).toBe("Paging: unpaged");
    expect(factText("operations", ["GET track-list: Track[]"])).toBe(
      "Operations in both SDKs: GET track-list: Track[]",
    );
    expect(factText("count", 4)).toBe("Operations: 4");
    expect(factText("screens", ["EventDashboard.tsx"])).toBe(
      "Screens: EventDashboard.tsx",
    );
    expect(factText("screen", "none yet")).toBe("Screen: none yet");
    expect(factText("uses", ["EntityGrid in RegistrationPanel.tsx"])).toBe(
      "Shared components: EntityGrid in RegistrationPanel.tsx",
    );
    expect(factText("bulk_actions", ["move (Move projects)"])).toBe(
      "Bulk actions: move (Move projects)",
    );
    expect(factText("bulk", "not offered")).toBe("Bulk: not offered");
    expect(factText("commands", ["conflux-admin events list"])).toBe(
      "Commands: conflux-admin events list",
    );
    expect(factText("cli", "no command")).toBe("CLI: no command");
    expect(factText("advanced", "none beyond the base screen")).toBe(
      "Advanced: none beyond the base screen",
    );
    expect(factText("roles", ["admin", "organizer"])).toBe(
      "Who can query: admin, organizer",
    );
    expect(factText("query", "entity applications")).toBe(
      "Query: entity applications",
    );
    expect(factText("repeats", ["POST track-list: unique"])).toBe(
      "When sent twice: POST track-list: unique",
    );
    expect(factText("actions", ["track.created", "track.deleted"])).toBe(
      "Audit actions: track.created, track.deleted",
    );
    expect(
      factText("explanation", {
        outcome: "allowed",
        summary: "Read: members.",
      }),
    ).toBe("Read: members.");
  });
});
