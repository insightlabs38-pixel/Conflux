import { ProfilePanel } from "../profile/ProfilePanel";
import {
  Destination,
  DestinationLink,
  WorkspaceViewTitle,
} from "../../components/WorkspaceNavigation";
import { PageHeader, Grid } from "../../components/Foundation";
import { useEffect, useState } from "react";
import { TeamPanel } from "./TeamPanel";
import { MarketplacePanel } from "./MarketplacePanel";
import { ProjectWorkspace } from "../artifacts/ProjectWorkspace";
import { Inbox } from "../communications/Inbox";
import {
  ChallengesPanel,
  MyOnsitePanel,
  PortfolioPanel,
  RulesPanel,
} from "../pvs";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";

type Event = { public_id: string; name: string };

function eventFromLocation(): string {
  return typeof window === "undefined"
    ? ""
    : (new URLSearchParams(window.location.search).get("event") ?? "");
}

export function TeamWorkspace({ workspaceId }: { workspaceId: string }) {
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedId, setSelectedId] = useState(eventFromLocation);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);
  const [teamRevision, setTeamRevision] = useState(0);

  function selectEvent(id: string) {
    setSelectedId(id);
    if (typeof window === "undefined") return;
    const url = new URL(window.location.href);
    if (id) url.searchParams.set("event", id);
    else url.searchParams.delete("event");
    url.searchParams.delete("invite");
    window.history.pushState({}, "", url);
  }

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    fetch(`/api/v1/workspaces/${workspaceId}/participant-events/`, {
      credentials: "include",
    })
      .then((response) => {
        if (!response.ok)
          throw new Error(`Could not load events (${response.status}).`);
        return response.json() as Promise<Event[]>;
      })
      .then((items) => {
        if (active) setEvents(items);
      })
      .catch((cause: unknown) => {
        if (active)
          setError(
            cause instanceof Error ? cause.message : "Could not load events.",
          );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [workspaceId, retry]);

  return (
    <section aria-label="Participant events">
      <PageHeader
        as="h1"
        title="Participant workspace"
        eyebrow={
          events.find((event) => event.public_id === selectedId)?.name ||
          "Your events"
        }
        description="Bring your team together, build your project, and get ready to submit."
      />
      <WorkspaceViewTitle role="participant" />
      <Destination id="messages">
        <Inbox workspaceId={workspaceId} />
      </Destination>
      <Destination id="profile" lazy>
        <ProfilePanel />
        <PortfolioPanel workspaceId={workspaceId} />
      </Destination>
      {loading && <LoadingState label="Loading events…" />}
      {error && (
        <ErrorState
          message={error}
          onRetry={() => setRetry((count) => count + 1)}
        />
      )}
      {!loading && !error && events.length === 0 && (
        <p>No events are open for participation.</p>
      )}
      {!loading &&
        !error &&
        selectedId &&
        !events.some((event) => event.public_id === selectedId) && (
          <p role="alert">
            This event is not available for participation. Choose another event
            or return to workspaces.
          </p>
        )}
      {!loading && !error && events.length > 0 && (
        <label>
          Event{" "}
          <select
            value={selectedId}
            onChange={(event) => selectEvent(event.target.value)}
          >
            <option value="">Choose an event</option>
            {events.map((event) => (
              <option key={event.public_id} value={event.public_id}>
                {event.name}
              </option>
            ))}
          </select>
        </label>
      )}
      <Destination id="overview">
        <section
          className="cx-workspace-overview"
          aria-label="Participant overview"
        >
          <h2>Your next steps</h2>
          <Grid>
            <DestinationLink id="team">
              <strong>1. Get your team ready</strong>
              <span>Manage your roster, invitations, and find teammates.</span>
            </DestinationLink>
            <DestinationLink id="project">
              <strong>2. Build and submit</strong>
              <span>
                Prepare your project, evidence, and finalized submission.
              </span>
            </DestinationLink>
            <DestinationLink id="resources">
              <strong>3. Stay connected to the event</strong>
              <span>
                Rules, sponsor challenges, sessions, and participation.
              </span>
            </DestinationLink>
          </Grid>
        </section>
      </Destination>
      {!loading &&
        !error &&
        selectedId &&
        events.some((event) => event.public_id === selectedId) && (
          <>
            <Destination id="team">
              <TeamPanel
                key={selectedId}
                workspaceId={workspaceId}
                eventId={selectedId}
                onTeamChange={() => setTeamRevision((revision) => revision + 1)}
              />
            </Destination>
            <Destination id="team">
              <MarketplacePanel
                key={`marketplace-${selectedId}-${teamRevision}`}
                workspaceId={workspaceId}
                eventId={selectedId}
              />
            </Destination>
            <Destination id="resources">
              <RulesPanel
                key={`rules-${selectedId}`}
                workspaceId={workspaceId}
                eventId={selectedId}
                canPublish={false}
              />
            </Destination>
            <Destination id="resources">
              <ChallengesPanel
                key={`challenges-${selectedId}`}
                workspaceId={workspaceId}
                eventId={selectedId}
              />
            </Destination>
            <Destination id="resources">
              <MyOnsitePanel
                key={`onsite-${selectedId}`}
                workspaceId={workspaceId}
                eventId={selectedId}
              />
            </Destination>
            <Destination id="project">
              <ProjectWorkspace
                key={`projects-${selectedId}`}
                workspaceId={workspaceId}
                eventId={selectedId}
              />
            </Destination>
          </>
        )}
    </section>
  );
}
