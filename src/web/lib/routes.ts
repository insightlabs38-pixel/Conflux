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

/**
 * A place inside a workspace, as data: the view, an optional top-level section (tab) of it, the
 * event it is about and any other context or panel params (`stage`, `plan`, a selected record).
 * Search results, palette entries, breadcrumbs, the event switcher and the inbox all produce one of
 * these and build the URL with `routes.target`; nothing composes a workspace URL by hand.
 */
export type RouteTarget = {
  view: string;
  section?: string;
  event?: string;
  params?: Record<string, string>;
};

/** A param value is a public id or a value from a fixed set: never free text (lib/urlState.ts). */
const SAFE_VALUE = /^[A-Za-z0-9_.:-]{1,100}$/;
/** The context params come first, in the order the app has always written them. */
const CONTEXT_ORDER = ["stage", "plan", "invite"];
const SAFE_KEY = /^[a-z][a-z0-9_]{0,39}$/;

/**
 * The location (path and search) for a target. The query is ordered the same way every time -
 * `event`, the context params (`stage`, `plan`, `invite`), any other params by name, then `section` - so one place has one URL. A value that is not
 * an id-like token is a programming error (it would put typed text or personal data in a URL) and
 * throws instead of being quietly dropped.
 */
function workspaceTarget(workspaceId: string, target: RouteTarget): string {
  const pairs: [string, string][] = [];
  const add = (key: string, value: string | undefined) => {
    if (value === undefined || value === "") return;
    if (!SAFE_KEY.test(key) || !SAFE_VALUE.test(value))
      throw new TypeError(`"${key}" is not a safe URL param`);
    pairs.push([key, value]);
  };
  add("event", target.event);
  const keys = Object.keys(target.params ?? {});
  const rank = (key: string) => {
    const at = CONTEXT_ORDER.indexOf(key);
    return at < 0 ? CONTEXT_ORDER.length : at;
  };
  keys.sort((a, b) => rank(a) - rank(b) || (a < b ? -1 : a > b ? 1 : 0));
  for (const key of keys) {
    if (key === "event" || key === "section")
      throw new TypeError(`"${key}" is a field of the target, not a param`);
    add(key, target.params?.[key]);
  }
  add("section", target.section);
  const query = new URLSearchParams(pairs).toString();
  return (
    routes.workspace(workspaceId, target.view || undefined) +
    (query ? `?${query}` : "")
  );
}

export const routes = {
  home: "/",
  workspace: (workspaceId: string, view?: string) =>
    view
      ? `/w/${enc(workspaceId)}/${enc(view)}`
      : `/w/${enc(workspaceId)}/overview`,
  target: workspaceTarget,
  person: (personId: string) => `/person/${enc(personId)}`,
  publicEvent: (eventId: string) => `/event/${enc(eventId)}`,
  apiExplorer: "/api-explorer",
} as const;

/**
 * The target a workspace location points at, or null when it is not a workspace location. The
 * inverse of `routes.target` for what it can express: params whose key or value is not safe are
 * left out, so a hand-edited URL never becomes a target carrying typed text.
 */
export function parseWorkspaceLocation(
  pathname: string,
  search: string,
): { workspaceId: string; target: RouteTarget } | null {
  const match = /^\/w\/([^/]+)(?:\/([^/]+))?\/?$/.exec(pathname);
  if (!match) return null;
  let workspaceId: string;
  let view: string;
  try {
    workspaceId = decodeURIComponent(match[1]);
    view = match[2] ? decodeURIComponent(match[2]) : "overview";
  } catch {
    return null;
  }
  const target: RouteTarget = { view };
  const params: Record<string, string> = {};
  for (const [key, value] of new URLSearchParams(search)) {
    if (!SAFE_KEY.test(key) || !SAFE_VALUE.test(value)) continue;
    if (key === "event") target.event = value;
    else if (key === "section") target.section = value;
    else params[key] = value;
  }
  if (Object.keys(params).length) target.params = params;
  return { workspaceId, target };
}

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
