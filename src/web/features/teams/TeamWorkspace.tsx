import { WorkflowSections } from "../../components/WorkflowSections";
import { ProfilePanel } from "../profile/ProfilePanel";
import {
  Destination,
  WorkspaceViewTitle,
} from "../../components/WorkspaceNavigation";
import { PageHeader } from "../../components/Foundation";
import { useEffect, useState } from "react";
import { ParticipantOverview } from "./ParticipantOverview";
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
        {selectedId &&
        events.some((event) => event.public_id === selectedId) ? (
          <ParticipantOverview
            key={`${selectedId}-${teamRevision}`}
            workspaceId={workspaceId}
            eventId={selectedId}
          />
        ) : (
          <p>Choose an event to see your team, deadlines, and next action.</p>
        )}
      </Destination>
      {!loading &&
        !error &&
        selectedId &&
        events.some((event) => event.public_id === selectedId) && (
          <>
            <Destination id="team">
              <WorkflowSections
                label="Team tasks"
                sections={[
                  {
                    id: "roster",
                    label: "Your team",
                    description: "Roster and invitations",
                    content: (
                      <TeamPanel
                        key={selectedId}
                        workspaceId={workspaceId}
                        eventId={selectedId}
                        onTeamChange={() =>
                          setTeamRevision((revision) => revision + 1)
                        }
                      />
                    ),
                  },
                  {
                    id: "marketplace",
                    label: "Find teammates",
                    description: "People, skills and team fit",
                    content: (
                      <MarketplacePanel
                        key={`marketplace-${selectedId}-${teamRevision}`}
                        workspaceId={workspaceId}
                        eventId={selectedId}
                      />
                    ),
                  },
                ]}
              />
            </Destination>
            <Destination id="resources">
              <WorkflowSections
                label="Event resources"
                sections={[
                  {
                    id: "rules",
                    label: "Rules",
                    description: "Read and acknowledge",
                    content: (
                      <RulesPanel
                        key={`rules-${selectedId}`}
                        workspaceId={workspaceId}
                        eventId={selectedId}
                        canPublish={false}
                      />
                    ),
                  },
                  {
                    id: "challenges",
                    label: "Sponsor challenges",
                    description: "Resources and prizes",
                    content: (
                      <ChallengesPanel
                        key={`challenges-${selectedId}`}
                        workspaceId={workspaceId}
                        eventId={selectedId}
                      />
                    ),
                  },
                  {
                    id: "onsite",
                    label: "On-site participation",
                    description: "Attendance and requests",
                    content: (
                      <MyOnsitePanel
                        key={`onsite-${selectedId}`}
                        workspaceId={workspaceId}
                        eventId={selectedId}
                      />
                    ),
                  },
                ]}
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
