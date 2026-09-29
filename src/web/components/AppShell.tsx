import { useRef, useState, type ReactNode } from "react";
import { DestinationLink, roleDestinations } from "./WorkspaceNavigation";
import { SkipLink } from "./SkipLink";

const MAIN_ID = "main-content";

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
  const toggle = useRef<HTMLButtonElement>(null);
  const destinations = role ? roleDestinations[role] : undefined;
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
              onClick={() => setNavOpen((open) => !open)}
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
          className={`cx-sidebar ${navOpen ? "cx-sidebar--open" : ""}`}
          onKeyDown={(event) => {
            if (event.key === "Escape") {
              setNavOpen(false);
              toggle.current?.focus();
            }
          }}
        >
          <nav
            aria-label="Primary"
            onClick={(event) => {
              if ((event.target as HTMLElement).closest("a")) setNavOpen(false);
            }}
          >
            <p className="cx-eyebrow">Your workspace</p>
            {destinations.map((item) => (
              <div key={item.id}>
                {item.group && (
                  <p className="cx-sidebar__group">{item.group}</p>
                )}
                <DestinationLink id={item.id} className="cx-sidebar__link">
                  {item.label}
                </DestinationLink>
              </div>
            ))}
          </nav>
          <p className="cx-sidebar__footer">Conflux · build with confidence</p>
        </aside>
      )}

      <main id={MAIN_ID} className="cx-shell__main" tabIndex={-1}>
        {children}
      </main>
    </div>
  );
}
