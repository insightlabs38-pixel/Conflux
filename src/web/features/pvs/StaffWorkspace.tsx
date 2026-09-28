import { useState } from "react";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { Inbox } from "../communications/Inbox";
import { useLoad } from "./http";
import { MentorDeskPanel } from ".";
import { OnsiteOperationsPanel } from ".";

type Event = { public_id: string; name: string };

/** Event-day workspace for mentors (help queue, office hours) and volunteers (check-in desk). */
export function StaffWorkspace({
  workspaceId,
  role,
}: {
  workspaceId: string;
  role: "mentor" | "volunteer";
}) {
  const events = useLoad<Event[]>(
    `/api/v1/workspaces/${workspaceId}/participant-events/`,
  );
  const [eventId, setEventId] = useState("");
  return (
    <section aria-label={role === "mentor" ? "Mentoring" : "Event desk"}>
      <h2>{role === "mentor" ? "Mentoring" : "Event desk"}</h2>
      <Inbox workspaceId={workspaceId} />
      {events.loading && <LoadingState label="Loading events…" />}
      {events.error && (
        <ErrorState message={events.error.message} onRetry={events.reload} />
      )}
      {events.data && events.data.length === 0 && (
        <EmptyState title="No events are open right now." />
      )}
      {events.data && events.data.length > 0 && (
        <label>
          Event{" "}
          <select
            value={eventId}
            onChange={(event) => setEventId(event.target.value)}
          >
            <option value="">Choose an event</option>
            {events.data.map((event) => (
              <option key={event.public_id} value={event.public_id}>
                {event.name}
              </option>
            ))}
          </select>
        </label>
      )}
      {eventId &&
        (role === "mentor" ? (
          <MentorDeskPanel
            key={eventId}
            workspaceId={workspaceId}
            eventId={eventId}
            isOrganizer={false}
          />
        ) : (
          <OnsiteOperationsPanel
            key={eventId}
            workspaceId={workspaceId}
            eventId={eventId}
            canManage={false}
          />
        ))}
    </section>
  );
}
