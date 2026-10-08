import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  barDestinations,
  DestinationLink,
  roleDestinations,
  useWorkspaceNavigation,
} from "./WorkspaceNavigation";
import { Link } from "react-router";
import { roleLabel } from "../lib/roles";
import { useAppDensity } from "../hooks/useAppDensity";
import { useAppTheme } from "../hooks/useAppTheme";
import { useMe } from "../hooks/useMe";
import {
  setDensityPreference,
  setThemePreference,
  useDensityPreference,
  useThemePreference,
  type Density,
  type Theme,
} from "../lib/shellPreferences";
import { EventSwitcher } from "./EventSwitcher";
import { InboxCenter } from "./InboxCenter";
import { CommandPaletteButton } from "./CommandPalette";
import { ShellShortcuts } from "./ShortcutsHelp";
import { onShellOverlay, openShellOverlay } from "../lib/shellEvents";
import { PreviewAsDialog } from "./PreviewAsDialog";
import { ShellNotice } from "./ShellNotice";
import { WorkspaceTabs } from "./WorkspaceTabs";
import { useDraftGuard } from "./DraftGuard";
import { OperationsHost } from "./OperationsPane";
import { WIDE_DISPLAY_PX } from "../hooks/useWideDisplay";
import { setOpsPane, useOpsPane, type OpsPane } from "../lib/shellPreferences";
import { SkipLink } from "./SkipLink";
import { Icon, type IconName } from "./Icon";

const MAIN_ID = "main-content";

/**
 * The signed-in person's theme on the app's own screens. It exists only in the workspace shell: the
 * public event site and the server-rendered public pages follow the organizer's theme and are never
 * overridden by the viewer's choice (design: dark-mode, Authority).
 */
function ThemeApplier() {
  const user = useMe().data?.public_id ?? "";
  useAppTheme(user);
  useAppDensity(user);
  return null;
}

const DENSITY_CHOICES: [Density, string][] = [
  ["comfortable", "Comfortable"],
  ["compact", "Compact"],
  ["high", "High density"],
];

/**
 * Which of their own roles the person is viewing the workspace as, shown only when they hold more
 * than one. Each choice is a link to that role's overview (a history entry); it picks a screen,
 * the server still authorizes every request against what the person really holds.
 */
function RoleChoice() {
  const navigation = useWorkspaceNavigation();
  if (!navigation || navigation.roles.length < 2) return null;
  return (
    <nav aria-label="Roles" className="cx-account__roles">
      <p className="cx-account__legend">Viewing as</p>
      {navigation.roles.map((held) => (
        <Link
          key={held}
          className="cx-account__link"
          aria-current={held === navigation.role ? "true" : undefined}
          to={navigation.target({ view: "overview", params: { as: held } })}
        >
          {roleLabel(held)}
        </Link>
      ))}
    </nav>
  );
}

/**
 * Preview as a participant, a judge or the public (organizers and admins): server-evaluated, read
 * only, never an impersonation. The dialog is opened by the account menu or a command.
 */
function PreviewAsHost() {
  const [role, setRole] = useState<string | null>(null);
  useEffect(
    () => onShellOverlay("preview", (arg) => setRole(arg || "participant")),
    [],
  );
  return role ? (
    <PreviewAsDialog initialRole={role} onClose={() => setRole(null)} />
  ) : null;
}

function PreviewAsMenu() {
  const navigation = useWorkspaceNavigation();
  if (
    !navigation ||
    (navigation.role !== "organizer" && navigation.role !== "admin")
  )
    return null;
  return (
    <div className="cx-account__roles">
      <p className="cx-account__legend">Preview as</p>
      {["participant", "judge", "public"].map((value) => (
        <button
          key={value}
          type="button"
          className="cx-account__link cx-account__shortcuts"
          onClick={() => openShellOverlay("preview", value)}
        >
          {roleLabel(value)}
        </button>
      ))}
    </div>
  );
}

function DensityChoice() {
  const user = useMe().data?.public_id ?? "";
  const preference = useDensityPreference(user);
  return (
    <fieldset className="cx-account__theme">
      <legend>Table density</legend>
      {DENSITY_CHOICES.map(([value, label]) => (
        <label key={value}>
          <input
            type="radio"
            name="density"
            value={value}
            checked={preference === value}
            onChange={() => setDensityPreference(user, value)}
          />{" "}
          {label}
        </label>
      ))}
    </fieldset>
  );
}

function OperationsChoice() {
  const user = useMe().data?.public_id ?? "";
  const navigation = useWorkspaceNavigation();
  const pane = useOpsPane(user);
  const organizer =
    navigation?.role === "organizer" || navigation?.role === "admin";
  return (
    <fieldset className="cx-account__theme">
      <legend>Operations mode</legend>
      {[
        ["", "Off"],
        [organizer ? "attention" : "inbox", "Second pane beside the page"],
      ].map(([value, text]) => (
        <label key={text}>
          <input
            type="radio"
            name="operations-mode"
            value={value}
            checked={value === "" ? pane === "" : pane !== ""}
            onChange={() => setOpsPane(user, value as OpsPane | "")}
          />{" "}
          {text}
        </label>
      ))}
      <p className="cx-metadata">
        Needs a display {WIDE_DISPLAY_PX}px wide or more; it watches what needs
        attention, your recent actions or your inbox.
      </p>
    </fieldset>
  );
}

function ThemeChoice() {
  const user = useMe().data?.public_id ?? "";
  const preference = useThemePreference(user);
  return (
    <fieldset className="cx-account__theme">
      <legend>Theme</legend>
      {(
        [
          ["system", "System"],
          ["light", "Light"],
          ["dark", "Dark"],
        ] as [Theme, string][]
      ).map(([value, label]) => (
        <label key={value}>
          <input
            type="radio"
            name="theme"
            value={value}
            checked={preference === value}
            onChange={() => setThemePreference(user, value)}
          />{" "}
          {label}
        </label>
      ))}
    </fieldset>
  );
}

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
  const guard = useDraftGuard(onSignOut);
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
      {destinations && <ThemeApplier />}
      {destinations && <ShellShortcuts />}
      {destinations && <PreviewAsHost />}
      {destinations && <ShellNotice />}
      {guard.dialog}
      <SkipLink targetId={MAIN_ID} />
      <header className="cx-shell__header">
        <Brand className="cx-shell__brand">
          <span className="cx-brand-mark" aria-hidden="true">
            C
          </span>
          <span className="cx-brand-name">{brand}</span>
        </Brand>
        {destinations && (
          <>
            <span className="cx-shell__context">
              {workspaceName
                ? `${workspaceName} · ${
                    (navigation?.roles.length ?? 0) > 1 ? "viewing as " : ""
                  }${role === "admin" ? "organizer" : role}`
                : `${role === "admin" ? "Organizer" : role} workspace`}
            </span>
            <EventSwitcher />
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
          <CommandPaletteButton onSignOut={guard.requestSignOut} />
        )}
        {destinations && <InboxCenter />}
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
                <>
                  <DestinationLink id="profile" className="cx-account__link">
                    View profile
                  </DestinationLink>
                  <DestinationLink
                    id="profile"
                    hash="notification-preferences"
                    className="cx-account__link"
                  >
                    Notification preferences
                  </DestinationLink>
                </>
              )}
              <RoleChoice />
              <PreviewAsMenu />
              <ThemeChoice />
              <DensityChoice />
              <OperationsChoice />
              <button
                type="button"
                className="cx-account__link cx-account__shortcuts"
                onClick={() => openShellOverlay("shortcuts")}
              >
                Keyboard shortcuts
              </button>
              <p className="cx-metadata">{role} access</p>
              {onSignOut && (
                <button
                  type="button"
                  className="cx-button cx-button--secondary"
                  onClick={guard.requestSignOut}
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

      {destinations && <WorkspaceTabs />}
      <main id={MAIN_ID} className="cx-shell__main" tabIndex={-1}>
        {children}
      </main>
      {destinations && <OperationsHost />}
    </div>
  );
}
