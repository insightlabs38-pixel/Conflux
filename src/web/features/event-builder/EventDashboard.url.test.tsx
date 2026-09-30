// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { useLocation } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EventDashboard } from "./EventDashboard";
import { withRouter } from "../../lib/test-router";
import { jsonResponse } from "../../lib/test-http";

vi.mock("./EventTemplatesPanel", () => ({ EventTemplatesPanel: () => null }));
vi.mock("../policy-builder/PolicyBuilder", () => ({
  PolicyBuilder: () => null,
}));
vi.mock("../stage-builder/StageBuilder", () => ({ StageBuilder: () => null }));
vi.mock("../teams/TeamPanel", () => ({ TeamPanel: () => null }));
vi.mock("../form-builder/FormBuilder", () => ({ FormBuilder: () => null }));
vi.mock("../page-builder/PageBuilder", () => ({ PageBuilder: () => null }));
vi.mock("../judging/EvaluationBuilder", () => ({
  EvaluationBuilder: () => null,
}));
vi.mock("../community-voting/CommunityVotingBuilder", () => ({
  CommunityVotingBuilder: () => null,
}));
vi.mock("../integrations/WebhooksPanel", () => ({ WebhooksPanel: () => null }));
vi.mock("../awards/AwardsPanel", () => ({ AwardsPanel: () => null }));
vi.mock("../operations/OperationsCenter", () => ({
  OperationsCenter: () => null,
}));
vi.mock("../operations/OperatorConsole", () => ({
  OperatorConsole: () => null,
}));
vi.mock("../communications/CommunicationsPanel", () => ({
  CommunicationsPanel: () => null,
}));
vi.mock("../awards/PublicAwards", () => ({ PublicAwards: () => null }));

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: ReturnType<typeof createRoot>;
let search = "";
function Where() {
  search = useLocation().search;
  return null;
}

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

async function waitFor(check: () => boolean) {
  for (let attempt = 0; attempt < 200; attempt++) {
    if (check()) return;
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error("Event dashboard did not update");
}

function stubApi() {
  const fetchMock = vi.fn(async (input: unknown) => {
    const url = String(input);
    const body = url.endsWith("/events/")
      ? [
          { public_id: "e1", name: "Spring Hack", status: "open" },
          { public_id: "e2", name: "Autumn Hack", status: "open" },
        ]
      : url.endsWith("/dashboard/")
        ? { checks: [], counts: {} }
        : [];
    return jsonResponse(200, body);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

const mount = (url: string) =>
  act(() =>
    root.render(
      withRouter(
        <>
          <Where />
          <EventDashboard workspaceId="w" />
        </>,
        url,
      ),
    ),
  );

describe("organizer event selection is URL state", () => {
  it("opens the linked event's dashboard on load", async () => {
    const fetchMock = stubApi();
    mount("/w/w/overview?event=e2");
    await waitFor(() =>
      fetchMock.mock.calls.some(([url]) =>
        String(url).endsWith("/e2/dashboard/"),
      ),
    );
    expect(
      container.querySelector(
        'nav[aria-label="Workspace events"] [aria-current]',
      )?.textContent,
    ).toContain("Autumn Hack");
  });

  it("selecting an event writes it to the URL", async () => {
    stubApi();
    mount("/w/w/overview");
    await waitFor(
      () =>
        container.querySelectorAll('nav[aria-label="Workspace events"] button')
          .length === 2,
    );
    await act(async () =>
      container
        .querySelectorAll<HTMLButtonElement>(
          'nav[aria-label="Workspace events"] button',
        )[0]
        .click(),
    );
    expect(search).toBe("?event=e1");
  });

  it("treats an unknown or invisible event as no selection", async () => {
    const fetchMock = stubApi();
    mount("/w/w/overview?event=missing");
    await waitFor(() => search === "");
    expect(
      fetchMock.mock.calls.some(([url]) => String(url).includes("/missing/")),
    ).toBe(false);
  });
});
