import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  barDestinations,
  DestinationLink,
  roleDestinations,
  useWorkspaceNavigation,
} from "./WorkspaceNavigation";
import { SkipLink } from "./SkipLink";
import { Icon, type IconName } from "./Icon";

const MAIN_ID = "main-content";

/** A rail icon helps find a place, so only the stable destinations have one. */
const DESTINATION_ICON: Record<string, IconName> = {
  overview: "home",
  setup: "sliders",
  participants: "users",
  eligibility: "file-text",
  judging: "list-checks",
  results: "trophy",
  communications: "message-square",
  onsite: "map-pin",
  integrations: "plug",
  operations: "shield",
  profile: "user",
  team: "users",
  project: "file-text",
  resources: "file-text",
  messages: "message-square",
  queue: "list-checks",
  schedule: "calendar",
};

/** Shared page chrome: skip link, header/nav landmark, main landmark. */
export function AppShell({
  nav,
  children,
  brand = "Conflux",
  brandAs: Brand = "h1",
  role,
  username,
  workspaceName,
  onSignOut,
  signingOut,
}: {
  nav?: ReactNode;
  children: ReactNode;
  brand?: string;
  role?: string;
  username?: string;
  workspaceName?: string;
  onSignOut?: () => void;
  signingOut?: boolean;
  /** The page's h1 lives wherever the page's actual title is; pass "p" here
   * when the shell wraps a page that renders its own h1 (e.g. an event name). */
  brandAs?: "h1" | "p";
}) {
  const [navOpen, setNavOpen] = useState(false);
  // The control that opened the navigation (the header toggle on a tablet, "More" on a phone) gets
  // focus back when it closes.
  const opener = useRef<HTMLButtonElement | null>(null);
  const toggle = useRef<HTMLButtonElement>(null);
  // Optional modules that are off are not offered (see WorkspaceNavigationProvider).
  const navigation = useWorkspaceNavigation();
  const destinations = role
    ? (navigation?.destinations ?? roleDestinations[role])
    : undefined;
  const { bar, more } = barDestinations(destinations ?? []);
  const inBar = new Set(more ? bar.map((item) => item.id) : []);
  const sheet = useRef<HTMLElement>(null);
  useEffect(() => {
    // On a phone the opened list is a sheet: put the reader inside it.
    if (navOpen && opener.current?.dataset.phone === "true")
      [...(sheet.current?.querySelectorAll<HTMLElement>("nav a") ?? [])]
        .find((link) => link.checkVisibility())
        ?.focus({ preventScroll: true });
  }, [navOpen]);
  const closeNavigation = () => {
    setNavOpen(false);
    opener.current?.focus();
  };
  return (
    <div className={`cx-shell ${destinations ? "cx-shell--workspace" : ""}`}>
      <SkipLink targetId={MAIN_ID} />
      <header className="cx-shell__header">
        <Brand className="cx-shell__brand">
          <span className="cx-brand-mark" aria-hidden="true">
            C
          </span>
          {brand}
        </Brand>
        {destinations && (
          <>
            <span className="cx-shell__context">
              {workspaceName
                ? `${workspaceName} · ${role === "admin" ? "organizer" : role}`
                : `${role === "admin" ? "Organizer" : role} workspace`}
            </span>
            <button
              ref={toggle}
              type="button"
              className="cx-nav-toggle cx-button cx-button--secondary"
              aria-expanded={navOpen}
              aria-controls="workspace-navigation"
              onClick={() => {
                opener.current = toggle.current;
                setNavOpen((open) => !open);
              }}
            >
              Navigation
            </button>
          </>
        )}
        {nav && (
          <nav
            className="cx-shell__nav"
            aria-label={destinations ? "Workspace actions" : "Primary"}
          >
            {nav}
          </nav>
        )}
        {destinations && (
          <details
            className="cx-account"
            onClick={(event) => {
              if ((event.target as HTMLElement).closest("a"))
                event.currentTarget.open = false;
            }}
            onKeyDown={(event) => {
              if (event.key === "Escape") {
                event.currentTarget.open = false;
                event.currentTarget.querySelector("summary")?.focus();
              }
            }}
          >
            <summary aria-label={`Account for ${username || "current user"}`}>
              <span>{username || "My account"}</span>
              <Icon name="chevron-down" />
            </summary>
            <div className="cx-account__panel">
              {destinations.some((item) => item.id === "profile") && (
                <DestinationLink id="profile" className="cx-account__link">
                  View profile
                </DestinationLink>
              )}
              <p className="cx-metadata">{role} access</p>
              {onSignOut && (
                <button
                  type="button"
                  className="cx-button cx-button--secondary"
                  onClick={onSignOut}
                  disabled={signingOut}
                >
                  {signingOut ? "Signing out…" : "Sign out"}
                </button>
              )}
            </div>
          </details>
        )}
      </header>
      {destinations && (
        <aside
          id="workspace-navigation"
          ref={sheet}
          className={`cx-sidebar ${navOpen ? "cx-sidebar--open" : ""}`}
          onKeyDown={(event) => {
            if (event.key === "Escape") closeNavigation();
          }}
        >
          <div className="cx-sidebar__sheet-head">
            <p className="cx-sidebar__sheet-title">All sections</p>
            <button
              type="button"
              className="cx-sidebar__sheet-close"
              onClick={closeNavigation}
              aria-label="Close navigation"
            >
              <Icon name="x" />
            </button>
          </div>
          <nav
            aria-label="Primary"
            onClick={(event) => {
              if ((event.target as HTMLElement).closest("a")) setNavOpen(false);
            }}
          >
            {destinations.map((item) => (
              <div
                key={item.id}
                className={
                  inBar.has(item.id) ? "cx-sidebar__in-bar" : undefined
                }
              >
                {item.group && (
                  <p className="cx-sidebar__group">{item.group}</p>
                )}
                <DestinationLink
                  id={item.id}
                  className="cx-sidebar__link"
                  title={item.label}
                >
                  {DESTINATION_ICON[item.id] && (
                    <Icon name={DESTINATION_ICON[item.id]} />
                  )}
                  <span className="cx-sidebar__label">{item.label}</span>
                </DestinationLink>
              </div>
            ))}
          </nav>
        </aside>
      )}
      {destinations && navOpen && (
        <button
          type="button"
          className="cx-sheet-scrim"
          tabIndex={-1}
          aria-label="Close navigation"
          onClick={closeNavigation}
        />
      )}
      {destinations && (
        <nav className="cx-bottom-nav" aria-label="Quick navigation">
          {bar.map((item) => (
            <DestinationLink
              key={item.id}
              id={item.id}
              className="cx-bottom-nav__item"
            >
              {DESTINATION_ICON[item.id] && (
                <Icon name={DESTINATION_ICON[item.id]} size={20} />
              )}
              <span>{item.short ?? item.label}</span>
            </DestinationLink>
          ))}
          {more && (
            <button
              type="button"
              className="cx-bottom-nav__item"
              data-phone="true"
              aria-expanded={navOpen}
              aria-controls="workspace-navigation"
              onClick={(event) => {
                opener.current = event.currentTarget;
                setNavOpen((open) => !open);
              }}
            >
              <Icon name="menu" size={20} />
              <span>More</span>
            </button>
          )}
        </nav>
      )}

      <main id={MAIN_ID} className="cx-shell__main" tabIndex={-1}>
        {children}
      </main>
    </div>
  );
}
