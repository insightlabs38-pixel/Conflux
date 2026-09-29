import { ProfilePanel } from "../profile/ProfilePanel";
import { WorkflowSections } from "../../components/WorkflowSections";
import { OrganizerOverview } from "./OrganizerOverview";
import {
  Destination,
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
import { OperatorConsole } from "../operations/OperatorConsole";
import { CommunicationsPanel } from "../communications/CommunicationsPanel";
import { ConfigHistoryPanel } from "../audit/ConfigHistoryPanel";
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

async function request<T>(
  path: string,
  method = "GET",
  body?: object,
): Promise<T> {
  const response = await fetch(path, {
    method,
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    let detail: unknown = `Request failed (${response.status}).`;
    try {
      detail = await response.json();
    } catch {
      /* Retain status message. */
    }
    throw new Error(message(detail));
  }
  return response.status === 204
    ? (undefined as T)
    : (response.json() as Promise<T>);
}

export function EventDashboard({ workspaceId }: { workspaceId: string }) {
  const base = `/api/v1/workspaces/${workspaceId}/events/`;
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [awardsRevision, setAwardsRevision] = useState(0);
  const selectedRef = useRef("");
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [tracks, setTracks] = useState<Track[]>([]);
  const [prizes, setPrizes] = useState<Prize[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loadingEvents, setLoadingEvents] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [retry, setRetry] = useState(0);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [trackName, setTrackName] = useState("");
  const [prizeName, setPrizeName] = useState("");
  const [prizeKind, setPrizeKind] = useState("other");
  const [prizeAmount, setPrizeAmount] = useState("");
  const [prizeCurrency, setPrizeCurrency] = useState("");
  const [prizeTrack, setPrizeTrack] = useState("");

  const eventBase = `${base}${selectedId}/`;
  async function refresh(id = selectedId) {
    const list = await request<Event[]>(base);
    setEvents(list);
    setLoadError("");
    if (!id) return;
    const detailBase = `${base}${id}/`;
    const [health, nextTracks, nextPrizes] = await Promise.all([
      request<Dashboard>(detailBase + "dashboard/"),
      request<Track[]>(detailBase + "tracks/"),
      request<Prize[]>(detailBase + "base-prizes/"),
    ]);
    if (selectedRef.current !== id) return;
    setDashboard(health);
    setTracks(nextTracks);
    setPrizes(nextPrizes);
  }
  useEffect(() => {
    let active = true;
    setLoadingEvents(true);
    setLoadError("");
    request<Event[]>(base)
      .then((list) => {
        if (active) setEvents(list);
      })
      .catch((cause: unknown) => {
        if (active) setLoadError(message(cause));
      })
      .finally(() => {
        if (active) setLoadingEvents(false);
      });
    return () => {
      active = false;
    };
  }, [base, retry]);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (cause) {
      setError(message(cause));
    } finally {
      setBusy(false);
    }
  }
  function choose(id: string) {
    selectedRef.current = id;
    setSelectedId(id);
    setDashboard(null);
    void run(() => refresh(id));
  }
  function createEvent(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (!name.trim() || !slug.trim())
        throw new Error("Name and slug are required.");
      const created = await request<Event>(base, "POST", {
        name: name.trim(),
        slug: slug.trim(),
      });
      setName("");
      setSlug("");
      selectedRef.current = created.public_id;
      setSelectedId(created.public_id);
      await refresh(created.public_id);
    });
  }
  function saveSettings(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const start = String(data.get("starts_at") || "");
    const end = String(data.get("ends_at") || "");
    void run(async () => {
      if (start && end && start >= end)
        throw new Error("End must be after start.");
      await request<Event>(eventBase, "PATCH", {
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
      await request<Track>(eventBase + "tracks/", "POST", {
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
      await request<Prize>(eventBase + "base-prizes/", "POST", {
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
  function transition(status: Event["status"]) {
    void run(async () => {
      await request<Event>(eventBase + "status/", "POST", { status });
      await refresh();
    });
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
        <ProfilePanel />
      </Destination>
      {error && <p role="alert">{error}</p>}
      {loadingEvents && <LoadingState label="Loading events…" />}
      {loadError && (
        <ErrorState
          message={loadError}
          onRetry={() => setRetry((count) => count + 1)}
        />
      )}
      <Destination id="setup">
        <details className="cx-create-event" open={events.length === 0}>
          <summary>Create a new event or start from a template</summary>
          <form onSubmit={createEvent}>
            <h2>Create event</h2>
            <label>
              Name{" "}
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </label>
            <label>
              Slug{" "}
              <input
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                required
              />
            </label>
            <button disabled={busy}>Create event</button>
          </form>
          <EventTemplatesPanel workspaceId={workspaceId} onCreated={choose} />
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
              checks={dashboard.configuration_checks}
            />
          </Destination>
          <Destination id="setup">
            <WorkflowSections
              label="Event setup"
              sections={[
                {
                  id: "settings",
                  label: "Settings",
                  description: "Details, status, tracks and prizes",
                  content: (
                    <>
                      {dashboard.configuration_checks.length > 0 && (
                        <section aria-label="Configuration checks">
                          <h3>Configuration checks</h3>
                          <ul>
                            {dashboard.configuration_checks.map((check) => (
                              <li key={check}>{check}</li>
                            ))}
                          </ul>
                        </section>
                      )}
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
                          onClick={() => transition(nextStatus)}
                        >
                          Move to {nextStatus}
                        </button>
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
                  id: "stages",
                  label: "Stages",
                  description: "Timeline and transitions",
                  content: (
                    <StageBuilder
                      workspaceId={workspaceId}
                      eventId={selected.public_id}
                    />
                  ),
                },
                {
                  id: "policies",
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
          </Destination>
          <Destination id="onsite">
            <OnsiteOperationsPanel
              key={`OnsiteOperationsPanel-${selected.public_id}`}
              workspaceId={workspaceId}
              eventId={selected.public_id}
              canManage
            />
          </Destination>
          <Destination id="judging">
            <WorkflowSections
              label="Judging tools"
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
            <WebhooksPanel
              key={`webhooks-${selected.public_id}`}
              workspaceId={workspaceId}
              eventId={selected.public_id}
            />
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
