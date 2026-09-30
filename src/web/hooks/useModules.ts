import { useCallback, useRef } from "react";
import { apiJson, describeProblem } from "../lib/api";
import { useLoad } from "./useLoad";

/** One optional module of an event, as the server computed it (eventconfig/modules.py). */
export type ModuleState = {
  key: string;
  label: string;
  description: string;
  /** The organizer destination this module owns (null when it only owns panels). */
  destination: string | null;
  /** Switched on by an organizer or already holding content. */
  enabled: boolean;
  in_use: boolean;
  explicit: boolean | null;
  can_disable: boolean;
  reason: string;
};
type ModuleList = {
  scope: "event" | "workspace";
  event: string | null;
  modules: ModuleState[];
};

export type Modules = {
  /** Null until the first answer; the last known list is kept while another event's loads. */
  modules: ModuleState[] | null;
  /** The event the list describes (null for the workspace union). */
  eventId: string | null;
  setEnabled: (eventId: string, key: string, enabled: boolean) => Promise<void>;
  reload: () => Promise<void>;
};

/**
 * Which optional modules an organizer's navigation and panels offer. Visibility is a function of
 * the server's answer (enabled = switched on or has content) for the selected event, or the
 * workspace union when none is selected. It is never authorization: every endpoint keeps its own
 * permission check. Inactive (non-organizer roles) makes no request and returns null.
 */
export function useModules(
  workspaceId: string,
  eventId: string,
  active: boolean,
): Modules {
  const base = `/api/v1/workspaces/${workspaceId}/`;
  const url = active
    ? `${base}modules/${eventId ? `?event=${encodeURIComponent(eventId)}` : ""}`
    : null;
  const load = useLoad<ModuleList>(url, { describe: describeProblem });
  const last = useRef<ModuleList | null>(null);
  if (load.data) last.current = load.data;
  if (!active) last.current = null;
  const shown = load.data ?? last.current;

  const setEnabled = useCallback(
    async (targetEvent: string, key: string, enabled: boolean) => {
      const next = await apiJson<ModuleList>(
        `${base}events/${targetEvent}/modules/${key}/`,
        "PATCH",
        { enabled },
      );
      // The answer is the event's effective list; the loaded list (event or union) is refetched.
      load.update((current) =>
        current?.scope === "event" && current.event === next.event
          ? next
          : current,
      );
      await load.reload();
    },
    [base, load],
  );

  return {
    modules: shown?.modules ?? null,
    eventId: shown?.event ?? null,
    setEnabled,
    reload: load.reload,
  };
}
