/**
 * A short message from the shell to the person ("Link copied"): shown by `ShellNotice` in a polite
 * live region for a few seconds. One channel so no feature draws its own toast.
 */
const EVENT = "conflux:shell-notice";

export function announce(message: string) {
  window.dispatchEvent(new CustomEvent<string>(EVENT, { detail: message }));
}

export function onNotice(handler: (message: string) => void) {
  const listen = (event: Event) =>
    handler((event as CustomEvent<string>).detail);
  window.addEventListener(EVENT, listen);
  return () => window.removeEventListener(EVENT, listen);
}
