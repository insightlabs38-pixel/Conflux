import { useSyncExternalStore } from "react";

/**
 * What is selected in the list in front of the person, offered to the command palette
 * (PD-F005-B03-T04). A list publishes its selection and the commands that apply to it; the palette
 * reads the one most recently changed, so "Move 3 projects to Track A" is a command like any other.
 * A command here only starts the list's own workflow (open the record, copy names, open the bulk
 * preview); nothing changes domain state without the consequence step. The selection is ids on this
 * page of one list, in memory only, and goes away with the list.
 */
export type SelectionCommand = {
  id: string;
  label: string;
  run: () => void;
};

export type SelectionSnapshot = {
  /** The list: its entity key and its plural name, for the palette's group heading. */
  entity: string;
  noun: string;
  count: number;
  commands: SelectionCommand[];
};

const slots = new Map<string, SelectionSnapshot>();
const listeners = new Set<() => void>();
let current: SelectionSnapshot | null = null;

/** Publish (or with null, withdraw) the selection of one list. Empty selections are withdrawn. */
export function publishSelection(
  slot: string,
  snapshot: SelectionSnapshot | null,
) {
  const next = snapshot && snapshot.count > 0 ? snapshot : null;
  if (next) {
    slots.delete(slot); // re-inserted last: the most recently changed list wins
    slots.set(slot, next);
  } else if (!slots.delete(slot)) return;
  current = [...slots.values()].at(-1) ?? null;
  listeners.forEach((listener) => listener());
}

export const currentSelection = () => current;

export function useSelection(): SelectionSnapshot | null {
  return useSyncExternalStore(
    (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    () => current,
    () => null,
  );
}

/** "1 project", "3 projects": the list's plural name made to fit a count. */
export function countOf(count: number, plural: string): string {
  const name = plural.toLowerCase();
  return `${count} ${count === 1 && name.endsWith("s") ? name.slice(0, -1) : name}`;
}
