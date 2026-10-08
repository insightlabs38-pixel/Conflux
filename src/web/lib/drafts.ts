import { useSyncExternalStore } from "react";

/**
 * Unsaved edits that outlive the screen that holds them (PD-F005-B03-T02). A form that adopts
 * `useDraft` keeps its edits here, so going to another place in the workspace and coming back finds
 * them where they were, and the shell can show which places hold unsaved work.
 *
 * Deliberate state ownership, not keep-everything-mounted: a draft is data in this store, the screen
 * is rebuilt from it. Memory only - never storage or a URL, because drafts are typed text - so a
 * reload or sign-out discards them (the shell warns first). Keyed by workspace and a scope the form
 * names ("theme:<event>"), never shared between workspaces.
 */
export type DraftInfo = {
  scope: string;
  /** What to call it: "Event appearance". */
  label: string;
  /** The place that holds it, as the router's target, with its context but without typed text. */
  to: string;
  view: string;
};

type Stored = DraftInfo & { value: unknown };

const drafts = new Map<string, Stored>();
const listeners = new Set<() => void>();
const snapshots = new Map<string, string>();
const key = (workspace: string, scope: string) => `${workspace}\u0000${scope}`;

function changed() {
  snapshots.clear();
  listeners.forEach((listener) => listener());
}

export const readDraft = (workspace: string, scope: string): unknown =>
  drafts.get(key(workspace, scope))?.value;

export function writeDraft(
  workspace: string,
  scope: string,
  value: unknown,
  info: Omit<DraftInfo, "scope">,
) {
  drafts.set(key(workspace, scope), { ...info, scope, value });
  changed();
}

export function discardDraft(workspace: string, scope: string) {
  if (drafts.delete(key(workspace, scope))) changed();
}

/** Drop every draft of one workspace, or of all (sign-out). */
export function discardDrafts(workspace?: string) {
  let any = false;
  for (const k of [...drafts.keys()])
    if (workspace === undefined || k.startsWith(`${workspace}\u0000`)) {
      drafts.delete(k);
      any = true;
    }
  if (any) changed();
}

export const hasDrafts = () => drafts.size > 0;

export function draftsIn(workspace: string): DraftInfo[] {
  return [...drafts.entries()]
    .filter(([k]) => k.startsWith(`${workspace}\u0000`))
    .map(([, { value: _value, ...info }]) => info);
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** The drafts of one workspace as React state; the snapshot is a string so it only changes with them. */
export function useDrafts(workspace: string): DraftInfo[] {
  const text = useSyncExternalStore(
    subscribe,
    () => {
      let cached = snapshots.get(workspace);
      if (cached === undefined) {
        cached = JSON.stringify(draftsIn(workspace));
        snapshots.set(workspace, cached);
      }
      return cached;
    },
    () => "[]",
  );
  return JSON.parse(text) as DraftInfo[];
}

export function useAnyDrafts(): boolean {
  return useSyncExternalStore(subscribe, hasDrafts, () => false);
}
