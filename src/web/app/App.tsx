import { useCallback, useEffect, useState } from "react";
import { EventDashboard } from "../features/event-builder/EventDashboard";
import { TeamWorkspace } from "../features/teams/TeamWorkspace";
import { WorkspaceSelector } from "./WorkspaceSelector";

// Guarded for non-browser rendering (tests, SSR) where `window` is unavailable.
function workspaceFromLocation(): string | null {
  if (typeof window === "undefined") return null;
  return new URLSearchParams(window.location.search).get("workspace");
}

function setWorkspaceParam(id: string | null) {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  if (id) url.searchParams.set("workspace", id);
  else url.searchParams.delete("workspace");
  window.history.pushState({}, "", url);
}

export function App() {
  const [workspaceId, setWorkspaceId] = useState<string | null>(
    workspaceFromLocation,
  );
  const [workspaceRole, setWorkspaceRole] = useState<string | null>(null);

  useEffect(() => {
    if (!workspaceId || workspaceRole) return;
    let active = true;
    fetch("/api/v1/accounts/me/", { credentials: "include" })
      .then((response) => (response.ok ? response.json() : null))
      .then(
        (
          me: { memberships?: { workspace: string; role: string }[] } | null,
        ) => {
          if (active)
            setWorkspaceRole(
              me?.memberships?.find(
                (membership) => membership.workspace === workspaceId,
              )?.role ?? null,
            );
        },
      )
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [workspaceId, workspaceRole]);

  const selectWorkspace = useCallback((id: string, role: string) => {
    setWorkspaceParam(id);
    setWorkspaceId(id);
    setWorkspaceRole(role);
  }, []);

  const backToWorkspaces = useCallback(() => {
    setWorkspaceParam(null);
    setWorkspaceId(null);
    setWorkspaceRole(null);
  }, []);

  return (
    <main>
      <h1>Conflux</h1>
      {workspaceId ? (
        <>
          <button type="button" onClick={backToWorkspaces}>
            Back to workspaces
          </button>
          {workspaceRole === "participant" ? (
            <TeamWorkspace workspaceId={workspaceId} />
          ) : (
            <EventDashboard workspaceId={workspaceId} />
          )}
        </>
      ) : (
        <WorkspaceSelector onSelect={selectWorkspace} />
      )}
    </main>
  );
}
