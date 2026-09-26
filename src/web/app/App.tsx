import { useCallback, useState } from "react";
import { EventDashboard } from "../features/event-builder/EventDashboard";
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

  const selectWorkspace = useCallback((id: string) => {
    setWorkspaceParam(id);
    setWorkspaceId(id);
  }, []);

  const backToWorkspaces = useCallback(() => {
    setWorkspaceParam(null);
    setWorkspaceId(null);
  }, []);

  return (
    <main>
      <h1>Conflux</h1>
      {workspaceId ? (
        <>
          <button type="button" onClick={backToWorkspaces}>
            Back to workspaces
          </button>
          <EventDashboard workspaceId={workspaceId} />
        </>
      ) : (
        <WorkspaceSelector onSelect={selectWorkspace} />
      )}
    </main>
  );
}
