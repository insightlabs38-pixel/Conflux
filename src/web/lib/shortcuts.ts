/**
 * The keyboard logic of the shell, apart from React so it can be tested exactly. "?" opens the help,
 * "/" opens the palette, and "G then a letter" goes to a place; a chord is dropped after
 * `CHORD_MS` or by any other key. Nothing here fires while the person is typing, while a dialog is
 * open, or with Ctrl, Cmd or Alt held (those belong to the browser and to the palette's own keys).
 */
export const CHORD_MS = 1500;

export type KeyInfo = {
  key: string;
  ctrlKey: boolean;
  metaKey: boolean;
  altKey: boolean;
  /** The element the key landed on. */
  target: Element | null;
  /** A modal dialog is open. */
  dialogOpen: boolean;
};

export type ShortcutAction =
  | { type: "help" }
  | { type: "palette" }
  | { type: "go"; letter: string }
  | { type: "chord" }
  | { type: "none" };

/** True where a printable key is text for the person, not a command. */
export function isTyping(target: Element | null): boolean {
  if (!target) return false;
  const element = target as HTMLElement;
  if (element.isContentEditable) return true;
  const tag = element.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
}

/**
 * What a key means, given whether a "g" is pending. Returns the action and whether a chord is now
 * pending. The caller handles the timer.
 */
export function interpret(
  info: KeyInfo,
  chordPending: boolean,
): { action: ShortcutAction; pending: boolean } {
  const none = { action: { type: "none" } as ShortcutAction, pending: false };
  if (info.ctrlKey || info.metaKey || info.altKey) return none;
  if (info.dialogOpen || isTyping(info.target)) return none;
  if (chordPending) {
    if (/^[a-z]$/i.test(info.key))
      return {
        action: { type: "go", letter: info.key.toLowerCase() },
        pending: false,
      };
    return none; // any other key drops the chord
  }
  if (info.key === "?") return { action: { type: "help" }, pending: false };
  if (info.key === "/") return { action: { type: "palette" }, pending: false };
  if (info.key === "g" || info.key === "G")
    return { action: { type: "chord" }, pending: true };
  return none;
}
