/**
 * Ask a shell overlay to open from somewhere that does not own it (the account menu, a command, a
 * key). The overlays listen; nothing here knows what they contain. An overlay may take one argument
 * (the role to preview as).
 */
export type ShellOverlay = "palette" | "shortcuts" | "preview";
const EVENT = "conflux:shell-overlay";
type Detail = { overlay: ShellOverlay; arg?: string };

export function openShellOverlay(overlay: ShellOverlay, arg?: string) {
  window.dispatchEvent(
    new CustomEvent<Detail>(EVENT, { detail: { overlay, arg } }),
  );
}

export function onShellOverlay(
  overlay: ShellOverlay,
  handler: (arg?: string) => void,
) {
  const listen = (event: Event) => {
    const detail = (event as CustomEvent<Detail>).detail;
    if (detail?.overlay === overlay) handler(detail.arg);
  };
  window.addEventListener(EVENT, listen);
  return () => window.removeEventListener(EVENT, listen);
}
