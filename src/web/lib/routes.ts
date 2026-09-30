/**
 * The application's route hierarchy (PD-B04-T01). Every in-app link, redirect and test builds URLs
 * here; nothing else composes path or query strings for navigation.
 *
 *   /                          workspace selector (and sign-in)
 *   /w/:workspaceId            -> /w/:workspaceId/overview
 *   /w/:workspaceId/:view      role workspace; `view` is one of the role's destinations (roleDestinations)
 *                              search: context params `event`, `stage`, `plan` and the `invite` entry
 *                              token; the rules for what belongs in a URL are in lib/urlState.ts
 *   /person/:personId          public person profile
 *   /event/:eventId            public event site (no session)
 *   /api-explorer              API explorer
 *
 * The app is served under a base path (`/app` behind the gateway, `` on the Vite dev server), which
 * the router strips; `appHref` adds it back for links that leave the router (new tabs, copied links).
 *
 * Compatibility: the pre-router app kept all state in the query string of `/` (`?workspace=&view=`,
 * `?person=`, `?event=`, `?api=explorer`). Those URLs are still emitted by the API (`profile_url`),
 * old invite links and bookmarks, so `legacyTarget` maps them onto the canonical routes.
 */
const enc = encodeURIComponent;

export const routes = {
  home: "/",
  workspace: (workspaceId: string, view?: string) =>
    view
      ? `/w/${enc(workspaceId)}/${enc(view)}`
      : `/w/${enc(workspaceId)}/overview`,
  person: (personId: string) => `/person/${enc(personId)}`,
  publicEvent: (eventId: string) => `/event/${enc(eventId)}`,
  apiExplorer: "/api-explorer",
} as const;

/** Base path the app is mounted on: `/app` behind the gateway, `` on the dev server and in tests. */
export function appBasename(pathname?: string): string {
  const path =
    pathname ?? (typeof window === "undefined" ? "" : window.location.pathname);
  return path === "/app" || path.startsWith("/app/") ? "/app" : "";
}

/** An absolute-path URL for a route, including the base path (for new tabs and shareable links). */
export function appHref(to: string): string {
  return appBasename() + to;
}

/**
 * Canonical location (path + search) for a legacy query-string URL at `/`, or null when the URL is
 * not a legacy one. Precedence mirrors the old app: API explorer, person, public event (an `event`
 * with no `workspace`), then a workspace with its optional `view`; unrelated params are dropped and
 * `event`/`invite` ride along as search params on the workspace route.
 */
export function legacyTarget(search: string): string | null {
  const params = new URLSearchParams(search);
  if (params.get("api") === "explorer") return routes.apiExplorer;
  const person = params.get("person");
  if (person) return routes.person(person);
  const workspace = params.get("workspace");
  const event = params.get("event");
  if (!workspace) return event ? routes.publicEvent(event) : null;
  const carried = new URLSearchParams();
  if (event) carried.set("event", event);
  const invite = params.get("invite");
  if (invite) carried.set("invite", invite);
  const query = carried.toString();
  return (
    routes.workspace(workspace, params.get("view") || undefined) +
    (query ? `?${query}` : "")
  );
}
