import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import { useLocation, useNavigate } from "react-router";
import { useMe } from "../hooks/useMe";
import { useGlobalSearch, MIN_QUERY } from "../hooks/useGlobalSearch";
import { useShellEvents } from "../hooks/useShellEvents";
import { usePinnedViewList } from "../hooks/usePinnedViewList";
import {
  commandsFor,
  rankCommands,
  type Command,
  type CommandContext,
} from "../lib/commands";
import "../lib/shellCommands";
import { roleLabel } from "../lib/roles";
import { onShellOverlay, openShellOverlay } from "../lib/shellEvents";
import {
  rememberCommand,
  setDensityPreference,
  setThemePreference,
  useRecentCommands,
} from "../lib/shellPreferences";
import { Icon } from "./Icon";
import { Modal } from "./Modal";
import { useWorkspaceNavigation } from "./WorkspaceNavigation";

type Option = {
  id: string;
  group: string;
  label: string;
  detail?: string;
  run: () => void;
};

const isMac = () =>
  typeof navigator !== "undefined" &&
  /mac|iphone|ipad/i.test(navigator.platform);

/**
 * The header's Search and the command palette are one overlay (⌘K or Ctrl+K from anywhere in the
 * workspace): commands from the registry (lib/commands.ts) and the records of the selected event
 * found through the universal query engine (`useGlobalSearch`). Commands only navigate or change
 * presentation; the server still decides what a person may open.
 */
export function CommandPaletteButton({
  onSignOut,
}: {
  onSignOut?: () => void;
}) {
  const [open, setOpen] = useState(false);
  const navigation = useWorkspaceNavigation();
  useEffect(() => onShellOverlay("palette", () => setOpen(true)), []);
  useEffect(() => {
    const toggle = (event: globalThis.KeyboardEvent) => {
      if (
        (event.metaKey || event.ctrlKey) &&
        !event.altKey &&
        event.key.toLowerCase() === "k" &&
        !event.defaultPrevented
      ) {
        event.preventDefault();
        setOpen((current) => !current);
      }
    };
    document.addEventListener("keydown", toggle);
    return () => document.removeEventListener("keydown", toggle);
  }, []);
  if (!navigation) return null;
  const keys = isMac() ? "⌘K" : "Ctrl K";
  return (
    <>
      <button
        type="button"
        className="cx-search-open"
        aria-label="Search or run a command"
        aria-haspopup="dialog"
        title={`Search or run a command (${keys})`}
        onClick={() => setOpen(true)}
      >
        <Icon name="search" size={20} />
        <span className="cx-search-open__word">Search</span>
        <kbd className="cx-search-open__keys">{keys}</kbd>
      </button>
      {open && (
        <CommandPalette onClose={() => setOpen(false)} onSignOut={onSignOut} />
      )}
    </>
  );
}

function CommandPalette({
  onClose,
  onSignOut,
}: {
  onClose: () => void;
  onSignOut?: () => void;
}) {
  const navigation = useWorkspaceNavigation()!;
  const navigate = useNavigate();
  const location = useLocation();
  const user = useMe().data?.public_id ?? "";
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const titleId = useId();
  const listId = useId();
  const input = useRef<HTMLInputElement>(null);
  // the modal puts focus on the dialog first; the box is where a person starts typing
  useEffect(() => input.current?.focus(), []);
  const { workspaceId, role } = navigation;
  const { events } = useShellEvents(workspaceId, role);
  const requested = new URLSearchParams(location.search).get("event") ?? "";
  const eventId = events.some((event) => event.public_id === requested)
    ? requested
    : "";
  const recent = useRecentCommands(user, workspaceId);
  const pinned = usePinnedViewList(workspaceId, eventId, user);
  const search = useGlobalSearch({ workspaceId, eventId, query });
  const text = query.trim();
  const canSearchRecords = role === "organizer" || role === "admin";

  const go = (to: string) => {
    navigate(to);
    requestAnimationFrame(() =>
      document.getElementById("main-content")?.focus(),
    );
  };
  const context: CommandContext = useMemo(
    () => ({
      role,
      workspaceId,
      eventId,
      view: navigation.view,
      places: navigation.destinations.map((place) => ({
        id: place.id,
        label: place.label,
        to: navigation.href(place.id),
        key: place.key,
      })),
      events: events.map((event) => ({
        id: event.public_id,
        name: event.name,
        current: event.public_id === eventId,
      })),
      go,
      target: navigation.target,
      pinned,
      roles: navigation.roles.map((held) => ({
        role: held,
        label: roleLabel(held),
        current: held === role,
      })),
      capabilities: {
        signOut: onSignOut,
        setTheme: (theme) => setThemePreference(user, theme),
        setDensity: (density) => setDensityPreference(user, density),
        openShortcuts: () => openShellOverlay("shortcuts"),
      },
    }),
    // `go` only closes over `navigate`, which is stable
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [role, workspaceId, eventId, navigation, events, onSignOut, user, pinned],
  );

  const options = useMemo(() => {
    const all = commandsFor(context);
    const run = (command: Command) => () => {
      onClose();
      rememberCommand(user, workspaceId, command.id);
      command.run(context);
    };
    const out: Option[] = [];
    if (text === "") {
      // the person's recent commands first, then the rest in registration order
      const byId = new Map(all.map((command) => [command.id, command]));
      for (const id of recent) {
        const command = byId.get(id);
        if (command)
          out.push({
            id: `recent-${command.id}`,
            group: "Recent",
            label: command.label,
            run: run(command),
          });
      }
    }
    const ranked = rankCommands(all, text, recent);
    // keep the ranked order but cluster by group, in the order each group first appears
    const groups = [...new Set(ranked.map((command) => command.group))];
    for (const group of groups)
      for (const command of ranked)
        if (command.group === group)
          out.push({
            id: command.id,
            group,
            label: command.label,
            detail: command.shortcut,
            run: run(command),
          });
    for (const group of search.groups)
      for (const hit of group.hits)
        out.push({
          id: `${group.key}-${hit.id}`,
          group: group.nouns,
          label: hit.label,
          detail: hit.detail,
          run: () => {
            onClose();
            go(
              navigation.target({
                view: hit.view,
                section: hit.section,
                event: eventId,
              }),
            );
          },
        });
    return out;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [context, text, recent, search.groups, user, workspaceId, eventId]);

  const at = Math.min(active, Math.max(0, options.length - 1));
  const keydown = (event: KeyboardEvent) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (options.length)
        setActive(
          (at + (event.key === "ArrowDown" ? 1 : -1) + options.length) %
            options.length,
        );
    } else if (event.key === "Enter") {
      event.preventDefault();
      options[at]?.run();
    }
  };

  const failed = search.groups.filter((group) => group.failed);
  const nothing = text !== "" && !search.pending && options.length === 0;
  let lastGroup = "";
  return (
    <Modal titleId={titleId} onClose={onClose} placement="top">
      <h2 id={titleId} className="cx-visually-hidden">
        Search and commands
      </h2>
      <div className="cx-search">
        <Icon name="search" />
        <input
          ref={input}
          type="search"
          role="combobox"
          aria-label="Search or run a command"
          aria-expanded={options.length > 0}
          aria-controls={listId}
          aria-activedescendant={options.length ? `${listId}-${at}` : undefined}
          autoComplete="off"
          value={query}
          placeholder="Search or run a command"
          onChange={(event) => {
            setQuery(event.target.value);
            setActive(0);
          }}
          onKeyDown={keydown}
        />
      </div>
      <div role="status" className="cx-search__status">
        {text.length === 1 &&
          canSearchRecords &&
          `Type at least ${MIN_QUERY} characters to search records.`}
        {search.pending && "Searching…"}
        {nothing && `No results for “${text}”.`}
        {!search.pending &&
          text.length >= MIN_QUERY &&
          !eventId &&
          canSearchRecords &&
          events.length > 0 &&
          "Choose an event to search its records."}
        {failed.map((group) => (
          <span key={group.key} role="alert">
            {" "}
            {group.nouns} could not be searched.
          </span>
        ))}
        {!search.pending &&
          search.groups.some((group) => group.total > group.hits.length) &&
          " Showing the first few of each; narrow the search to see others."}
      </div>
      <ul
        id={listId}
        role="listbox"
        aria-label="Results"
        className="cx-search__list"
      >
        {options.map((option, index) => {
          const heading = option.group !== lastGroup;
          lastGroup = option.group;
          return (
            <li key={option.id} role="presentation">
              {heading && <p className="cx-search__group">{option.group}</p>}
              <div
                id={`${listId}-${index}`}
                role="option"
                aria-selected={index === at}
                className="cx-search__option"
                onMouseMove={() => setActive(index)}
                onClick={() => option.run()}
              >
                <span>{option.label}</span>
                {option.detail && (
                  <span className="cx-search__detail">{option.detail}</span>
                )}
              </div>
            </li>
          );
        })}
      </ul>
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
