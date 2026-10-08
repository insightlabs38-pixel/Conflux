import { useCallback, useRef, useState } from "react";
import { useWorkspaceNavigation } from "../components/WorkspaceNavigation";
import { discardDraft, readDraft, writeDraft } from "../lib/drafts";
import { shareableTarget } from "../lib/shareLink";

/**
 * `useState` for a form whose edits must survive leaving the screen. `initial` is what the server
 * holds; the value starts as the stored draft when there is one. `dirty` is whether it differs from
 * the last saved state. Call `saved()` once the server has accepted it (the value becomes the new
 * saved state) or `discard()` to go back to `initial`. Outside a workspace (tests, embeds) it keeps
 * nothing beyond the component, exactly like `useState`.
 */
export function useDraft<T>(
  scope: string,
  initial: T,
  label: string,
): [
  T,
  (next: T | ((current: T) => T)) => void,
  { dirty: boolean; saved: () => void; discard: () => void },
] {
  const navigation = useWorkspaceNavigation();
  const workspace = navigation?.workspaceId ?? "";
  const view = navigation?.view ?? "";
  const [value, setValueState] = useState<T>(() =>
    workspace && readDraft(workspace, scope) !== undefined
      ? (readDraft(workspace, scope) as T)
      : initial,
  );
  const [baseline, setBaseline] = useState(() => JSON.stringify(initial));
  const latest = useRef(value);
  latest.current = value;

  const keep = useCallback(
    (next: T, base: string) => {
      if (!workspace) return;
      if (JSON.stringify(next) === base) return discardDraft(workspace, scope);
      const to = shareableTarget(
        window.location.pathname,
        window.location.search,
      );
      if (to) writeDraft(workspace, scope, next, { label, to, view });
    },
    [workspace, scope, label, view],
  );
  const setValue = useCallback(
    (next: T | ((current: T) => T)) => {
      const resolved =
        typeof next === "function"
          ? (next as (current: T) => T)(latest.current)
          : next;
      latest.current = resolved;
      setValueState(resolved);
      keep(resolved, baseline);
    },
    [keep, baseline],
  );
  return [
    value,
    setValue,
    {
      dirty: JSON.stringify(value) !== baseline,
      saved: () => {
        const base = JSON.stringify(latest.current);
        setBaseline(base);
        if (workspace) discardDraft(workspace, scope);
      },
      discard: () => {
        latest.current = initial;
        setValueState(initial);
        setBaseline(JSON.stringify(initial));
        if (workspace) discardDraft(workspace, scope);
      },
    },
  ];
}
