import { useCallback, useContext, useRef } from "react";
import {
  UNSAFE_NavigationContext,
  useLocation,
  useNavigate,
} from "react-router";

/**
 * URL-state conventions (PD-B04-T04). The rule is: the URL holds *where you are and what you are
 * looking at*, never *what you are typing*.
 *
 * | Kind        | Lives in                     | Examples                                    | History |
 * | ----------- | ---------------------------- | ------------------------------------------- | ------- |
 * | Location    | path (lib/routes.ts)         | workspace, view, person, public event       | push    |
 * | Context     | search, carried across views | `event`, `stage`, `plan`                    | push    |
 * | Panel state | search, dropped on view exit | selected row, enumerated filter/sort, tab, page | replace |
 * | Entry token | search, read once            | `invite`                                    | -       |
 * | Local only  | component state / storage    | drafts, form fields, scores, comments, free-text search, open menus | - |
 *
 * Rules
 * - A param is only ever a public id or a value from a fixed set. Free text, personal data and
 *   credentials never go in a URL (they end up in history, logs, referrers and shared links). The
 *   one exception is the single-use `invite` entry token, which is read once and removed on use.
 * - Defaults are omitted, so a clean URL means the default view; an unknown or no-longer-visible
 *   value falls back to the default and the URL is corrected with `replace` (no phantom entry).
 * - Selecting a *context* changes what the page is about, so it pushes (Back returns to the
 *   previous context) and clears the params that depend on it. Selecting inside a panel replaces:
 *   Back leaves the view instead of stepping through forty selections.
 * - The URL is never authority. Ids in it are requests; the server still authorizes and a value
 *   that does not resolve to something the user can see is treated as absent, not as another one.
 * - Panels that stay mounted while hidden (`Destination`) must keep drafts in component state; only
 *   the *selection* mirrors to the URL, so leaving a view cannot discard unsaved work.
 */
export const CONTEXT_PARAMS = ["event", "stage", "plan"] as const;

/** Params that follow the user when they move between the views of one workspace. */
const CARRIED = new Set<string>([...CONTEXT_PARAMS, "invite"]);

/** The search string for a link to another view of the same workspace: context params only. */
export function carriedSearch(search: string): string {
  const source = new URLSearchParams(search);
  const kept = new URLSearchParams();
  for (const [key, value] of source)
    if (CARRIED.has(key)) kept.append(key, value);
  const text = kept.toString();
  return text ? `?${text}` : "";
}

type Options = {
  /** Params that depend on this one and are removed when it changes. */
  clears?: string[];
};
type Change = { replace?: boolean };

/**
 * One string search param as state: `[value, set]`. `""` means absent; setting `""` removes it.
 * `set(value, { replace: true })` corrects the URL without adding a history entry.
 */
export function useUrlParam(
  key: string,
  { clears = [] }: Options = {},
): [string, (value: string, change?: Change) => void] {
  const location = useLocation();
  const navigate = useNavigate();
  const navigation = useContext(UNSAFE_NavigationContext);
  // The router renders a navigation *later* (in a transition), so `location` can lag behind the URL
  // the user has just navigated to. A setter must build on the URL as it is now; the history object
  // is the one synchronous source. Corrections should still come from effects on rendered state
  // (see the rules above), this is the safety net that keeps a late one from undoing a navigation.
  const latest = useRef(location);
  latest.current = location;
  const current = useCallback(() => {
    const now = (
      navigation.navigator as {
        location?: { pathname: string; search: string };
      }
    ).location;
    if (!now) return latest.current;
    const base = navigation.basename === "/" ? "" : navigation.basename;
    const pathname =
      base && now.pathname.startsWith(base)
        ? now.pathname.slice(base.length) || "/"
        : now.pathname;
    return { pathname, search: now.search };
  }, [navigation]);
  const value = new URLSearchParams(location.search).get(key) ?? "";
  const dependents = clears.join("\u0000");
  const set = useCallback(
    (next: string, { replace = false }: Change = {}) => {
      const { pathname, search } = current();
      const params = new URLSearchParams(search);
      if ((params.get(key) ?? "") === next) return;
      if (next) params.set(key, next);
      else params.delete(key);
      for (const dependent of dependents ? dependents.split("\u0000") : [])
        params.delete(dependent);
      const text = params.toString();
      void navigate({ pathname, search: text ? `?${text}` : "" }, { replace });
    },
    [key, dependents, navigate, current],
  );
  return [value, set];
}
