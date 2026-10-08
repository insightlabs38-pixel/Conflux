/**
 * The command registry (primitive COMMANDS, spec 005, ESC-20260930-007): one place that knows what a
 * person can do from the keyboard. The palette is its first consumer; the shortcut overlay
 * (PD-F005-B02-T07) and selection-parameterised commands (PD-F005-B03-T04) read the same registry.
 *
 * Rules
 * - A command is data: an id, words, a group, an optional shortcut, `when(context)` and `run(context)`.
 *   `when` only narrows what is offered (the role, an event, a module that is off); it never decides
 *   what is allowed, the server still refuses.
 * - A command never changes domain state itself. One that must calls the canonical endpoint through
 *   the shared client and shows the standard consequence step (none ships in this batch).
 * - Providers contribute commands for the current context (a command per place, per event), so a
 *   feature adds commands by registering a provider; nothing else lists commands.
 * - Ranking is deterministic: exact, prefix, word prefix, substring, subsequence, then the person's
 *   recent commands, then registration order. No model, no randomness.
 */
import type { RouteTarget } from "./routes";

export type CommandContext = {
  role: string;
  workspaceId: string;
  /** The selected event, or "" when none is. */
  eventId: string;
  /** The current view of the workspace. */
  view: string;
  /** The places this person has in this workspace (the shell's destinations, hidden modules removed). */
  places: { id: string; label: string; to: string; key?: string }[];
  /** The events this person may choose between, the selected one marked. */
  events: { id: string; name: string; current: boolean }[];
  /** Go to a location (path and search) built with `target`. */
  go: (to: string) => void;
  /** A location in this workspace that keeps the current event and role (`navigation.target`). */
  target: (target: RouteTarget) => string;
  /** The person's pinned saved views of the selected event that still exist. */
  pinned: { id: string; entity: string; name: string }[];
  /** The saved views they opened lately (still existing, not pinned), newest first. */
  recentViews: { id: string; entity: string; name: string }[];
  /** The roles the person holds here, the one being viewed as marked. */
  roles: { role: string; label: string; current: boolean }[];
  /** Everything else a command may need is handed in by the shell as named capabilities. */
  capabilities: Partial<{
    signOut: () => void;
    setTheme: (theme: "system" | "light" | "dark") => void;
    setDensity: (density: "comfortable" | "compact" | "high") => void;
    openShortcuts: () => void;
    /** Whether live operations mode is on, and the switch for it. */
    liveOperations: boolean;
    setLiveOperations: (on: boolean) => void;
    /** Copy the address that reopens exactly this view (event, section, saved view, sort, page, record). */
    copyLink: () => void;
    /** Open the read-only preview as a participant, a judge or the public. */
    openPreview: (role: "participant" | "judge" | "public") => void;
  }>;
};

export type Command = {
  id: string;
  label: string;
  group: string;
  /** Extra words that find it (synonyms). */
  keywords?: string[];
  /** A key combination shown beside it, e.g. "G then J"; the palette itself does not bind it. */
  shortcut?: string;
  when?: (context: CommandContext) => boolean;
  run: (context: CommandContext) => void;
};

export type CommandProvider = (context: CommandContext) => Command[];

const providers: CommandProvider[] = [];

/** Add a provider. Returns a function that removes it (tests, hot reload). */
export function registerCommandProvider(provider: CommandProvider) {
  providers.push(provider);
  return () => {
    const at = providers.indexOf(provider);
    if (at >= 0) providers.splice(at, 1);
  };
}

/** Every command offered in this context, in registration order, each id once. */
export function commandsFor(context: CommandContext): Command[] {
  const seen = new Set<string>();
  const out: Command[] = [];
  for (const provider of providers)
    for (const command of provider(context)) {
      if (seen.has(command.id) || (command.when && !command.when(context)))
        continue;
      seen.add(command.id);
      out.push(command);
    }
  return out;
}

const norm = (text: string) => text.toLowerCase().normalize("NFKD");

function subsequence(text: string, query: string): boolean {
  let at = 0;
  for (const letter of text) if (letter === query[at]) at += 1;
  return at === query.length;
}

/** 0 means no match; higher is better. */
export function score(command: Command, query: string): number {
  const q = norm(query.trim());
  if (!q) return 1;
  const label = norm(command.label);
  if (label === q) return 100;
  if (label.startsWith(q)) return 80;
  const words = [label, ...(command.keywords ?? []).map(norm)]
    .join(" ")
    .split(/[^a-z0-9]+/)
    .filter(Boolean);
  if (words.some((word) => word.startsWith(q))) return 60;
  // every typed word starts a word of the command ("go jud" finds "Go to Judging")
  const typed = q.split(/\s+/);
  if (
    typed.length > 1 &&
    typed.every((t) => words.some((w) => w.startsWith(t)))
  )
    return 55;
  if (
    label.includes(q) ||
    (command.keywords ?? []).some((k) => norm(k).includes(q))
  )
    return 40;
  if (subsequence(label.replace(/\s+/g, ""), q.replace(/\s+/g, ""))) return 20;
  return 0;
}

/**
 * The commands that match, best first. With no query, the recent ones come first (most recent
 * first), then everything else in registration order.
 */
export function rankCommands(
  commands: Command[],
  query: string,
  recent: string[] = [],
): Command[] {
  const order = new Map(commands.map((command, at) => [command.id, at]));
  const recency = (command: Command) => {
    const at = recent.indexOf(command.id);
    return at < 0 ? Number.MAX_SAFE_INTEGER : at;
  };
  return commands
    .map((command) => ({ command, score: score(command, query) }))
    .filter((entry) => entry.score > 0)
    .sort(
      (a, b) =>
        b.score - a.score ||
        recency(a.command) - recency(b.command) ||
        order.get(a.command.id)! - order.get(b.command.id)!,
    )
    .map((entry) => entry.command);
}
