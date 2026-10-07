import { useSyncExternalStore } from "react";

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
