import { WorkflowSections } from "../../components/WorkflowSections";
import { ProfilePanel } from "../profile/ProfilePanel";
import {
  Destination,
  WorkspaceViewTitle,
} from "../../components/WorkspaceNavigation";
import { PageHeader } from "../../components/Foundation";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiCall } from "../../lib/api";
import { queryKeys } from "../../lib/query";
import { useUrlParam } from "../../lib/urlState";
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

export function TeamWorkspace({ workspaceId }: { workspaceId: string }) {
  // The selected event is context (lib/urlState.ts): it survives refresh, back/forward and sharing.
  const [selectedId, selectEvent] = useUrlParam("event", {
    clears: ["invite"],
  });
  const eventsQuery = useQuery({
    queryKey: queryKeys.participantEvents(workspaceId),
    queryFn: ({ signal }) =>
      apiCall(
        "get_api_v1_workspaces_workspace_public_id_participant_events",
        { path: { workspace_public_id: workspaceId } },
        { signal, describe: (status) => `Could not load events (${status}).` },
      ),
  });
  const events = eventsQuery.data ?? [];
  const loading =
    eventsQuery.isPending || (eventsQuery.isFetching && eventsQuery.isError);
  const error =
    eventsQuery.isError && !eventsQuery.isFetching
      ? eventsQuery.error.message || "Could not load events."
      : "";
  const [teamRevision, setTeamRevision] = useState(0);

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
          onRetry={() => void eventsQuery.refetch()}
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
