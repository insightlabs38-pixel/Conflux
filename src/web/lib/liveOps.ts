import type { ConnectionStatus } from "./realtime";

/**
 * What the connection under a live list means to the person watching it (design States-2 "Live ops",
 * state S-OFF): one word, the reason in a sentence, and whether things that need fresh data should
 * wait. Transport trouble is a status here, never an error to handle (lib/realtime.ts).
 */
export type LiveHealth = {
  tone: "ok" | "degraded" | "offline" | "idle";
  word: string;
  detail: string;
  /** Actions that need live data are disabled while this is true, with `detail` as the reason. */
  blocksActions: boolean;
};

export function describeHealth(
  status: ConnectionStatus,
  everySeconds: number,
): LiveHealth {
  switch (status) {
    case "live":
      return {
        tone: "ok",
        word: "Connected",
        detail: "Updates arrive as they happen.",
        blocksActions: false,
      };
    case "polling":
      return {
        tone: "degraded",
        word: "Checking",
        detail: `Asking the server every ${everySeconds} s; changes can take that long to show.`,
        blocksActions: false,
      };
    case "connecting":
      return {
        tone: "degraded",
        word: "Connecting",
        detail: "Reconnecting to the server.",
        blocksActions: false,
      };
    case "offline":
      return {
        tone: "offline",
        word: "Offline",
        detail:
          "This device has no connection. Showing the last data received; changes wait until it is back.",
        blocksActions: true,
      };
    default:
      return {
        tone: "idle",
        word: "Not watching",
        detail: "Live updates are not running.",
        blocksActions: false,
      };
  }
}

/** "as of 14:46:20 · 42 s ago": the time is the data's, the age is relative to `now`. */
export function dataAge(now: number, updatedAt: number | null): string {
  if (updatedAt === null) return "No data yet";
  const seconds = Math.max(0, Math.round((now - updatedAt) / 1000));
  const clock = new Date(updatedAt).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
  const ago =
    seconds < 5
      ? "just now"
      : seconds < 60
        ? `${seconds} s ago`
        : seconds < 3600
          ? `${Math.floor(seconds / 60)} min ago`
          : `${Math.floor(seconds / 3600)} h ago`;
  return `Data as of ${clock} \u00b7 ${ago}`;
}
