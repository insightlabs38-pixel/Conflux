import { useModules, type Modules } from "../hooks/useModules";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router";
import { routes } from "../lib/routes";
import { carriedSearch } from "../lib/urlState";

export type Destination = {
  id: string;
  label: string;
  group?: string;
  /** The word under the icon in the phone's bottom bar. */
  short?: string;
  /** Kept in the bottom bar when the role has more than five places (the rest go to "More"). */
  bar?: boolean;
  /** The letter after G that goes here ("G then J"); unique within the role. */
  key?: string;
};

export const roleDestinations: Record<string, Destination[]> = {
  participant: [
    { id: "overview", label: "Overview", key: "o", bar: true },
    { id: "team", label: "Team", key: "t", bar: true },
    {
      id: "project",
      label: "Project & submission",
      key: "p",
      short: "Project",
      bar: true,
    },
    { id: "resources", label: "Event resources", key: "r", short: "Resources" },
    { id: "messages", label: "Messages", key: "m", bar: true },
    { id: "profile", label: "Profile & history", key: "f" },
  ],
  judge: [
    { id: "overview", label: "Overview", key: "o" },
    { id: "queue", label: "Review queue", key: "q", short: "Queue" },
    { id: "schedule", label: "Schedule & route", key: "s", short: "Schedule" },
    { id: "profile", label: "Judge profile", key: "f", short: "Profile" },
    { id: "messages", label: "Messages", key: "m" },
  ],
  organizer: [
    { id: "overview", label: "Overview", key: "o", bar: true },
    { id: "setup", label: "Event setup", key: "s", group: "Manage event" },
    {
      id: "participants",
      label: "Participants & teams",
      key: "p",
      short: "People",
      bar: true,
    },
    {
      id: "eligibility",
      label: "Projects & eligibility",
      key: "e",
      short: "Projects",
    },
    { id: "judging", label: "Judging", key: "j", bar: true },
    { id: "results", label: "Results & publication", key: "r" },
    { id: "communications", label: "Communications", key: "c" },
    { id: "onsite", label: "On-site", key: "n", bar: true },
    { id: "integrations", label: "Integrations", key: "i", group: "Advanced" },
    { id: "operations", label: "Operations & audit", key: "a" },
    { id: "profile", label: "Profile", key: "f", group: "Account" },
  ],
  mentor: [
    { id: "overview", label: "Mentor desk", key: "o" },
    { id: "profile", label: "Profile", key: "f" },
    { id: "messages", label: "Messages", key: "m" },
  ],
  volunteer: [
    { id: "overview", label: "Check-in desk", key: "o" },
    { id: "profile", label: "Profile", key: "f" },
    { id: "messages", label: "Messages", key: "m" },
  ],
};
roleDestinations.admin = roleDestinations.organizer;

/**
 * The destinations without the hidden ones. A group heading belongs to the run of items after it,
 * so when its first item is hidden the heading moves to the next shown item of that group.
 */
function visibleDestinations(
  destinations: Destination[],
  hidden: Set<string | null>,
) {
  let current: string | undefined;
  let shown: string | undefined;
  const out: Destination[] = [];
  for (const item of destinations) {
    if (item.group) current = item.group;
    if (hidden.has(item.id)) continue;
    out.push({
      ...item,
      group: undefined,
      ...(current !== shown ? { group: current } : {}),
    });
    shown = current;
  }
  return out;
}

/**
 * What the phone's bottom bar shows: every place when there are at most five, otherwise the places
 * the role keeps in the bar plus a "More" control for the rest (at most four, so five controls).
 */
export function barDestinations(destinations: Destination[]): {
  bar: Destination[];
  more: boolean;
} {
  if (destinations.length <= 5) return { bar: destinations, more: false };
  return {
    bar: destinations.filter((item) => item.bar).slice(0, 4),
    more: true,
  };
}

type Navigation = {
  workspaceId: string;
  role: string;
  view: string;
  navigate: (id: string) => void;
  /** Link to a destination; `section` opens one of its tabs (see WorkflowSections `linkable`). */
  href: (id: string, section?: string) => string;
  /** The role's destinations minus optional modules that are neither enabled nor in use. */
  destinations: Destination[];
  /** Optional modules for the selected event (organizer/admin only; null until known). */
  modules: Modules;
};
const Context = createContext<Navigation | null>(null);
/**
 * The current destination is the `:view` segment of `/w/:workspaceId/:view` (lib/routes.ts), so the
 * browser owns history, deep links and refresh; this provider only validates it against the role.
 * A view the role does not have resolves to the overview (the workspace route also redirects the
 * URL). Links carry the context params (`event`, `stage`, `plan`, `invite`: lib/urlState.ts) so the
 * selected event survives; panel state does not follow the user to another view.
 */
export function WorkspaceNavigationProvider({
  role,
  workspaceId = "",
  children,
}: {
  role: string;
  workspaceId?: string;
  children: ReactNode;
}) {
  const { view: requested = "overview" } = useParams();
  const { search } = useLocation();
  const go = useNavigate();
  const destinations = roleDestinations[role] || [];
  // Optional modules follow the selected event (context param `event`, lib/urlState.ts). A view the
  // role has stays a valid place while its module is off: it explains and offers to enable it.
  const modules = useModules(
    workspaceId,
    new URLSearchParams(search).get("event") ?? "",
    role === "organizer" || role === "admin",
  );
  const hidden = new Set(
    (modules.modules ?? [])
      .filter((module) => module.destination && !module.enabled)
      .map((module) => module.destination),
  );
  const visible = visibleDestinations(destinations, hidden);
  const view = destinations.some((item) => item.id === requested)
    ? requested
    : "overview";
  const href = useCallback(
    (id: string, section?: string) => {
      // Context follows the person between views; panel state and typed text do not (urlState.ts).
      const kept = new URLSearchParams(carriedSearch(search));
      const event = kept.get("event") ?? undefined;
      kept.delete("event");
      return routes.target(workspaceId, {
        view: id,
        section,
        event,
        params: Object.fromEntries(kept),
      });
    },
    [workspaceId, search],
  );
  const navigate = useCallback(
    (id: string) => {
      if (!destinations.some((item) => item.id === id)) return;
      go(href(id));
      requestAnimationFrame(() =>
        document.getElementById("main-content")?.focus(),
      );
    },
    [destinations, go, href],
  );
  return (
    <Context
      value={{
        workspaceId,
        role,
        view,
        navigate,
        href,
        destinations: visible,
        modules,
      }}
    >
      {children}
    </Context>
  );
}
export function useWorkspaceNavigation() {
  return useContext(Context);
}
/**
 * Whether an optional module is on for the selected event. Unknown (not loaded, or a role without
 * a module list) counts as on: nothing is hidden on a guess.
 */
export function useModuleEnabled(key: string): boolean {
  const modules = useWorkspaceNavigation()?.modules.modules;
  return modules?.find((module) => module.key === key)?.enabled ?? true;
}
/**
 * The state of an optional module for one event, for panels that must not mount (and so must not
 * load or create anything) until the module is on: "unknown" until the server has answered for
 * that event, never a guess from a list that describes another event or the workspace.
 */
export function useModuleState(
  key: string,
  eventId: string,
): "on" | "off" | "unknown" {
  const modules = useWorkspaceNavigation()?.modules;
  if (!modules?.modules || modules.eventId !== eventId) return "unknown";
  return modules.modules.find((module) => module.key === key)?.enabled
    ? "on"
    : "off";
}
/** Keep a destination mounted to retain form drafts and offline buffers across navigation. */
export function Destination({
  id,
  children,
  lazy = false,
}: {
  lazy?: boolean;
  id: string | string[];
  children: ReactNode;
}) {
  const navigation = useWorkspaceNavigation();
  const visible =
    !navigation ||
    (Array.isArray(id) ? id.includes(navigation.view) : id === navigation.view);
  const eligible = navigation ? visible : !lazy;
  const [activated, setActivated] = useState(!lazy || eligible);
  useEffect(() => {
    if (eligible) setActivated(true);
  }, [eligible]);
  if (lazy && !activated) return null;
  return (
    <div className="cx-destination" hidden={!visible}>
      {children}
    </div>
  );
}
export function DestinationLink({
  id,
  section,
  children,
  className = "cx-task-link",
  title,
  hash,
}: {
  id: string;
  /** A tooltip for a link whose words are hidden (the icon rail). */
  title?: string;
  /** An element id on the destination to scroll to (for a part of a page that is not a tab). */
  hash?: string;
  /** Open this tab of the destination (a `linkable` WorkflowSections id). */
  section?: string;
  children: ReactNode;
  className?: string;
}) {
  const navigation = useWorkspaceNavigation();
  // A real router link: plain clicks navigate in-app, modified clicks (new tab/window) fall through
  // to the browser, and the href is the canonical deep link.
  return (
    <Link
      to={
        (navigation?.href(id, section) || routes.home) +
        (hash ? `#${hash}` : "")
      }
      onClick={(event) => {
        if (
          event.button === 0 &&
          !(event.metaKey || event.ctrlKey || event.shiftKey || event.altKey)
        )
          requestAnimationFrame(() =>
            document.getElementById("main-content")?.focus(),
          );
      }}
      className={className}
      title={title}
      aria-current={navigation?.view === id ? "page" : undefined}
    >
      {children}
    </Link>
  );
}

export function WorkspaceViewTitle({ role }: { role: string }) {
  const navigation = useWorkspaceNavigation();
  const title = roleDestinations[role]?.find(
    (item) => item.id === (navigation?.view || "overview"),
  )?.label;
  return title ? <h2 className="cx-view-title">{title}</h2> : null;
}
