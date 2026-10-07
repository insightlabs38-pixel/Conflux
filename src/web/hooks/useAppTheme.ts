import { useLayoutEffect, useSyncExternalStore } from "react";
import { useThemePreference } from "../lib/shellPreferences";

const QUERY = "(prefers-color-scheme: dark)";

function subscribe(listener: () => void) {
  const media = window.matchMedia?.(QUERY);
  media?.addEventListener("change", listener);
  return () => media?.removeEventListener("change", listener);
}

/** Whether the operating system asks for dark; false where it cannot be asked (tests, old browsers). */
const systemDark = () => window.matchMedia?.(QUERY).matches ?? false;

/**
 * Apply the person's theme to the app's own screens (`data-theme` on the document, which the v3
 * dark tokens key on). The server-rendered public pages are a separate document and the React public
 * event site sets its own theme on its own root, so neither is touched. The attribute the app found
 * is put back when the person signs out or leaves, so nothing outlives the session.
 */
export function useAppTheme(user: string) {
  const preference = useThemePreference(user);
  const dark = useSyncExternalStore(subscribe, systemDark, () => false);
  const effective = !user
    ? null
    : preference === "system"
      ? dark
        ? "dark"
        : "light"
      : preference;
  // before paint, so the shell never shows in the wrong theme first
  useLayoutEffect(() => {
    if (!effective) return;
    const root = document.documentElement;
    const before = root.getAttribute("data-theme");
    root.setAttribute("data-theme", effective);
    return () => {
      if (before === null) root.removeAttribute("data-theme");
      else root.setAttribute("data-theme", before);
    };
  }, [effective]);
  return { preference, effective };
}
