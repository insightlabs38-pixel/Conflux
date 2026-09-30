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

type Navigation = {
  view: string;
  navigate: (id: string) => void;
  href: (id: string) => string;
};
const Context = createContext<Navigation | null>(null);
/**
 * The current destination is the `:view` segment of `/w/:workspaceId/:view` (lib/routes.ts), so the
 * browser owns history, deep links and refresh; this provider only validates it against the role.
 * A view the role does not have resolves to the overview (the workspace route also redirects the
 * URL). Links keep the current search (`?event=`, `?invite=`) so a selected event survives.
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
  const view = destinations.some((item) => item.id === requested)
    ? requested
    : "overview";
  const href = useCallback(
    (id: string) => routes.workspace(workspaceId, id) + search,
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
  return <Context value={{ view, navigate, href }}>{children}</Context>;
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
