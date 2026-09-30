import { describeProblem } from "../lib/api";
import { useLoad, type Loaded } from "./useLoad";

export type ReadinessItem = {
  id: string;
  severity: "blocker" | "warning";
  passed: boolean;
  detail: string;
  module: string;
  fix: { destination: string; section: string };
};
export type Readiness = {
  status: "ready" | "warning" | "blocked";
  items: ReadinessItem[];
};

/**
 * The event's readiness: the one list of what is missing before launch (server rules, eventconfig/
 * readiness.py). Every surface that talks about readiness reads this, none recomputes it.
 */
export function useReadiness(
  workspaceId: string,
  eventId: string | null,
): Loaded<Readiness> {
  return useLoad<Readiness>(
    eventId
      ? `/api/v1/workspaces/${workspaceId}/events/${eventId}/readiness/`
      : null,
    { describe: describeProblem },
  );
}

/** Unresolved items, blockers first (stable within a severity). */
export function unresolvedItems(readiness: Readiness | null): ReadinessItem[] {
  const open = (readiness?.items ?? []).filter((item) => !item.passed);
  return [
    ...open.filter((item) => item.severity === "blocker"),
    ...open.filter((item) => item.severity === "warning"),
  ];
}
