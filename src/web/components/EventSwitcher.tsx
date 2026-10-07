import { useEffect, useRef } from "react";
import { Link, useLocation } from "react-router";
import { useMe } from "../hooks/useMe";
import { useShellEvents, type ShellEvent } from "../hooks/useShellEvents";
import { routes } from "../lib/routes";
import {
  rememberEvent,
  toggleFavoriteEvent,
  useFavoriteEvents,
  useRecentEvents,
} from "../lib/shellPreferences";
import { Icon } from "./Icon";
import { useWorkspaceNavigation } from "./WorkspaceNavigation";

const RECENT_SHOWN = 5;

/**
 * Choose the event the workspace is about, and the workspace itself. The selected event is the URL's
 * `event` context param (lib/urlState.ts), so this reads and writes it through `routes.target`; the
 * lists are the ones the role already loads from the server, so a stale favorite or recent that is
 * no longer listed is simply not shown. Choosing one is a history entry (Back returns) and drops the
 * params that depend on the event (`stage`, `plan`, `invite`).
 */
export function EventSwitcher() {
  const navigation = useWorkspaceNavigation();
  const location = useLocation();
  const me = useMe().data;
  const user = me?.public_id ?? "";
  const workspaceId = navigation?.workspaceId ?? "";
  const { events, loading, error, reload } = useShellEvents(
    workspaceId,
    navigation?.role ?? "",
  );
  const favorites = useFavoriteEvents(user, workspaceId);
  const recents = useRecentEvents(user, workspaceId);
  const details = useRef<HTMLDetailsElement>(null);

  const requested = new URLSearchParams(location.search).get("event") ?? "";
  const current = events.find((event) => event.public_id === requested) ?? null;
  // A choice is remembered when it is made, not on every visit to a page.
  useEffect(() => {
    if (current) rememberEvent(user, workspaceId, current.public_id);
  }, [current, user, workspaceId]);

  if (!navigation) return null;
  const memberships = (me?.memberships ?? []).filter(
    (membership, at, all) =>
      all.findIndex((other) => other.workspace === membership.workspace) === at,
  );
  const byId = new Map(events.map((event) => [event.public_id, event]));
  const favorite = favorites
    .map((id) => byId.get(id))
    .filter((event): event is ShellEvent => !!event);
  const recent = recents
    .filter((id) => !favorites.includes(id) && id !== current?.public_id)
    .map((id) => byId.get(id))
    .filter((event): event is ShellEvent => !!event)
    .slice(0, RECENT_SHOWN);
  const shown = new Set(
    [...favorite, ...recent].map((event) => event.public_id),
  );
  const rest = events.filter((event) => !shown.has(event.public_id));

  const label = current
    ? current.name
    : loading
      ? "Loading events…"
      : events.length
        ? "Choose an event"
        : "No events";
  const to = (eventId: string) =>
    navigation.target({ view: navigation.view, event: eventId });

  const row = (event: ShellEvent) => {
    const starred = favorites.includes(event.public_id);
    return (
      <li key={event.public_id} className="cx-switcher__row">
        <Link
          to={to(event.public_id)}
          className="cx-switcher__choice"
          aria-current={
            event.public_id === current?.public_id ? "true" : undefined
          }
          onClick={() => {
            if (details.current) details.current.open = false;
          }}
        >
          {event.name}
        </Link>
        <button
          type="button"
          className="cx-switcher__star"
          aria-pressed={starred}
          aria-label={`Favorite ${event.name}`}
          title={starred ? "Remove from favorites" : "Add to favorites"}
          onClick={() =>
            toggleFavoriteEvent(user, workspaceId, event.public_id)
          }
        >
          <Icon name="star" />
        </button>
      </li>
    );
  };

  return (
    <details
      ref={details}
      className="cx-switcher"
      onKeyDown={(event) => {
        if (event.key === "Escape" && details.current?.open) {
          event.stopPropagation();
          details.current.open = false;
          details.current.querySelector("summary")?.focus();
        }
      }}
    >
      <summary aria-label={`Event: ${label}. Switch event`}>
        <span>{label}</span>
        <Icon name="chevron-down" />
      </summary>
      <div className="cx-switcher__panel">
        {error && (
          <p role="alert">
            Could not load events.{" "}
            <button type="button" onClick={() => void reload()}>
              Try again
            </button>
          </p>
        )}
        {favorite.length > 0 && (
          <section aria-label="Favorite events">
            <p className="cx-switcher__group">Favorites</p>
            <ul>{favorite.map(row)}</ul>
          </section>
        )}
        {recent.length > 0 && (
          <section aria-label="Recent events">
            <p className="cx-switcher__group">Recent</p>
            <ul>{recent.map(row)}</ul>
          </section>
        )}
        {rest.length > 0 && (
          <section aria-label="All events">
            <p className="cx-switcher__group">
              {favorite.length + recent.length > 0 ? "Other events" : "Events"}
            </p>
            <ul>{rest.map(row)}</ul>
          </section>
        )}
        {!loading && !error && events.length === 0 && (
          <p role="status">No events in this workspace yet.</p>
        )}
        {memberships.length > 1 && (
          <section aria-label="Workspaces">
            <p className="cx-switcher__group">Workspaces</p>
            <ul>
              {memberships.map((membership) => (
                <li key={membership.workspace}>
                  <Link
                    to={routes.workspace(membership.workspace)}
                    className="cx-switcher__choice"
                    aria-current={
                      membership.workspace === workspaceId ? "true" : undefined
                    }
                    onClick={() => {
                      if (details.current) details.current.open = false;
                    }}
                  >
                    {membership.workspace_name || membership.workspace}
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </details>
  );
}
