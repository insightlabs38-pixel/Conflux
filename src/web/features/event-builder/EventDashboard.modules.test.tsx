// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { useLocation } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EventDashboard } from "./EventDashboard";
import { withRouter } from "../../lib/test-router";
import { WorkspaceNavigationProvider } from "../../components/WorkspaceNavigation";
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
const mountedVoting = vi.hoisted(() => ({ count: 0 }));
vi.mock("../community-voting/CommunityVotingBuilder", () => ({
  CommunityVotingBuilder: () => {
    mountedVoting.count++;
    return <p>Voting builder</p>;
  },
}));
vi.mock("../integrations/WebhooksPanel", () => ({ WebhooksPanel: () => null }));
vi.mock("../awards/AwardsPanel", () => ({ AwardsPanel: () => null }));
vi.mock("../operations/OperationsCenter", () => ({
  OperationsCenter: () => null,
}));
vi.mock("../operations/ExtensionsPanel", () => ({
  ExtensionsPanel: () => null,
}));
vi.mock("../operations/OperatorConsole", () => ({
  OperatorConsole: () => null,
}));
vi.mock("../communications/CommunicationsPanel", () => ({
  CommunicationsPanel: () => null,
}));
vi.mock("../awards/PublicAwards", () => ({ PublicAwards: () => null }));
vi.mock("./OrganizerOverview", () => ({ OrganizerOverview: () => null }));
vi.mock("./RegistrationPanel", () => ({ RegistrationPanel: () => null }));
vi.mock("./PermissionMatrixExplorer", () => ({
  PermissionMatrixExplorer: () => null,
}));
vi.mock("../judging/JudgeWorkloadPanel", () => ({
  JudgeWorkloadPanel: () => null,
}));
vi.mock("../audit/ConfigHistoryPanel", () => ({
  ConfigHistoryPanel: () => null,
}));
vi.mock("../profile/ProfilePanel", () => ({ ProfilePanel: () => null }));
vi.mock("../pvs", () => ({
  ContinuationsAdminPanel: () => null,
  DeliberationPanel: () => null,
  EligibilityReviewPanel: () => null,
  ExceptionRequestsPanel: () => null,
  MentorDeskPanel: () => null,
  OnsiteOperationsPanel: () => null,
  OrganizerJudgingLogisticsPanel: () => null,
  PublicationGovernancePanel: () => null,
  RulesPanel: () => null,
}));

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: ReturnType<typeof createRoot>;
beforeEach(() => {
  mountedVoting.count = 0;
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

const moduleList = (voting: boolean) => ({
  scope: "event",
  event: "e1",
  modules: [
    {
      key: "community_voting",
      label: "Community voting",
      description: "",
      destination: null,
      home: { destination: "judging", section: "CommunityVotingBuilder" },
      enabled: voting,
      in_use: false,
      explicit: voting ? true : null,
      can_disable: voting,
      reason: "",
    },
  ],
});

function stub(voting: boolean) {
  const fetchMock = vi.fn(async (input: unknown) => {
    const url = String(input);
    if (url.includes("/modules/")) return jsonResponse(200, moduleList(voting));
    if (url.endsWith("/events/"))
      return jsonResponse(200, [
        { public_id: "e1", name: "Spring Hack", status: "open" },
      ]);
    if (url.endsWith("/dashboard/"))
      return jsonResponse(200, {
        event: { public_id: "e1", name: "Spring Hack", status: "open" },
        track_count: 0,
        base_prize_count: 0,
        configuration_checks: [],
      });
    if (url.endsWith("/configuration/"))
      return jsonResponse(200, { event: "e1", preset: null, settings: [] });
    if (url.endsWith("/readiness/"))
      return jsonResponse(200, { status: "ready", items: [] });
    return jsonResponse(200, []);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

const mount = (url: string) =>
  act(() =>
    root.render(
      withRouter(
        <WorkspaceNavigationProvider role="organizer" workspaceId="w">
          <EventDashboard workspaceId="w" />
        </WorkspaceNavigationProvider>,
        url,
      ),
    ),
  );

describe("optional module panels", () => {
  it("do not mount, and so load and create nothing, until the module is on", async () => {
    stub(false);
    mount("/w/w/judging?event=e1");
    await waitFor(
      () =>
        !!container.querySelector(
          '[role="tablist"][aria-label="Judging tools"]',
        ),
    );
    await act(async () => new Promise((resolve) => setTimeout(resolve, 50)));
    expect(mountedVoting.count).toBe(0);
    const tabs = [...container.querySelectorAll('[role="tab"]')].map((t) =>
      t.textContent?.trim(),
    );
    expect(tabs.some((t) => t?.startsWith("Community voting"))).toBe(false);
  });

  it("mount once the server says the module is on for the selected event", async () => {
    stub(true);
    mount("/w/w/judging?event=e1");
    await waitFor(() => mountedVoting.count > 0);
    const tabs = [...container.querySelectorAll('[role="tab"]')].map((t) =>
      t.textContent?.trim(),
    );
    expect(tabs.some((t) => t?.startsWith("Community voting"))).toBe(true);
  });

  it("keep Policies behind Advanced in Setup until asked for", async () => {
    stub(false);
    mount("/w/w/setup?event=e1");
    await waitFor(
      () =>
        !!container.querySelector('[role="tablist"][aria-label="Event setup"]'),
    );
    const setup = container.querySelector(
      '[role="tablist"][aria-label="Event setup"]',
    )!;
    const tabNames = () =>
      [...setup.querySelectorAll('[role="tab"]')].map((t) =>
        t.textContent?.trim(),
      );
    expect(tabNames().some((t) => t?.startsWith("Policies"))).toBe(false);
    const disclosure = setup
      .closest(".cx-workflow")!
      .querySelector<HTMLButtonElement>(".cx-workflow__advanced")!;
    expect(disclosure.textContent?.replace(/^[+\u2212]\s*/, "")).toBe(
      "Advanced (2)",
    );
    await act(async () => disclosure.click());
    expect(tabNames().some((t) => t?.startsWith("Policies"))).toBe(true);
  });
});
