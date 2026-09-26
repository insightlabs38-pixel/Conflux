import { EventDashboard } from "../features/event-builder/EventDashboard";

export function App() {
  // No workspace-selection UI exists yet; a workspace id passed via query string is the current entry point.
  // Guarded for non-browser rendering (tests, SSR) where `window` is unavailable.
  const workspaceId =
    typeof window === "undefined"
      ? null
      : new URLSearchParams(window.location.search).get("workspace");

  return (
    <main>
      <h1>Conflux</h1>
      {workspaceId ? (
        <EventDashboard workspaceId={workspaceId} />
      ) : (
        <p>Platform setup is in progress.</p>
      )}
    </main>
  );
}
