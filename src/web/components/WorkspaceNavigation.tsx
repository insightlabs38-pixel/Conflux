import {
  createContext,
  useContext,
  useEffect,
  useState,
  type MouseEvent,
  type ReactNode,
} from "react";

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
function locationView() {
  return typeof window === "undefined"
    ? "overview"
    : new URLSearchParams(window.location.search).get("view") || "overview";
}
export function WorkspaceNavigationProvider({
  role,
  children,
}: {
  role: string;
  children: ReactNode;
}) {
  const [requested, setRequested] = useState(locationView);
  const destinations = roleDestinations[role] || [];
  const view = destinations.some((item) => item.id === requested)
    ? requested
    : "overview";
  useEffect(() => {
    const sync = () => setRequested(locationView());
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);
  function href(id: string) {
    if (typeof window === "undefined") return `?view=${id}`;
    const url = new URL(window.location.href);
    url.searchParams.set("view", id);
    return url.pathname + url.search;
  }
  function navigate(id: string) {
    if (!destinations.some((item) => item.id === id)) return;
    window.history.pushState({}, "", href(id));
    setRequested(id);
    requestAnimationFrame(() =>
      document.getElementById("main-content")?.focus(),
    );
  }
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
  function click(event: MouseEvent<HTMLAnchorElement>) {
    if (
      !navigation ||
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    )
      return;
    event.preventDefault();
    navigation.navigate(id);
  }
  return (
    <a
      href={navigation?.href(id) || `?view=${id}`}
      onClick={click}
      className={className}
      aria-current={navigation?.view === id ? "page" : undefined}
    >
      {children}
    </a>
  );
}

export function WorkspaceViewTitle({ role }: { role: string }) {
  const navigation = useWorkspaceNavigation();
  const title = roleDestinations[role]?.find(
    (item) => item.id === (navigation?.view || "overview"),
  )?.label;
  return title ? <h2 className="cx-view-title">{title}</h2> : null;
}
