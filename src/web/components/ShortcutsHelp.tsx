import { useId, useLayoutEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router";
import { useMe } from "../hooks/useMe";
import { commandsFor, type CommandContext } from "../lib/commands";
import "../lib/shellCommands";
import { onShellOverlay, openShellOverlay } from "../lib/shellEvents";
import {
  setSingleKeyShortcuts,
  useSingleKeyShortcuts,
} from "../lib/shellPreferences";
import { CHORD_MS, interpret } from "../lib/shortcuts";
import { Modal } from "./Modal";
import { useWorkspaceNavigation } from "./WorkspaceNavigation";

const isMac = () =>
  typeof navigator !== "undefined" &&
  /mac|iphone|ipad/i.test(navigator.platform);

/**
 * The keyboard of the shell: "?" shows this help, "/" opens the palette and "G then a letter" goes to
 * a place. They are single-key shortcuts, so the help has the switch that turns them off (WCAG
 * 2.1.4); Ctrl+K and Cmd+K stay. The list is read from the command registry, so a command that
 * declares a shortcut appears here without anyone editing this file.
 */
export function ShellShortcuts() {
  const navigation = useWorkspaceNavigation();
  const navigate = useNavigate();
  const user = useMe().data?.public_id ?? "";
  const enabled = useSingleKeyShortcuts(user);
  const [open, setOpen] = useState(false);
  const chord = useRef<ReturnType<typeof setTimeout> | null>(null);
  const places = navigation?.destinations;
  const href = navigation?.href;

  useLayoutEffect(() => onShellOverlay("shortcuts", () => setOpen(true)), []);

  // The listener reads the latest places and navigation through a ref, so it is subscribed once per
  // on or off and a re-render (data arriving, the URL changing) can never drop a chord half typed.
  const latest = useRef({ places, href, navigate });
  latest.current = { places, href, navigate };
  useLayoutEffect(() => {
    if (!enabled) return;
    const stop = () => {
      if (chord.current) clearTimeout(chord.current);
      chord.current = null;
    };
    const listen = (event: KeyboardEvent) => {
      if (event.defaultPrevented) return;
      const { action, pending } = interpret(
        {
          key: event.key,
          ctrlKey: event.ctrlKey,
          metaKey: event.metaKey,
          altKey: event.altKey,
          target: event.target as Element | null,
          dialogOpen: !!document.querySelector(
            '[role="dialog"][aria-modal="true"]',
          ),
        },
        chord.current !== null,
      );
      stop();
      if (pending) chord.current = setTimeout(stop, CHORD_MS);
      if (action.type === "help") {
        event.preventDefault();
        setOpen(true);
      } else if (action.type === "palette") {
        event.preventDefault();
        openShellOverlay("palette");
      } else if (action.type === "go") {
        const { places, href, navigate } = latest.current;
        const place = places?.find((item) => item.key === action.letter);
        if (place && href) {
          event.preventDefault();
          navigate(href(place.id));
          requestAnimationFrame(() =>
            document.getElementById("main-content")?.focus(),
          );
        }
      }
    };
    document.addEventListener("keydown", listen);
    return () => {
      document.removeEventListener("keydown", listen);
      stop();
    };
  }, [enabled]);

  if (!navigation || !open) return null;
  return (
    <ShortcutsDialog
      user={user}
      enabled={enabled}
      onClose={() => setOpen(false)}
    />
  );
}

function ShortcutsDialog({
  user,
  enabled,
  onClose,
}: {
  user: string;
  enabled: boolean;
  onClose: () => void;
}) {
  const navigation = useWorkspaceNavigation()!;
  const location = useLocation();
  const titleId = useId();
  const requested = new URLSearchParams(location.search).get("event") ?? "";
  const context: CommandContext = useMemo(
    () => ({
      role: navigation.role,
      workspaceId: navigation.workspaceId,
      eventId: requested,
      view: navigation.view,
      selection: null,
      places: navigation.destinations.map((place) => ({
        id: place.id,
        label: place.label,
        to: navigation.href(place.id),
        key: place.key,
      })),
      events: [],
      go: () => {},
      target: navigation.target,
      roles: [],
      pinned: [],
      recentViews: [],
      capabilities: { openShortcuts: () => {} },
    }),
    [navigation, requested],
  );
  const listed = commandsFor(context).filter((command) => command.shortcut);
  const groups = [...new Set(listed.map((command) => command.group))];
  const mod = isMac() ? "⌘K" : "Ctrl K";
  return (
    <Modal titleId={titleId} onClose={onClose}>
      <h2 id={titleId}>Keyboard shortcuts</h2>
      <section aria-label="Anywhere">
        <h3>Anywhere</h3>
        <dl className="cx-shortcuts">
          <div>
            <dt>
              <kbd>{mod}</kbd>
            </dt>
            <dd>Search or run a command</dd>
          </div>
          {enabled && (
            <div>
              <dt>
                <kbd>/</kbd>
              </dt>
              <dd>Search or run a command</dd>
            </div>
          )}
          <div>
            <dt>
              <kbd>Esc</kbd>
            </dt>
            <dd>Close a menu or dialog</dd>
          </div>
        </dl>
      </section>
      {enabled &&
        groups.map((group) => (
          <section key={group} aria-label={group}>
            <h3>{group}</h3>
            <dl className="cx-shortcuts">
              {listed
                .filter((command) => command.group === group)
                .map((command) => (
                  <div key={command.id}>
                    <dt>
                      <kbd>{command.shortcut}</kbd>
                    </dt>
                    <dd>{command.label}</dd>
                  </div>
                ))}
            </dl>
          </section>
        ))}
      <label className="cx-shortcuts__switch">
        <input
          type="checkbox"
          checked={enabled}
          onChange={(event) =>
            setSingleKeyShortcuts(user, event.target.checked)
          }
        />{" "}
        Use single-key shortcuts (?, /, and G then a letter)
      </label>
      {!enabled && (
        <p role="status" className="cx-search__status">
          Single-key shortcuts are off. {mod} still opens the palette.
        </p>
      )}
      <div className="cx-consequence__actions">
        <button
          type="button"
          className="cx-button cx-button--secondary"
          onClick={onClose}
        >
          Close
        </button>
      </div>
    </Modal>
  );
}
