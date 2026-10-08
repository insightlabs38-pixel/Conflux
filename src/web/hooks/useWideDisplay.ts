import { useSyncExternalStore } from "react";

/** Operations mode needs room: the second pane only exists from this width (design D-009, 1800+). */
export const WIDE_DISPLAY_PX = 1800;
const QUERY = `(min-width: ${WIDE_DISPLAY_PX}px)`;

export function useWideDisplay(): boolean {
  return useSyncExternalStore(
    (listener) => {
      const list = window.matchMedia?.(QUERY);
      list?.addEventListener?.("change", listener);
      return () => list?.removeEventListener?.("change", listener);
    },
    () => window.matchMedia?.(QUERY).matches ?? false,
    () => false,
  );
}
