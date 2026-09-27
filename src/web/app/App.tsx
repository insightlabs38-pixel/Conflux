import { useCallback, useEffect, useState } from "react";
import { AppShell } from "../components/AppShell";
import { Button } from "../components/Button";
import { EventDashboard } from "../features/event-builder/EventDashboard";
import { JudgeWorkspace } from "../features/judging/JudgeWorkspace";
import { TeamWorkspace } from "../features/teams/TeamWorkspace";
import { EventSite } from "../public/event-site/EventSite";
import { WorkspaceSelector } from "./WorkspaceSelector";

// Guarded for non-browser rendering (tests, SSR) where `window` is unavailable.
function workspaceFromLocation(): string | null {
  if (typeof window === "undefined") return null;
  return new URLSearchParams(window.location.search).get("workspace");
}

// A bare `?event=<id>` link (no `workspace`) is the public, unauthenticated
// event site; it never requires a session.
function publicEventFromLocation(): string | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  return params.get("workspace") ? null : params.get("event");
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
  const publicEventId = publicEventFromLocation();

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

  if (publicEventId) {
    return <EventSite eventId={publicEventId} />;
  }

  return (
    <AppShell
      nav={
        workspaceId && (
          <Button variant="secondary" onClick={backToWorkspaces}>
            Back to workspaces
          </Button>
        )
      }
    >
      {workspaceId ? (
        workspaceRole === "participant" ? (
          <TeamWorkspace workspaceId={workspaceId} />
        ) : workspaceRole === "judge" ? (
          <JudgeWorkspace workspaceId={workspaceId} />
        ) : (
          <EventDashboard workspaceId={workspaceId} />
        )
      ) : (
        <WorkspaceSelector onSelect={selectWorkspace} />
      )}
    </AppShell>
  );
}
