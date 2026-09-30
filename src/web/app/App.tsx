import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
  StaticRouter,
  useLocation,
  useNavigate,
  useParams,
} from "react-router";
import { PersonProfilePage } from "../features/profile/PersonProfilePage";
import {
  roleDestinations,
  WorkspaceNavigationProvider,
} from "../components/WorkspaceNavigation";
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
import { appBasename, legacyTarget, routes } from "../lib/routes";
import { SignIn } from "./SignIn";
import { WorkspaceSelector } from "./WorkspaceSelector";

const ApiExplorer = lazy(() => import("../features/api-explorer/ApiExplorer"));

type RoleState = "loading" | "ready" | "denied" | "error" | "signed-out";
const ROLES = [
  "participant",
  "judge",
  "mentor",
  "volunteer",
  "organizer",
  "admin",
];

/** The history router for the browser; a static one when there is no `window` (tests, SSR). */
function AppRouter({ children }: { children: ReactNode }) {
  const [basename] = useState(() => appBasename());
  return typeof window === "undefined" ? (
    <StaticRouter location="/">{children}</StaticRouter>
  ) : (
    <BrowserRouter basename={basename}>{children}</BrowserRouter>
  );
}

/** Shared page chrome for routes that are not a role workspace. */
function Page({ children }: { children: ReactNode }) {
  return (
    <AppShell
      brandAs="h1"
      nav={<Link to={routes.apiExplorer}>API explorer</Link>}
    >
      {children}
    </AppShell>
  );
}

// `/`: the workspace selector, or a legacy query-string URL (see lib/routes.ts) sent to its route.
function RootRoute() {
  const { search } = useLocation();
  const navigate = useNavigate();
  const legacy = legacyTarget(search);
  if (legacy) return <Navigate to={legacy} replace />;
  return (
    <Page>
      <WorkspaceSelector
        onSelect={(workspaceId) => navigate(routes.workspace(workspaceId))}
      />
    </Page>
  );
}

// `/w/:workspaceId/:view`: resolves the member's role, then mounts that role's workspace once; the
// view only changes which destination is visible, so drafts in other destinations stay mounted.
function WorkspaceRoute() {
  const { workspaceId = "", view = "overview" } = useParams();
  const { search } = useLocation();
  const navigate = useNavigate();
  const [roleState, setRoleState] = useState<RoleState>("loading");
  const [role, setRole] = useState<string | null>(null);
  const [username, setUsername] = useState("");
  const [workspaceName, setWorkspaceName] = useState("");
  const [signingOut, setSigningOut] = useState(false);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let active = true;
    setRoleState((state) => (state === "ready" ? state : "loading"));
    fetch("/api/v1/accounts/me/", { credentials: "include" })
      .then((response) => {
        if (response.status === 401) return null;
        if (!response.ok) throw new Error("Could not check workspace access.");
        return response.json();
      })
      .then(
        (
          me: {
            username?: string;
            memberships?: {
              workspace: string;
              workspace_name?: string;
              role: string;
            }[];
          } | null,
        ) => {
          if (!active) return;
          if (!me) {
            setRoleState("signed-out");
            return;
          }
          setUsername(me.username || "");
          const membership = me.memberships?.find(
            (candidate) => candidate.workspace === workspaceId,
          );
          setWorkspaceName(membership?.workspace_name || "");
          if (membership && ROLES.includes(membership.role)) {
            setRole(membership.role);
            setRoleState("ready");
          } else {
            setRole(null);
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
  }, [workspaceId, retry]);

  const backToWorkspaces = useCallback(() => navigate(routes.home), [navigate]);
  const signOut = useCallback(async () => {
    setSigningOut(true);
    await fetch("/api/v1/accounts/logout/", {
      method: "POST",
      credentials: "include",
    }).catch(() => undefined);
    setUsername("");
    setSigningOut(false);
    navigate(routes.home);
  }, [navigate]);

  // A view this role does not have is not a place: send the URL to the overview.
  const destinations = role ? roleDestinations[role] : undefined;
  if (
    roleState === "ready" &&
    destinations &&
    !destinations.some((item) => item.id === view)
  )
    return <Navigate to={routes.workspace(workspaceId) + search} replace />;

  const ready = roleState === "ready" && role;
  return (
    <WorkspaceNavigationProvider role={role || ""} workspaceId={workspaceId}>
      <AppShell
        role={ready ? role : undefined}
        username={username}
        workspaceName={workspaceName}
        onSignOut={signOut}
        signingOut={signingOut}
        brandAs={ready ? "p" : "h1"}
        nav={
          <>
            <Link to={routes.apiExplorer}>API explorer</Link>
            <Button variant="secondary" onClick={backToWorkspaces}>
              Back to workspaces
            </Button>
          </>
        }
      >
        {roleState === "loading" ? (
          <LoadingState label="Checking workspace access…" />
        ) : roleState === "signed-out" ? (
          <SignIn onSignedIn={() => setRetry((count) => count + 1)} />
        ) : roleState === "error" ? (
          <ErrorState
            message="Could not check workspace access."
            onRetry={() => setRetry((count) => count + 1)}
          />
        ) : roleState === "denied" ? (
          <DeniedState message="You are not a member of this workspace." />
        ) : role === "participant" ? (
          <TeamWorkspace key={workspaceId} workspaceId={workspaceId} />
        ) : role === "judge" ? (
          <JudgeWorkspace key={workspaceId} workspaceId={workspaceId} />
        ) : role === "mentor" || role === "volunteer" ? (
          <StaffWorkspace
            key={workspaceId}
            workspaceId={workspaceId}
            role={role}
          />
        ) : role === "organizer" || role === "admin" ? (
          <EventDashboard key={workspaceId} workspaceId={workspaceId} />
        ) : (
          <DeniedState />
        )}
      </AppShell>
    </WorkspaceNavigationProvider>
  );
}

function PersonRoute() {
  const { personId = "" } = useParams();
  return <PersonProfilePage personId={personId} />;
}

function PublicEventRoute() {
  const { eventId = "" } = useParams();
  return <EventSite eventId={eventId} />;
}

function NotFoundRoute() {
  return (
    <Page>
      <DeniedState message="That page does not exist." />
      <p>
        <Link to={routes.home}>Back to workspaces</Link>
      </p>
    </Page>
  );
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<RootRoute />} />
      <Route path="/w/:workspaceId" element={<WorkspaceIndexRedirect />} />
      <Route path="/w/:workspaceId/:view" element={<WorkspaceRoute />} />
      <Route path="/person/:personId" element={<PersonRoute />} />
      <Route path="/event/:eventId" element={<PublicEventRoute />} />
      <Route
        path="/api-explorer"
        element={
          <Suspense fallback={<p>Loading API explorer…</p>}>
            <ApiExplorer />
          </Suspense>
        }
      />
      <Route path="*" element={<NotFoundRoute />} />
    </Routes>
  );
}

function WorkspaceIndexRedirect() {
  const { workspaceId = "" } = useParams();
  const { search } = useLocation();
  return <Navigate to={routes.workspace(workspaceId) + search} replace />;
}

export function App() {
  return (
    <AppRouter>
      <AppRoutes />
    </AppRouter>
  );
}
