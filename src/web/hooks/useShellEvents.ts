import { useLoad } from "./useLoad";
import { describeProblem } from "../lib/api";

/** Where an event is in its life, as the server derives it (events.lifecycle). */
export type EventPhase = {
  key: "draft" | "open" | "closed" | "judging" | "published" | "archived";
  label: string;
  reason: string;
};
export type ShellEvent = {
  public_id: string;
  name: string;
  phase?: EventPhase;
};

/** The list each role already uses to choose an event (so these reads share one cache entry). */
export function shellEventsUrl(workspaceId: string, role: string): string {
  const base = `/api/v1/workspaces/${workspaceId}/`;
  if (role === "organizer" || role === "admin") return `${base}events/`;
  if (role === "judge") return `${base}judge-events/`;
  return `${base}participant-events/`; // participant, mentor, volunteer
}

/** The events this person may choose between in a workspace, for the switcher. */
export function useShellEvents(workspaceId: string, role: string) {
  const load = useLoad<ShellEvent[]>(
    workspaceId && role ? shellEventsUrl(workspaceId, role) : null,
    { describe: describeProblem },
  );
  return {
    events: Array.isArray(load.data) ? load.data : [],
    loading: load.loading,
    error: load.error?.message ?? "",
    reload: load.reload,
  };
}
