import { useMemo, useSyncExternalStore } from "react";

/**
 * Everything the shell remembers about a person, in one place (spec 005, PD-F005-B01). It is
 * device-local by decision: a value lives under `conflux:v1:<user>:<workspace>:<name>`, is validated
 * when read, is only ever *used* after it matches what the server listed (a stored id is a request,
 * never authority) and is removed at sign-out so a shared computer keeps nothing. Moving these to a
 * per-user server store later changes only this file.
 */
const PREFIX = "conflux:v1:";
export const MAX_FAVORITES = 12;
export const MAX_RECENTS = 8;

const ID = /^[A-Za-z0-9_.:-]{1,100}$/;

function storage(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.localStorage;
  } catch {
    return null; // blocked storage: the shell works, it just remembers nothing
  }
}

const key = (user: string, workspace: string, name: string) =>
  `${PREFIX}${user}:${workspace}:${name}`;

const listeners = new Set<() => void>();
const changed = () => listeners.forEach((listener) => listener());

/** A stored list of ids: anything that is not a short array of id-like strings reads as empty. */
function readIds(user: string, workspace: string, name: string): string[] {
  if (!user || !workspace) return [];
  const raw = storage()?.getItem(key(user, workspace, name));
  if (!raw) return [];
  try {
    const value: unknown = JSON.parse(raw);
    if (!Array.isArray(value)) return [];
    const seen = new Set<string>();
    for (const item of value)
      if (typeof item === "string" && ID.test(item)) seen.add(item);
    return [...seen];
  } catch {
    return [];
  }
}

function writeIds(
  user: string,
  workspace: string,
  name: string,
  ids: string[],
) {
  if (!user || !workspace) return;
  try {
    storage()?.setItem(key(user, workspace, name), JSON.stringify(ids));
  } catch {
    // quota or blocked: nothing is remembered, nothing breaks
  }
  changed();
}

export const favoriteEvents = (user: string, workspace: string) =>
  readIds(user, workspace, "favorite-events").slice(0, MAX_FAVORITES);

export const recentEvents = (user: string, workspace: string) =>
  readIds(user, workspace, "recent-events").slice(0, MAX_RECENTS);

/** Star or unstar an event. Returns false when the favorites are full and nothing was added. */
export function toggleFavoriteEvent(
  user: string,
  workspace: string,
  eventId: string,
): boolean {
  if (!ID.test(eventId)) return false;
  const current = favoriteEvents(user, workspace);
  if (current.includes(eventId)) {
    writeIds(
      user,
      workspace,
      "favorite-events",
      current.filter((id) => id !== eventId),
    );
    return true;
  }
  if (current.length >= MAX_FAVORITES) return false;
  writeIds(user, workspace, "favorite-events", [...current, eventId]);
  return true;
}

/** Remember that an event was chosen: it moves to the front, the list keeps the newest eight. */
export function rememberEvent(
  user: string,
  workspace: string,
  eventId: string,
) {
  if (!ID.test(eventId)) return;
  const current = recentEvents(user, workspace);
  if (current[0] === eventId) return;
  writeIds(
    user,
    workspace,
    "recent-events",
    [eventId, ...current.filter((id) => id !== eventId)].slice(0, MAX_RECENTS),
  );
}

/**
 * How tightly tables are set (design D-009): comfortable is the app's long-standing look (rows about
 * 44px), compact about 36px and high density about 28px. Never changed because of the viewport.
 */
export type Density = "comfortable" | "compact" | "high";
const DENSITIES: readonly Density[] = ["comfortable", "compact", "high"];

export function densityPreference(user: string): Density {
  if (!user) return "comfortable";
  const raw = storage()?.getItem(key(user, DEVICE, "density"));
  return DENSITIES.find((density) => density === raw) ?? "comfortable";
}

export function setDensityPreference(user: string, density: Density) {
  if (!user || !DENSITIES.includes(density)) return;
  try {
    if (density === "comfortable")
      storage()?.removeItem(key(user, DEVICE, "density"));
    else storage()?.setItem(key(user, DEVICE, "density"), density);
  } catch {
    // blocked storage: the choice lasts until the page is closed
  }
  changed();
}

export function useDensityPreference(user: string): Density {
  return useSyncExternalStore(
    subscribe,
    () => densityPreference(user),
    () => "comfortable" as Density,
  );
}

/**
 * Single-key shortcuts (?, /, G then a letter) can be switched off (WCAG 2.1.4); the keys that use
 * Ctrl or Cmd stay. On by default, stored only when off.
 */
export const singleKeyShortcuts = (user: string) =>
  !user ||
  storage()?.getItem(key(user, DEVICE, "single-key-shortcuts")) !== "off";

export function setSingleKeyShortcuts(user: string, on: boolean) {
  if (!user) return;
  try {
    if (on) storage()?.removeItem(key(user, DEVICE, "single-key-shortcuts"));
    else storage()?.setItem(key(user, DEVICE, "single-key-shortcuts"), "off");
  } catch {
    // blocked storage: the choice lasts until the page is closed
  }
  changed();
}

export const useSingleKeyShortcuts = (user: string) =>
  useSyncExternalStore(
    subscribe,
    () => singleKeyShortcuts(user),
    () => true,
  );

/**
 * Pinned views: a person's shortcut to one saved view of an entity in an event. A pin is the three
 * ids "event:entity:view"; the view itself (its name, filter, columns) stays the server's, so a pin
 * to a view that was deleted or is no longer visible simply does not resolve and is not shown.
 */
export const MAX_PINS = 12;
export type PinnedView = { event: string; entity: string; view: string };

const pinText = (pin: PinnedView) => `${pin.event}:${pin.entity}:${pin.view}`;

export function pinnedViews(user: string, workspace: string): PinnedView[] {
  const out: PinnedView[] = [];
  for (const text of readIds(user, workspace, "pinned-views")) {
    const [event, entity, view, extra] = text.split(":");
    if (event && entity && view && extra === undefined)
      out.push({ event, entity, view });
  }
  return out.slice(0, MAX_PINS);
}

/** Pin or unpin. Returns false when the pins are full and nothing was added. */
export function togglePinnedView(
  user: string,
  workspace: string,
  pin: PinnedView,
): boolean {
  if (
    ![pin.event, pin.entity, pin.view].every(
      (part) => ID.test(part) && !part.includes(":"),
    )
  )
    return false;
  const text = pinText(pin);
  const current = pinnedViews(user, workspace).map(pinText);
  if (current.includes(text)) {
    writeIds(
      user,
      workspace,
      "pinned-views",
      current.filter((other) => other !== text),
    );
    return true;
  }
  if (current.length >= MAX_PINS) return false;
  writeIds(user, workspace, "pinned-views", [...current, text]);
  return true;
}

/** The saved views the person opened lately: the same three ids as a pin, newest first, eight at most. */
const MAX_RECENT_VIEWS = 8;
export function recentViews(user: string, workspace: string): PinnedView[] {
  const out: PinnedView[] = [];
  for (const text of readIds(user, workspace, "recent-views")) {
    const [event, entity, view, extra] = text.split(":");
    if (event && entity && view && extra === undefined)
      out.push({ event, entity, view });
  }
  return out.slice(0, MAX_RECENT_VIEWS);
}

export function rememberView(user: string, workspace: string, pin: PinnedView) {
  if (
    ![pin.event, pin.entity, pin.view].every(
      (part) => ID.test(part) && !part.includes(":"),
    )
  )
    return;
  const text = pinText(pin);
  const current = recentViews(user, workspace).map(pinText);
  if (current[0] === text) return;
  writeIds(
    user,
    workspace,
    "recent-views",
    [text, ...current.filter((other) => other !== text)].slice(
      0,
      MAX_RECENT_VIEWS,
    ),
  );
}

export const useRecentViews = (
  user: string,
  workspace: string,
): PinnedView[] => {
  const snapshot = useSyncExternalStore(
    subscribe,
    () => JSON.stringify(recentViews(user, workspace)),
    () => "[]",
  );
  return useMemo(() => JSON.parse(snapshot) as PinnedView[], [snapshot]);
};

export const usePinnedViews = (
  user: string,
  workspace: string,
): PinnedView[] => {
  const snapshot = useSyncExternalStore(
    subscribe,
    () => JSON.stringify(pinnedViews(user, workspace)),
    () => "[]",
  );
  return useMemo(() => JSON.parse(snapshot) as PinnedView[], [snapshot]);
};

const MAX_RECENT_COMMANDS = 5;
const COMMAND_ID = /^[a-z][a-z0-9._-]{0,80}$/i;

export const recentCommands = (user: string, workspace: string) =>
  readIds(user, workspace, "recent-commands")
    .filter((id) => COMMAND_ID.test(id))
    .slice(0, MAX_RECENT_COMMANDS);

/** Remember a command that was run: newest first, once each, the latest five. */
export function rememberCommand(user: string, workspace: string, id: string) {
  if (!COMMAND_ID.test(id)) return;
  const current = recentCommands(user, workspace);
  if (current[0] === id) return;
  writeIds(
    user,
    workspace,
    "recent-commands",
    [id, ...current.filter((other) => other !== id)].slice(
      0,
      MAX_RECENT_COMMANDS,
    ),
  );
}

export const useRecentCommands = (user: string, workspace: string) =>
  useList(() => recentCommands(user, workspace));

/** Forget everything the shell stored, for every person and workspace (called at sign-out). */
export function clearShellPreferences() {
  const store = storage();
  if (!store) return;
  try {
    for (const name of Object.keys(store))
      if (name.startsWith(PREFIX)) store.removeItem(name);
  } catch {
    // nothing to do
  }
  changed();
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  window.addEventListener("storage", listener); // another tab changed it
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", listener);
  };
}

/** The lists as React state; the snapshot is a string so an unchanged value does not re-render. */
function useList(read: () => string[]): string[] {
  const snapshot = useSyncExternalStore(
    subscribe,
    () => JSON.stringify(read()),
    () => "[]",
  );
  return JSON.parse(snapshot) as string[];
}

export const useFavoriteEvents = (user: string, workspace: string) =>
  useList(() => favoriteEvents(user, workspace));
export const useRecentEvents = (user: string, workspace: string) =>
  useList(() => recentEvents(user, workspace));

/**
 * Which columns a person keeps visible in a list (PD-F005-B03-T01): per person, workspace and entity,
 * the field keys in the order the list shows them. A stored key is only a request - the list honours
 * the ones it still has and falls back to its defaults when none remain. A saved view's own columns
 * win while that view is open; this is what the list shows otherwise.
 */
export const MAX_COLUMNS = 60;

export const columnPreference = (
  user: string,
  workspace: string,
  entity: string,
): string[] =>
  ID.test(entity)
    ? readIds(user, workspace, `columns:${entity}`).slice(0, MAX_COLUMNS)
    : [];

/** Remember the columns; an empty list forgets them so the list returns to its defaults. */
export function setColumnPreference(
  user: string,
  workspace: string,
  entity: string,
  keys: string[],
) {
  if (!user || !workspace || !ID.test(entity)) return;
  const name = `columns:${entity}`;
  if (keys.length === 0) {
    try {
      storage()?.removeItem(key(user, workspace, name));
    } catch {
      // blocked storage: nothing was remembered
    }
    changed();
    return;
  }
  writeIds(
    user,
    workspace,
    name,
    keys.filter((k) => ID.test(k)).slice(0, MAX_COLUMNS),
  );
}

export const useColumnPreference = (
  user: string,
  workspace: string,
  entity: string,
) => useList(() => columnPreference(user, workspace, entity));

/** The colour theme of the app's own screens; "system" follows the operating system (design D-008). */
export type Theme = "system" | "light" | "dark";
const THEMES: readonly Theme[] = ["system", "light", "dark"];
const DEVICE = "device"; // a value that is the person's, not one workspace's

export function themePreference(user: string): Theme {
  if (!user) return "system";
  const raw = storage()?.getItem(key(user, DEVICE, "theme"));
  return THEMES.find((theme) => theme === raw) ?? "system";
}

export function setThemePreference(user: string, theme: Theme) {
  if (!user || !THEMES.includes(theme)) return;
  try {
    if (theme === "system") storage()?.removeItem(key(user, DEVICE, "theme"));
    else storage()?.setItem(key(user, DEVICE, "theme"), theme);
  } catch {
    // blocked storage: the choice lasts until the page is closed, nothing breaks
  }
  changed();
}

export function useThemePreference(user: string): Theme {
  return useSyncExternalStore(
    subscribe,
    () => themePreference(user),
    () => "system" as Theme,
  );
}
