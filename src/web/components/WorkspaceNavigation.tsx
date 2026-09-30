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

export const roleDestinations: Record<
  string,
  { id: string; label: string; group?: string }[]
> = {
  participant: [
    { id: "overview", label: "Overview" },
    { id: "team", label: "Team" },
    { id: "project", label: "Project & submission" },
    { id: "resources", label: "Event resources" },
    { id: "messages", label: "Messages" },
    { id: "profile", label: "Profile & history" },
  ],
  judge: [
    { id: "overview", label: "Overview" },
    { id: "queue", label: "Review queue" },
    { id: "schedule", label: "Schedule & route" },
    { id: "profile", label: "Judge profile" },
    { id: "messages", label: "Messages" },
  ],
  organizer: [
    { id: "overview", label: "Overview" },
    { id: "setup", label: "Event setup", group: "Manage event" },
    { id: "participants", label: "Participants & teams" },
    { id: "eligibility", label: "Projects & eligibility" },
    { id: "judging", label: "Judging" },
    { id: "results", label: "Results & publication" },
    { id: "communications", label: "Communications" },
    { id: "onsite", label: "On-site" },
    { id: "integrations", label: "Integrations", group: "Advanced" },
    { id: "operations", label: "Operations & audit" },
    { id: "profile", label: "Profile", group: "Account" },
  ],
  mentor: [
    { id: "overview", label: "Mentor desk" },
    { id: "profile", label: "Profile" },
    { id: "messages", label: "Messages" },
  ],
  volunteer: [
    { id: "overview", label: "Check-in desk" },
    { id: "profile", label: "Profile" },
    { id: "messages", label: "Messages" },
  ],
};
roleDestinations.admin = roleDestinations.organizer;

/**
 * The destinations without the hidden ones. A group heading belongs to the run of items after it,
 * so when its first item is hidden the heading moves to the next shown item of that group.
 */
function visibleDestinations(
  destinations: { id: string; label: string; group?: string }[],
  hidden: Set<string | null>,
) {
  let current: string | undefined;
  let shown: string | undefined;
  const out: { id: string; label: string; group?: string }[] = [];
  for (const item of destinations) {
    if (item.group) current = item.group;
    if (hidden.has(item.id)) continue;
    out.push({
      id: item.id,
      label: item.label,
      ...(current !== shown ? { group: current } : {}),
    });
    shown = current;
  }
  return out;
}

type Navigation = {
  view: string;
  navigate: (id: string) => void;
  href: (id: string) => string;
  /** The role's destinations minus optional modules that are neither enabled nor in use. */
  destinations: { id: string; label: string; group?: string }[];
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
    (id: string) => routes.workspace(workspaceId, id) + carriedSearch(search),
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
    <Context value={{ view, navigate, href, destinations: visible, modules }}>
      {children}
    </Context>
  );
}
export function useWorkspaceNavigation() {
  return useContext(Context);
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
  children,
  className = "cx-task-link",
}: {
  id: string;
  children: ReactNode;
  className?: string;
}) {
  const navigation = useWorkspaceNavigation();
  // A real router link: plain clicks navigate in-app, modified clicks (new tab/window) fall through
  // to the browser, and the href is the canonical deep link.
  return (
    <Link
      to={navigation?.href(id) || routes.home}
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
