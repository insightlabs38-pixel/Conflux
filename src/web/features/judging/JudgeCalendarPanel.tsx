import { useEffect, useState } from "react";
import { Badge } from "../../components/Badge";
import { Card } from "../../components/Card";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";

type Window = {
  name: string;
  opens_at: string | null;
  closes_at: string | null;
  status: "not_yet_open" | "open" | "closed";
};
type Assignment = {
  stage_name: string;
  plan: string;
  plan_name: string;
  rubric_published: boolean;
  assigned_count: number;
  submitted_count: number;
  completion_ratio: number;
};
type Calendar = { windows: Window[]; assignments: Assignment[] };

function message(error: unknown): string {
  if (error instanceof Error) return error.message;
  return "Request failed.";
}

const WINDOW_TONE: Record<Window["status"], "success" | "neutral" | "warning"> =
  {
    open: "success",
    not_yet_open: "neutral",
    closed: "warning",
  };

// The judge's own time-aware view of this event (S24): its open/closed
// windows plus per-plan assigned/submitted progress, so a judge can see
// where they stand without opening every plan one at a time.
export function JudgeCalendarPanel({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const [calendar, setCalendar] = useState<Calendar | null>(null);
  const [error, setError] = useState("");

  function load() {
    setError("");
    void fetch(
      `/api/v1/workspaces/${workspaceId}/events/${eventId}/judge-calendar/`,
      { credentials: "include" },
    )
      .then(async (response) => {
        if (!response.ok)
          throw new Error(`Request failed (${response.status}).`);
        return (await response.json()) as Calendar;
      })
      .then(setCalendar)
      .catch((cause: unknown) => setError(message(cause)));
  }
  useEffect(load, [workspaceId, eventId]);

  return (
    <Card title="My judging calendar" as="h4">
      {error && <ErrorState message={error} onRetry={load} />}
      {!error && calendar === null && (
        <LoadingState label="Loading your judging calendar…" />
      )}
      {!error && calendar !== null && (
        <>
          {calendar.windows.length > 0 && (
            <ul aria-label="Event windows">
              {calendar.windows.map((window) => (
                <li key={window.name}>
                  <Badge tone={WINDOW_TONE[window.status]}>
                    {window.status.replace(/_/g, " ")}
                  </Badge>{" "}
                  {window.name}
                </li>
              ))}
            </ul>
          )}
          {calendar.assignments.length === 0 ? (
            <p>You have no assigned candidates yet.</p>
          ) : (
            <ul aria-label="My plan assignments">
              {calendar.assignments.map((assignment) => (
                <li key={assignment.plan}>
                  {assignment.stage_name} &middot; {assignment.plan_name}:{" "}
                  {assignment.submitted_count}/{assignment.assigned_count}{" "}
                  submitted
                  {!assignment.rubric_published &&
                    " (rubric not yet published)"}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </Card>
  );
}
