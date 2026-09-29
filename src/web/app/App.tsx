import { useCallback, useEffect, useState } from "react";
import { WorkspaceNavigationProvider } from "../components/WorkspaceNavigation";
import { AppShell } from "../components/AppShell";
import { Button } from "../components/Button";
import { DeniedState } from "../components/DeniedState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { EventDashboard } from "../features/event-builder/EventDashboard";
import { JudgeWorkspace } from "../features/judging/JudgeWorkspace";
import { TeamWorkspace } from "../features/teams/TeamWorkspace";
import { StaffWorkspace } from "../features/pvs/StaffWorkspace";
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
  else {
    url.searchParams.delete("workspace");
    url.searchParams.delete("event");
    url.searchParams.delete("invite");
    url.searchParams.delete("view");
  }
  window.history.pushState({}, "", url);
}

export function App() {
  const [workspaceId, setWorkspaceId] = useState<string | null>(
    workspaceFromLocation,
  );
  const [signingOut, setSigningOut] = useState(false);
  const [workspaceName, setWorkspaceName] = useState("");
  const [username, setUsername] = useState("");
  const [workspaceRole, setWorkspaceRole] = useState<string | null>(null);
  const [roleState, setRoleState] = useState<
    "loading" | "ready" | "denied" | "error"
  >("loading");
  const [roleRetry, setRoleRetry] = useState(0);
  const publicEventId = publicEventFromLocation();

  useEffect(() => {
    if (!workspaceId) return;
    let active = true;
    if (!workspaceRole) setRoleState("loading");
    fetch("/api/v1/accounts/me/", { credentials: "include" })
      .then((response) => {
        if (!response.ok) throw new Error("Could not check workspace access.");
        return response.json();
      })
      .then(
        (me: {
          username?: string;
          memberships?: {
            workspace: string;
            workspace_name?: string;
            role: string;
          }[];
        }) => {
          if (!active) return;
          setUsername(me.username || "");
          const membership = me?.memberships?.find(
            (membership) => membership.workspace === workspaceId,
          );
          const role = membership?.role;
          setWorkspaceName(membership?.workspace_name || "");
          if (
            role === "participant" ||
            role === "judge" ||
            role === "mentor" ||
            role === "volunteer" ||
            role === "organizer" ||
            role === "admin"
          ) {
            setWorkspaceRole(role);
            setRoleState("ready");
          } else {
            setWorkspaceRole(null);
            setRoleState("denied");
          }
        },
      )
      .catch(() => {
        if (active) setRoleState("error");
      });
    return () => {
      active = false;
    };
  }, [workspaceId, roleRetry]);

  const selectWorkspace = useCallback((id: string, role: string) => {
    setWorkspaceParam(id);
    setWorkspaceId(id);
    setWorkspaceRole(role);
    setRoleState("ready");
  }, []);

  const backToWorkspaces = useCallback(() => {
    setWorkspaceParam(null);
    setWorkspaceId(null);
    setWorkspaceRole(null);
    setWorkspaceName("");
    setRoleState("loading");
  }, []);

  const signOut = useCallback(async () => {
    setSigningOut(true);
    await fetch("/api/v1/accounts/logout/", {
      method: "POST",
      credentials: "include",
    }).catch(() => undefined);
    setUsername("");
    backToWorkspaces();
    setSigningOut(false);
  }, [backToWorkspaces]);

  if (publicEventId) {
    return <EventSite eventId={publicEventId} />;
  }

  return (
    <WorkspaceNavigationProvider
      key={workspaceId || "selection"}
      role={workspaceRole || ""}
    >
      <AppShell
        role={
          roleState === "ready" && workspaceId
            ? workspaceRole || undefined
            : undefined
        }
        username={username}
        workspaceName={workspaceName}
        onSignOut={signOut}
        signingOut={signingOut}
        brandAs={workspaceId && roleState === "ready" ? "p" : "h1"}
        nav={
          <>
            <a href="/?api=explorer">API explorer</a>
            {workspaceId && (
              <Button variant="secondary" onClick={backToWorkspaces}>
                Back to workspaces
              </Button>
            )}
          </>
        }
      >
        {workspaceId ? (
          roleState === "loading" ? (
            <LoadingState label="Checking workspace access…" />
          ) : roleState === "error" ? (
            <ErrorState
              message="Could not check workspace access."
              onRetry={() => setRoleRetry((count) => count + 1)}
            />
          ) : roleState === "denied" ? (
            <DeniedState message="You are not a member of this workspace." />
          ) : workspaceRole === "participant" ? (
            <TeamWorkspace key={workspaceId} workspaceId={workspaceId} />
          ) : workspaceRole === "judge" ? (
            <JudgeWorkspace key={workspaceId} workspaceId={workspaceId} />
          ) : workspaceRole === "mentor" || workspaceRole === "volunteer" ? (
            <StaffWorkspace
              key={workspaceId}
              workspaceId={workspaceId}
              role={workspaceRole}
            />
          ) : workspaceRole === "organizer" || workspaceRole === "admin" ? (
            <EventDashboard key={workspaceId} workspaceId={workspaceId} />
          ) : (
            <DeniedState />
          )
        ) : (
          <WorkspaceSelector onSelect={selectWorkspace} />
        )}
      </AppShell>
    </WorkspaceNavigationProvider>
  );
}
