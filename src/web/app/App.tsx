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
import { QueryClientProvider, type QueryClient } from "@tanstack/react-query";
import { useMe, useSessionChanged, useSignOut } from "../hooks/useMe";
import { createQueryClient } from "../lib/query";
import { pollingTransport, RealtimeHub } from "../lib/realtime";
import { RealtimeProvider } from "../hooks/useRealtime";
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
import { pickRole, rolesIn } from "../lib/roles";
import { SignIn } from "./SignIn";
import { WorkspaceSelector } from "./WorkspaceSelector";

const ApiExplorer = lazy(() => import("../features/api-explorer/ApiExplorer"));

type RoleState = "loading" | "ready" | "denied" | "error" | "signed-out";

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
  const me = useMe();
  const signOutMutation = useSignOut();
  const sessionChanged = useSessionChanged();

  const membership = me.data?.memberships?.find(
    (candidate) => candidate.workspace === workspaceId,
  );
  // A person may hold several roles here; `as` (a URL context param) picks which of their own to
  // view as, otherwise the most privileged. It chooses a screen; the server still authorizes.
  const roles = rolesIn(me.data?.memberships, workspaceId);
  const requestedAs = new URLSearchParams(search).get("as") ?? "";
  const { role, requestedUnheld } = pickRole(roles, requestedAs);
  const roleState: RoleState =
    me.isPending || (me.isError && me.isFetching)
      ? "loading"
      : me.isError
        ? "error"
        : me.data === null
          ? "signed-out"
          : role
            ? "ready"
            : "denied";
  const username = me.data?.username || "";
  const workspaceName = membership?.workspace_name || "";

  const backToWorkspaces = useCallback(() => navigate(routes.home), [navigate]);
  const signOut = useCallback(async () => {
    await signOutMutation.mutateAsync();
    navigate(routes.home);
  }, [navigate, signOutMutation]);

  // A role the person does not hold is not a place either: drop it from the URL.
  if (roleState === "ready" && requestedUnheld) {
    const params = new URLSearchParams(search);
    params.delete("as");
    const text = params.toString();
    return (
      <Navigate
        to={routes.workspace(workspaceId, view) + (text ? `?${text}` : "")}
        replace
      />
    );
  }
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
    <WorkspaceNavigationProvider
      role={role || ""}
      roles={roles}
      workspaceId={workspaceId}
    >
      <AppShell
        role={ready ? role : undefined}
        username={username}
        workspaceName={workspaceName}
        onSignOut={signOut}
        signingOut={signOutMutation.isPending}
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
          <SignIn onSignedIn={sessionChanged} />
        ) : roleState === "error" ? (
          <ErrorState
            kind="read"
            message="Could not check workspace access."
            onRetry={() => void me.refetch()}
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

/** `queryClient` is injectable so tests (and embedders) control retries and cache lifetime. */
export function App({
  queryClient,
  realtimeHub,
}: {
  queryClient?: QueryClient;
  realtimeHub?: RealtimeHub;
}) {
  const [client] = useState(() => queryClient ?? createQueryClient());
  const [hub] = useState(
    () => realtimeHub ?? new RealtimeHub(pollingTransport()),
  );
  // Closing the hub with the app also releases timers and listeners when it is torn down.
  useEffect(() => () => hub.reset(), [hub]);
  return (
    <QueryClientProvider client={client}>
      <RealtimeProvider hub={hub}>
        <AppRouter>
          <AppRoutes />
        </AppRouter>
      </RealtimeProvider>
    </QueryClientProvider>
  );
}
