/**
 * Ask a shell overlay to open from somewhere that does not own it (the account menu, a command, a
 * key). The overlays listen; nothing here knows what they contain.
 */
export type ShellOverlay = "palette" | "shortcuts";
const EVENT = "conflux:shell-overlay";

export function openShellOverlay(overlay: ShellOverlay) {
  window.dispatchEvent(new CustomEvent(EVENT, { detail: overlay }));
}

export function onShellOverlay(overlay: ShellOverlay, handler: () => void) {
  const listen = (event: Event) => {
    if ((event as CustomEvent<ShellOverlay>).detail === overlay) handler();
  };
  window.addEventListener(EVENT, listen);
  return () => window.removeEventListener(EVENT, listen);
}
