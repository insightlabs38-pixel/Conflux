import { appBasename, parseWorkspaceLocation, routes } from "./routes";

/** The keys the app itself writes: context (`as`, `stage`, `plan`, `event`) and the panel entries. Anything else, such as typed text, is left out. */
const SHAREABLE_KEY =
  /^(as|stage|plan|event|(sort|page|size|row|view|f)_[a-z0-9_]+)$/;

/**
 * The address that reopens exactly what a person is looking at: the workspace view, its section,
 * the event, the role, the saved view, the sort, the page and the open record, all of which are ids
 * or fixed names (lib/urlState.ts). Typed text never reaches a URL, so it is not in the link.
 * Rebuilt from the parsed location rather than copied, so anything unsafe or unknown is dropped, and
 * the single-use `invite` entry token is always left out (a shared link must not carry a credential).
 * Returns null away from a workspace view (a public page has its own address).
 */
export function shareableHref(
  pathname: string,
  search: string,
  origin: string,
): string | null {
  const target = shareableTarget(pathname, search);
  return target === null ? null : origin + appBasename(pathname) + target;
}

/** The same address without the origin and base path: what the router and the tabs navigate to. */
export function shareableTarget(
  pathname: string,
  search: string,
): string | null {
  const base = appBasename(pathname);
  const inner = pathname.startsWith(base)
    ? pathname.slice(base.length)
    : pathname;
  const parsed = parseWorkspaceLocation(inner || "/", search);
  if (!parsed) return null;
  const params: Record<string, string> = {};
  for (const [key, value] of Object.entries(parsed.target.params ?? {})) {
    if (SHAREABLE_KEY.test(key)) params[key] = value;
  }
  return routes.target(parsed.workspaceId, { ...parsed.target, params });
}

/** A place is its view and event: the same two make the same tab, wherever inside it a person is. */
export function placeOf(to: string): { view: string; event: string } | null {
  const url = new URL(to, "http://x");
  const view = url.pathname.split("/")[3];
  return view ? { view, event: url.searchParams.get("event") ?? "" } : null;
}

export function placeKey(to: string): string {
  const place = placeOf(to);
  return place ? `${place.view}|${place.event}` : to;
}
