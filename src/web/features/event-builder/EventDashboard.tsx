import { ProfilePanel } from "../profile/ProfilePanel";
import { WorkflowSections } from "../../components/WorkflowSections";
import { OrganizerOverview } from "./OrganizerOverview";
import {
  Destination,
  useModuleState,
  WorkspaceViewTitle,
} from "../../components/WorkspaceNavigation";
import { PageHeader } from "../../components/Foundation";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { PolicyBuilder } from "../policy-builder/PolicyBuilder";
import { StageBuilder } from "../stage-builder/StageBuilder";
import { TeamPanel } from "../teams/TeamPanel";
import { FormBuilder } from "../form-builder/FormBuilder";
import { PageBuilder } from "../page-builder/PageBuilder";
import { EvaluationBuilder } from "../judging/EvaluationBuilder";
import { JudgeWorkloadPanel } from "../judging/JudgeWorkloadPanel";
import { CommunityVotingBuilder } from "../community-voting/CommunityVotingBuilder";
import { WebhooksPanel } from "../integrations/WebhooksPanel";
import { AwardsPanel } from "../awards/AwardsPanel";
import { OperationsCenter } from "../operations/OperationsCenter";
import { ApprovalsPanel } from "../operations/ApprovalsPanel";
import { TimelinePanel } from "../operations/TimelinePanel";
import { JobsPanel } from "../operations/JobsPanel";
import { ExtensionsPanel } from "../operations/ExtensionsPanel";
import { CompletenessPanel } from "../operations/CompletenessPanel";
import { OperatorConsole } from "../operations/OperatorConsole";
import { CommunicationsPanel } from "../communications/CommunicationsPanel";
import { ConfigHistoryPanel } from "../audit/ConfigHistoryPanel";
import { useReadiness } from "../../hooks/useReadiness";
import { ConfigurationPanel } from "./ConfigurationPanel";
import { ConsequenceDialog } from "../../components/ConsequenceDialog";
import { CreateEvent } from "./CreateEvent";
import { ProjectsGrid } from "./ProjectsGrid";
import { WorkflowStatus } from "./WorkflowStatus";
import { FeaturesPanel } from "./FeaturesPanel";
import { ReadinessPanel } from "./ReadinessPanel";
import { ModuleGate } from "./ModuleGate";
import { EventTemplatesPanel } from "./EventTemplatesPanel";
import { PermissionMatrixExplorer } from "./PermissionMatrixExplorer";
import { RegistrationPanel } from "./RegistrationPanel";
import {
  ContinuationsAdminPanel,
  DeliberationPanel,
  EligibilityReviewPanel,
  ExceptionRequestsPanel,
  MentorDeskPanel,
  OnsiteOperationsPanel,
  OrganizerJudgingLogisticsPanel,
  PublicationGovernancePanel,
  RulesPanel,
} from "../pvs";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { apiJson, describeProblem } from "../../lib/api";
import { useLoad } from "../../hooks/useLoad";
import { useUrlParam } from "../../lib/urlState";

type Event = {
  public_id: string;
  name: string;
  slug: string;
  description: string;
  timezone: string;
  starts_at: string | null;
  ends_at: string | null;
  status: "draft" | "open" | "closed" | "archived";
  is_public: boolean;
  updated_at: string;
};
type Track = { public_id: string; name: string; description: string };
type Prize = {
  public_id: string;
  name: string;
  kind: string;
  track: string | null;
};
type Dashboard = {
  event: Event;
  track_count: number;
  base_prize_count: number;
  configuration_checks: string[];
};

function localDateTime(value: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}

function message(error: unknown): string {
  if (typeof error === "string") return error;
  if (error instanceof Error) return error.message;
  if (Array.isArray(error)) return error.map(message).join(" ");
  if (error && typeof error === "object") {
    return Object.entries(error)
      .map(([key, value]) => `${key}: ${message(value)}`)
      .join(" ");
  }
  return "Request failed.";
}

export function EventDashboard({ workspaceId }: { workspaceId: string }) {
  const base = `/api/v1/workspaces/${workspaceId}/events/`;
  // The selected event is context (lib/urlState.ts): refresh, back/forward and shared links keep it.
  const [selectedId, setEventParam] = useUrlParam("event");
  const [awardsRevision, setAwardsRevision] = useState(0);
  const chosen = useRef(new Set<string>());
  const [actionError, setActionError] = useState("");
  const [busy, setBusy] = useState(false);
  const [trackName, setTrackName] = useState("");
  const [prizeName, setPrizeName] = useState("");
  const [prizeKind, setPrizeKind] = useState("other");
  const [prizeAmount, setPrizeAmount] = useState("");
  const [prizeCurrency, setPrizeCurrency] = useState("");
  const [prizeTrack, setPrizeTrack] = useState("");

  // Server state (hooks/useLoad.ts): the list, and the selected event's dashboard, tracks and prizes.
  const eventsLoad = useLoad<Event[]>(base, { describe: describeProblem });
  const events = eventsLoad.data ?? [];
  const loadingEvents = eventsLoad.data === null && eventsLoad.error === null;
  const loadError = eventsLoad.error?.message ?? "";
  // Only an event the server listed (or one chosen here, e.g. just created) may be requested; a
  // link to one this account cannot see is treated as no selection.
  const known =
    selectedId !== "" &&
    (chosen.current.has(selectedId) ||
      events.some((item) => item.public_id === selectedId));
  const eventBase = `${base}${selectedId}/`;
  const detail = (path: string) => (known ? eventBase + path : null);
  const dashboardLoad = useLoad<Dashboard>(detail("dashboard/"), {
    describe: describeProblem,
  });
  const tracksLoad = useLoad<Track[]>(detail("tracks/"), {
    describe: describeProblem,
  });
  const prizesLoad = useLoad<Prize[]>(detail("base-prizes/"), {
    describe: describeProblem,
  });
  // The one readiness list, shared by Setup, the overview and operations (hooks/useReadiness.ts).
  const readinessLoad = useReadiness(workspaceId, known ? selectedId : null);
  // Panels of optional modules mount only once the server says the module is on for this event:
  // a hidden panel must not load (or, like the voting plan, create) anything on its own.
  const forEvent = known ? selectedId : "";
  const publicPageOff = useModuleState("public_page", forEvent) !== "on";
  const mentorshipOff = useModuleState("mentorship", forEvent) !== "on";
  const votingOff = useModuleState("community_voting", forEvent) !== "on";
  const dashboard = dashboardLoad.data;
  const tracks = tracksLoad.data ?? [];
  const prizes = prizesLoad.data ?? [];
  const error =
    actionError ||
    dashboardLoad.error?.message ||
    tracksLoad.error?.message ||
    prizesLoad.error?.message ||
    "";
  async function refresh() {
    await Promise.all([
      eventsLoad.reload(),
      dashboardLoad.reload(),
      tracksLoad.reload(),
      prizesLoad.reload(),
      readinessLoad.reload(),
    ]);
  }

  useEffect(() => {
    if (!loadingEvents && selectedId && !known)
      setEventParam("", { replace: true });
  }, [loadingEvents, selectedId, known, setEventParam]);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setActionError("");
    try {
      await action();
    } catch (cause) {
      setActionError(message(cause));
    } finally {
      setBusy(false);
    }
  }
  function choose(id: string) {
    chosen.current.add(id);
    setEventParam(id);
  }
  function saveSettings(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const start = String(data.get("starts_at") || "");
    const end = String(data.get("ends_at") || "");
    void run(async () => {
      if (start && end && start >= end)
        throw new Error("End must be after start.");
      await apiJson<Event>(eventBase, "PATCH", {
        name: String(data.get("name") || "").trim(),
        timezone: String(data.get("timezone") || "").trim(),
        starts_at: start ? new Date(start).toISOString() : null,
        ends_at: end ? new Date(end).toISOString() : null,
        is_public: data.get("is_public") === "on",
      });
      await refresh();
    });
  }
  function addTrack(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (!trackName.trim()) throw new Error("Track name is required.");
      await apiJson<Track>(eventBase + "tracks/", "POST", {
        name: trackName.trim(),
      });
      setTrackName("");
      await refresh();
    });
  }
  function addPrize(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (!prizeName.trim()) throw new Error("Prize name is required.");
      if (
        prizeKind === "cash" &&
        (!prizeAmount || !/^[A-Za-z]{3}$/.test(prizeCurrency))
      ) {
        throw new Error(
          "Cash prizes require an amount and three-letter currency.",
        );
      }
      await apiJson<Prize>(eventBase + "base-prizes/", "POST", {
        name: prizeName.trim(),
        kind: prizeKind,
        track: prizeTrack || null,
        ...(prizeKind === "cash"
          ? { amount: prizeAmount, currency: prizeCurrency.toUpperCase() }
          : {}),
      });
      setPrizeName("");
      setPrizeAmount("");
      setPrizeCurrency("");
      await refresh();
    });
  }
  // The operation waits for the consequences to be read (components/ConsequenceDialog.tsx).
  const [pendingStatus, setPendingStatus] = useState<Event["status"] | null>(
    null,
  );
  const STATUS_ACTION = {
    open: "event.open",
    closed: "event.close",
    archived: "event.archive",
  } as const;
  async function applyStatus(status: Event["status"]) {
    await apiJson<Event>(eventBase + "status/", "POST", { status });
    setPendingStatus(null);
    await refresh();
  }
  const selected = dashboard?.event;
  const nextStatus =
    selected?.status === "draft"
      ? "open"
      : selected?.status === "open"
        ? "closed"
        : selected?.status === "closed"
          ? "archived"
          : null;

  return (
    <section aria-label="Event dashboard">
      <PageHeader
        as="h1"
        title={selected?.name || "Events"}
        eyebrow="Organizer workspace"
        description="Manage the event, review what needs attention, and bring the results to publication."
      />
      <WorkspaceViewTitle role="organizer" />
      <Destination id="profile" lazy>
        <ProfilePanel workspaceId={workspaceId} />
      </Destination>
      {error && <p role="alert">{error}</p>}
      {loadingEvents && <LoadingState label="Loading events…" />}
      {loadError && (
        <ErrorState message={loadError} onRetry={eventsLoad.reload} />
      )}
      <Destination id="setup">
        <details className="cx-create-event" open={events.length === 0}>
          <summary>Create a new event or start from a template</summary>
          <CreateEvent
            workspaceId={workspaceId}
            onCreated={(id) => {
              // The server now lists the new event; without the refetch it was selected but absent
              // from the events navigation until the next visit.
              choose(id);
              void eventsLoad.reload();
            }}
          />
          <EventTemplatesPanel
            workspaceId={workspaceId}
            onCreated={(id) => {
              // The server now lists the new event; without the refetch it was selected but absent
              // from the events navigation until the next visit.
              choose(id);
              void eventsLoad.reload();
            }}
          />
        </details>
      </Destination>
      <nav aria-label="Workspace events">
        {events.map((item) => (
          <button
            key={item.public_id}
            type="button"
            aria-current={selectedId === item.public_id ? "page" : undefined}
            onClick={() => choose(item.public_id)}
          >
            {item.name} ({item.status})
          </button>
        ))}
      </nav>
      {!loadingEvents && !loadError && events.length === 0 && (
        <p>No events yet. Create one to get started.</p>
      )}
      <Destination id="operations">
        <OperatorConsole workspaceId={workspaceId} onChooseEvent={choose} />
      </Destination>
      {selected && (
        <article>
          <p>
            Status: {selected.status} ·{" "}
            {selected.is_public ? "Public" : "Private"}
          </p>
          <Destination id="overview">
            <OrganizerOverview
              key={`overview-${selected.public_id}`}
              workspaceId={workspaceId}
              eventId={selected.public_id}
              starts={selected.starts_at}
              ends={selected.ends_at}
              status={selected.status}
              readiness={readinessLoad}
            />
          </Destination>
          <Destination id="setup">
            <WorkflowSections
              label="Event setup"
              linkable
              sections={[
                {
                  id: "settings",
                  label: "Settings",
                  description: "Details, status, tracks and prizes",
                  content: (
                    <>
                      <ReadinessPanel load={readinessLoad} />
                      <form
                        onSubmit={saveSettings}
                        key={selected.public_id + selected.updated_at}
                      >
                        <h3>Settings</h3>
                        <label>
                          Name{" "}
                          <input
                            name="name"
                            defaultValue={selected.name}
                            required
                          />
                        </label>
                        <label>
                          Timezone{" "}
                          <input
                            name="timezone"
                            defaultValue={selected.timezone}
                            required
                          />
                        </label>
                        <label>
                          Start{" "}
                          <input
                            name="starts_at"
                            type="datetime-local"
                            defaultValue={localDateTime(selected.starts_at)}
                          />
                        </label>
                        <label>
                          End{" "}
                          <input
                            name="ends_at"
                            type="datetime-local"
                            defaultValue={localDateTime(selected.ends_at)}
                          />
                        </label>
                        <label>
                          Public{" "}
                          <input
                            name="is_public"
                            type="checkbox"
                            defaultChecked={selected.is_public}
                          />
                        </label>
                        <button
                          disabled={busy || selected.status === "archived"}
                        >
                          Save settings
                        </button>
                      </form>
                      {nextStatus && (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => setPendingStatus(nextStatus)}
                        >
                          Move to {nextStatus}
                        </button>
                      )}
                      {pendingStatus && pendingStatus !== "draft" && (
                        <ConsequenceDialog
                          url={`${eventBase}consequences/?action=${STATUS_ACTION[pendingStatus]}`}
                          onConfirm={() => applyStatus(pendingStatus)}
                          onCancel={() => setPendingStatus(null)}
                        />
                      )}
                      <section>
                        <h3>Tracks ({dashboard.track_count})</h3>
                        <ul>
                          {tracks.map((track) => (
                            <li key={track.public_id}>{track.name}</li>
                          ))}
                        </ul>
                        <form onSubmit={addTrack}>
                          <label>
                            Track name{" "}
                            <input
                              value={trackName}
                              onChange={(e) => setTrackName(e.target.value)}
                              required
                            />
                          </label>
                          <button disabled={busy}>Add track</button>
                        </form>
                      </section>
                      <section>
                        <h3>Base prizes ({dashboard.base_prize_count})</h3>
                        <ul>
                          {prizes.map((prize) => (
                            <li key={prize.public_id}>
                              {prize.name} ({prize.kind})
                            </li>
                          ))}
                        </ul>
                        <form onSubmit={addPrize}>
                          <label>
                            Prize name{" "}
                            <input
                              value={prizeName}
                              onChange={(e) => setPrizeName(e.target.value)}
                              required
                            />
                          </label>
                          <label>
                            Type{" "}
                            <select
                              value={prizeKind}
                              onChange={(e) => setPrizeKind(e.target.value)}
                            >
                              {[
                                "cash",
                                "credit",
                                "discount",
                                "subscription",
                                "hardware",
                                "travel",
                                "service",
                                "mentorship",
                                "swag",
                                "other",
                              ].map((kind) => (
                                <option key={kind} value={kind}>
                                  {kind}
                                </option>
                              ))}
                            </select>
                          </label>
                          <label>
                            Track{" "}
                            <select
                              value={prizeTrack}
                              onChange={(e) => setPrizeTrack(e.target.value)}
                            >
                              <option value="">All tracks</option>
                              {tracks.map((track) => (
                                <option
                                  key={track.public_id}
                                  value={track.public_id}
                                >
                                  {track.name}
                                </option>
                              ))}
                            </select>
                          </label>
                          {prizeKind === "cash" && (
                            <>
                              <label>
                                Amount{" "}
                                <input
                                  type="number"
                                  min="0"
                                  step="0.01"
                                  value={prizeAmount}
                                  onChange={(e) =>
                                    setPrizeAmount(e.target.value)
                                  }
                                  required
                                />
                              </label>
                              <label>
                                Currency{" "}
                                <input
                                  maxLength={3}
                                  value={prizeCurrency}
                                  onChange={(e) =>
                                    setPrizeCurrency(e.target.value)
                                  }
                                  required
                                />
                              </label>
                            </>
                          )}
                          <button disabled={busy}>Add prize</button>
                        </form>
                      </section>
                    </>
                  ),
                },
                {
                  id: "features",
                  label: "Features",
                  description: "Turn on only what this event needs",
                  content: <FeaturesPanel eventId={selected.public_id} />,
                },
                {
                  id: "configuration",
                  label: "Defaults & overrides",
                  description: "Where each value comes from",
                  advanced: true,
                  content: (
                    <ConfigurationPanel
                      key={`configuration-${selected.public_id}`}
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                    />
                  ),
                },
                {
                  id: "stages",
                  label: "Stages",
                  description: "Timeline and transitions",
                  content: (
                    <>
                      <WorkflowStatus
                        key={`workflow-${selected.public_id}`}
                        workspaceId={workspaceId}
                        eventId={selected.public_id}
                      />
                      <StageBuilder
                        workspaceId={workspaceId}
                        eventId={selected.public_id}
                      />
                    </>
                  ),
                },
                {
                  id: "policies",
                  advanced: true,
                  label: "Policies",
                  description: "Rules of entry, gates and debugging",
                  content: (
                    <PolicyBuilder
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                    />
                  ),
                },
                {
                  id: "rules",
                  label: "Rules",
                  description: "Event rules and acknowledgements",
                  content: (
                    <>
                      <RulesPanel
                        key={`RulesPanel-${selected.public_id}`}
                        workspaceId={workspaceId}
                        eventId={selected.public_id}
                        canPublish
                      />
                    </>
                  ),
                },
                {
                  id: "forms",
                  label: "Forms",
                  description: "Registration and project forms",
                  content: (
                    <>
                      <FormBuilder
                        workspaceId={workspaceId}
                        eventId={selected.public_id}
                      />
                    </>
                  ),
                },
                {
                  id: "page",
                  hidden: publicPageOff,
                  label: "Public page",
                  description: "Blocks, appearance and accessibility",
                  content: (
                    <>
                      <PageBuilder
                        workspaceId={workspaceId}
                        eventId={selected.public_id}
                      />
                    </>
                  ),
                },
              ]}
            />
          </Destination>
          <Destination id="participants">
            <WorkflowSections
              label="Participant tools"
              linkable
              sections={[
                {
                  id: "RegistrationPanel",
                  label: "Registration",
                  description: "Applications and invitations",
                  content: (
                    <RegistrationPanel
                      key={`registration-${selected.public_id}`}
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                    />
                  ),
                },
                {
                  id: "ProjectsGrid",
                  label: "Projects",
                  description: "Every project, filterable",
                  content: (
                    <ProjectsGrid
                      key={`projects-${selected.public_id}`}
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                      tracks={tracks}
                    />
                  ),
                },
                {
                  id: "TeamPanel",
                  label: "Teams",
                  description: "Rosters and matching",
                  content: (
                    <TeamPanel
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                    />
                  ),
                },
                {
                  id: "MentorDeskPanel",
                  hidden: mentorshipOff,
                  label: "Mentors",
                  description: "Availability and help requests",
                  content: (
                    <MentorDeskPanel
                      key={`MentorDeskPanel-${selected.public_id}`}
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                      isOrganizer
                    />
                  ),
                },
              ]}
            />
          </Destination>
          <Destination id="eligibility">
            <ModuleGate
              module="eligibility_review"
              eventId={selected.public_id}
            >
              <WorkflowSections
                label="Eligibility tools"
                sections={[
                  {
                    id: "EligibilityReviewPanel",
                    label: "Review queue",
                    description: "Findings and decisions",
                    content: (
                      <EligibilityReviewPanel
                        key={`EligibilityReviewPanel-${selected.public_id}`}
                        workspaceId={workspaceId}
                        eventId={selected.public_id}
                      />
                    ),
                  },
                  {
                    id: "ExceptionRequestsPanel",
                    label: "Deadline exceptions",
                    description: "Requests and decisions",
                    content: (
                      <ExceptionRequestsPanel
                        key={`ExceptionRequestsPanel-${selected.public_id}`}
                        workspaceId={workspaceId}
                        eventId={selected.public_id}
                      />
                    ),
                  },
                ]}
              />
            </ModuleGate>
          </Destination>
          <Destination id="onsite">
            <ModuleGate module="onsite" eventId={selected.public_id}>
              <OnsiteOperationsPanel
                key={`OnsiteOperationsPanel-${selected.public_id}`}
                workspaceId={workspaceId}
                eventId={selected.public_id}
                canManage
              />
            </ModuleGate>
          </Destination>
          <Destination id="judging">
            <WorkflowSections
              label="Judging tools"
              linkable
              sections={[
                {
                  id: "EvaluationBuilder",
                  label: "Rubrics and plans",
                  description: "Criteria and evaluation plans",
                  content: (
                    <EvaluationBuilder
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                    />
                  ),
                },
                {
                  id: "JudgeWorkloadPanel",
                  label: "Judge workload",
                  description: "Who is behind",
                  content: (
                    <JudgeWorkloadPanel
                      key={`judge-workload-${selected.public_id}`}
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                    />
                  ),
                },
                {
                  id: "OrganizerJudgingLogisticsPanel",
                  label: "Logistics",
                  description: "Assignments, coverage and routes",
                  content: (
                    <OrganizerJudgingLogisticsPanel
                      key={`OrganizerJudgingLogisticsPanel-${selected.public_id}`}
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                    />
                  ),
                },
                {
                  id: "CommunityVotingBuilder",
                  hidden: votingOff,
                  label: "Community voting",
                  description: "Public voting",
                  content: (
                    <CommunityVotingBuilder
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                    />
                  ),
                },
              ]}
            />
          </Destination>
          <Destination id="integrations">
            <ModuleGate module="integrations" eventId={selected.public_id}>
              <WebhooksPanel
                key={`webhooks-${selected.public_id}`}
                workspaceId={workspaceId}
                eventId={selected.public_id}
              />
            </ModuleGate>
          </Destination>
          <Destination id="results">
            <WorkflowSections
              label="Results tools"
              sections={[
                {
                  id: "DeliberationPanel",
                  label: "Deliberation",
                  description: "Finalists, evidence and decisions",
                  content: (
                    <DeliberationPanel
                      key={`DeliberationPanel-${selected.public_id}`}
                      onFinalized={() => setAwardsRevision((n) => n + 1)}
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                    />
                  ),
                },
                {
                  id: "PublicationGovernancePanel",
                  label: "Publication",
                  description: "Approval, schedule and corrections",
                  content: (
                    <PublicationGovernancePanel
                      key={`PublicationGovernancePanel-${selected.public_id}`}
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                    />
                  ),
                },
                {
                  id: "AwardsPanel",
                  label: "Awards",
                  description: "Award definitions",
                  content: (
                    <AwardsPanel
                      key={`awards-${selected.public_id}-${awardsRevision}`}
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                    />
                  ),
                },
              ]}
            />
          </Destination>
          <Destination id="operations">
            <WorkflowSections
              label="Operations tools"
              sections={[
                {
                  id: "OperationsCenter",
                  label: "Operations",
                  description: "Health and jobs",
                  content: (
                    <OperationsCenter
                      key={`operations-${selected.public_id}`}
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                    />
                  ),
                },
                {
                  id: "TimelinePanel",
                  label: "Timeline",
                  description: "Every date and window, with conflicts",
                  content: (
                    <TimelinePanel
                      key={`timeline-${selected.public_id}`}
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                    />
                  ),
                },
                {
                  id: "ApprovalsPanel",
                  label: "Approvals",
                  description: "Second-person gates and waiting requests",
                  content: (
                    <ApprovalsPanel
                      key={`approvals-${selected.public_id}`}
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                    />
                  ),
                },
                {
                  id: "JobsPanel",
                  label: "Exports and jobs",
                  description: "Archive export and background work",
                  content: (
                    <JobsPanel
                      key={`jobs-${selected.public_id}`}
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                    />
                  ),
                },
                {
                  id: "ContinuationsAdminPanel",
                  label: "Continuations",
                  description: "Post-event",
                  content: (
                    <ContinuationsAdminPanel
                      key={`ContinuationsAdminPanel-${selected.public_id}`}
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                    />
                  ),
                },
                {
                  id: "ConfigHistoryPanel",
                  label: "Configuration history",
                  description: "Audit of changes",
                  content: (
                    <ConfigHistoryPanel
                      key={`config-history-${selected.public_id}`}
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                    />
                  ),
                },
                {
                  id: "PermissionMatrixExplorer",
                  label: "Permissions",
                  description: "Role matrix",
                  content: (
                    <PermissionMatrixExplorer
                      key={`permission-matrix-${selected.public_id}`}
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                    />
                  ),
                },
                {
                  id: "ExtensionsPanel",
                  label: "Extensions",
                  description: "What this deployment provides",
                  content: <ExtensionsPanel workspaceId={workspaceId} />,
                },
                {
                  id: "CompletenessPanel",
                  label: "Completeness",
                  description: "What each feature provides, checked",
                  content: <CompletenessPanel workspaceId={workspaceId} />,
                },
              ]}
            />
          </Destination>
          <Destination id="communications">
            <CommunicationsPanel
              key={`communications-${selected.public_id}`}
              workspaceId={workspaceId}
              eventId={selected.public_id}
            />
          </Destination>
        </article>
      )}
    </section>
  );
}
