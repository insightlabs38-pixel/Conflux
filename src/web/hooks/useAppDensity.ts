import { useLayoutEffect } from "react";
import { useDensityPreference } from "../lib/shellPreferences";

/**
 * Apply the person's table density to the app's own screens (`data-density` on the document, which
 * the table tokens in tokens.css key on). The default sets no attribute at all, so the long-standing
 * look is exactly what it was. The attribute found before is put back when the shell leaves.
 */
export function useAppDensity(user: string) {
  const density = useDensityPreference(user);
  useLayoutEffect(() => {
    if (!user || density === "comfortable") return;
    const root = document.documentElement;
    const before = root.getAttribute("data-density");
    root.setAttribute("data-density", density);
    return () => {
      if (before === null) root.removeAttribute("data-density");
      else root.setAttribute("data-density", before);
    };
  }, [density, user]);
  return density;
}
