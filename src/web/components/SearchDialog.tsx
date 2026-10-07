import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import { useLocation, useNavigate } from "react-router";
import { useGlobalSearch, MIN_QUERY } from "../hooks/useGlobalSearch";
import { useShellEvents } from "../hooks/useShellEvents";
import { routes, type RouteTarget } from "../lib/routes";
import { Icon } from "./Icon";
import { Modal } from "./Modal";
import { useWorkspaceNavigation } from "./WorkspaceNavigation";

type Option = {
  id: string;
  group: string;
  label: string;
  detail?: string;
  to: string;
};

const matches = (text: string, query: string) =>
  text.toLowerCase().includes(query.toLowerCase());

/**
 * The header's Search: places, events and the records of the selected event, found as you type.
 * Places and events come from what the shell already holds; records come from the universal query
 * engine (`useGlobalSearch`), so the server decides what this person may find. Choosing a result
 * goes to its place through `routes.target`; what was typed is never put in a URL.
 */
export function SearchButton() {
  const [open, setOpen] = useState(false);
  const navigation = useWorkspaceNavigation();
  if (!navigation) return null;
  return (
    <>
      <button
        type="button"
        className="cx-search-open"
        aria-label="Search"
        aria-haspopup="dialog"
        onClick={() => setOpen(true)}
      >
        <Icon name="search" size={20} />
        <span className="cx-search-open__word">Search</span>
      </button>
      {open && <SearchDialog onClose={() => setOpen(false)} />}
    </>
  );
}

function SearchDialog({ onClose }: { onClose: () => void }) {
  const navigation = useWorkspaceNavigation()!;
  const navigate = useNavigate();
  const location = useLocation();
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const titleId = useId();
  const listId = useId();
  const input = useRef<HTMLInputElement>(null);
  // the modal puts focus on the dialog first; the search box is where a person starts typing
  useEffect(() => input.current?.focus(), []);
  const { workspaceId, role } = navigation;
  const { events } = useShellEvents(workspaceId, role);
  const requested = new URLSearchParams(location.search).get("event") ?? "";
  const eventId = events.some((event) => event.public_id === requested)
    ? requested
    : "";
  const search = useGlobalSearch({ workspaceId, eventId, query });
  const text = query.trim();
  const canSearchRecords = role === "organizer" || role === "admin";

  const options = useMemo(() => {
    const out: Option[] = [];
    if (text.length >= 1) {
      for (const place of navigation.destinations)
        if (matches(place.label, text))
          out.push({
            id: `place-${place.id}`,
            group: "Places",
            label: place.label,
            to: navigation.href(place.id),
          });
      for (const event of events)
        if (matches(event.name, text))
          out.push({
            id: `event-${event.public_id}`,
            group: "Events",
            label: event.name,
            to: routes.target(workspaceId, {
              view: navigation.view,
              event: event.public_id,
            } satisfies RouteTarget),
          });
    }
    for (const group of search.groups)
      for (const hit of group.hits)
        out.push({
          id: `${group.key}-${hit.id}`,
          group: group.nouns,
          label: hit.label,
          detail: hit.detail,
          to: routes.target(workspaceId, {
            view: hit.view,
            section: hit.section,
            event: eventId,
          }),
        });
    return out;
  }, [text, navigation, events, search.groups, workspaceId, eventId]);

  const at = Math.min(active, Math.max(0, options.length - 1));
  const go = (option: Option | undefined) => {
    if (!option) return;
    onClose();
    navigate(option.to);
    requestAnimationFrame(() =>
      document.getElementById("main-content")?.focus(),
    );
  };
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
      go(options[at]);
    }
  };

  const failed = search.groups.filter((group) => group.failed);
  const total = search.groups.reduce((sum, group) => sum + group.total, 0);
  const nothing =
    text.length >= MIN_QUERY && !search.pending && options.length === 0;
  let lastGroup = "";
  return (
    <Modal titleId={titleId} onClose={onClose} placement="top">
      <h2 id={titleId} className="cx-visually-hidden">
        Search
      </h2>
      <div className="cx-search">
        <Icon name="search" />
        <input
          ref={input}
          type="search"
          role="combobox"
          aria-label="Search places, events and records"
          aria-expanded={options.length > 0}
          aria-controls={listId}
          aria-activedescendant={options.length ? `${listId}-${at}` : undefined}
          autoComplete="off"
          value={query}
          placeholder="Search places, events and records"
          onChange={(event) => {
            setQuery(event.target.value);
            setActive(0);
          }}
          onKeyDown={keydown}
        />
      </div>
      <div role="status" className="cx-search__status">
        {text.length === 0 && "Type to search."}
        {text.length === 1 &&
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
          total >
            options.filter(
              (o) => !o.id.startsWith("place-") && !o.id.startsWith("event-"),
            ).length &&
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
                onClick={() => go(option)}
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
