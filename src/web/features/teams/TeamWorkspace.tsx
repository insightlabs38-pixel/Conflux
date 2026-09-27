import { useEffect, useState } from "react";
import { TeamPanel } from "./TeamPanel";
import { MarketplacePanel } from "./MarketplacePanel";
import { ProjectWorkspace } from "../artifacts/ProjectWorkspace";
import { Inbox } from "../communications/Inbox";
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
      <h2>Join an event team</h2>
      <Inbox workspaceId={workspaceId} />
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
      {!loading &&
        !error &&
        selectedId &&
        events.some((event) => event.public_id === selectedId) && (
          <>
            <TeamPanel
              key={selectedId}
              workspaceId={workspaceId}
              eventId={selectedId}
              onTeamChange={() => setTeamRevision((revision) => revision + 1)}
            />
            <MarketplacePanel
              key={`marketplace-${selectedId}-${teamRevision}`}
              workspaceId={workspaceId}
              eventId={selectedId}
            />
            <ProjectWorkspace
              key={`projects-${selectedId}`}
              workspaceId={workspaceId}
              eventId={selectedId}
            />
          </>
        )}
    </section>
  );
}
