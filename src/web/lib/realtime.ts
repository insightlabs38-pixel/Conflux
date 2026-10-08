/**
 * The realtime subscription boundary (PD-B04-T06). Screens that benefit from live updates depend on
 * this file only; the transport (polling today, SSE/WebSocket when the API offers a push channel)
 * is a plug behind `RealtimeTransport` and can change without touching a screen or the app shell.
 *
 * Rules
 * - An event is a *hint*, never data: it says "topic X may have changed". Consumers react by
 *   refetching through the server-state layer (`useRealtimeInvalidate`), so authorization,
 *   validation and ordering stay server-side and a spoofed or replayed hint can do no more than
 *   cause one extra authorized read. Payloads are never merged into UI state.
 * - Topics are `<scope>:<id>:<resource>` (e.g. `workspace:w1:inbox`), opened only while a mounted
 *   screen wants them; identical topics share one transport subscription (ref-counted) and it
 *   closes with the last subscriber.
 * - Bursts are coalesced: any number of hints inside `coalesceMs` reach handlers once.
 * - A hub belongs to a session: `reset()` (sign-in/sign-out) closes everything, like the query
 *   cache, so nothing subscribed for one account outlives it.
 * - Live updates never touch unsaved drafts: drafts live in component state, hints only invalidate
 *   server state.
 * - Transport trouble is a status (`polling`, `offline`), never an error the user must handle.
 */
export type ConnectionStatus =
  "idle" | "connecting" | "live" | "polling" | "offline";

export type RealtimeEvent = { topic: string; kind?: string };
export type Unsubscribe = () => void;

export interface RealtimeTransport {
  /** Start delivering hints for `topic`; the returned function stops them. */
  open(
    topic: string,
    deliver: (event: RealtimeEvent) => void,
    setStatus: (status: ConnectionStatus) => void,
  ): Unsubscribe;
}

type Entry = {
  handlers: Set<(event: RealtimeEvent) => void>;
  close: Unsubscribe;
  status: ConnectionStatus;
  timer: ReturnType<typeof setTimeout> | null;
  last: RealtimeEvent | null;
};

export class RealtimeHub {
  private entries = new Map<string, Entry>();
  private listeners = new Set<() => void>();

  constructor(
    private readonly transport: RealtimeTransport,
    private readonly options: { coalesceMs?: number } = {},
  ) {}

  subscribe(
    topic: string,
    handler: (event: RealtimeEvent) => void,
  ): Unsubscribe {
    let entry = this.entries.get(topic);
    if (!entry) {
      const created: Entry = {
        handlers: new Set(),
        close: () => {},
        status: "connecting",
        timer: null,
        last: null,
      };
      this.entries.set(topic, created);
      entry = created;
      created.close = this.transport.open(
        topic,
        (event) => this.deliver(topic, event),
        (status) => {
          if (
            this.entries.get(topic) === created &&
            created.status !== status
          ) {
            created.status = status;
            this.notify();
          }
        },
      );
    }
    entry.handlers.add(handler);
    this.notify();
    let active = true;
    return () => {
      if (!active) return;
      active = false;
      const current = this.entries.get(topic);
      if (!current) return;
      current.handlers.delete(handler);
      if (current.handlers.size === 0) this.drop(topic);
    };
  }

  status(topic: string): ConnectionStatus {
    return this.entries.get(topic)?.status ?? "idle";
  }

  /** Subscribe to status changes (for `useSyncExternalStore`). */
  onChange(listener: () => void): Unsubscribe {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  /** Close every subscription; call when the session changes. */
  reset(): void {
    for (const topic of [...this.entries.keys()]) this.drop(topic);
  }

  private drop(topic: string) {
    const entry = this.entries.get(topic);
    if (!entry) return;
    this.entries.delete(topic);
    if (entry.timer) clearTimeout(entry.timer);
    entry.close();
    this.notify();
  }

  private deliver(topic: string, event: RealtimeEvent) {
    const entry = this.entries.get(topic);
    if (!entry) return;
    entry.last = event;
    if (entry.timer) return; // coalesced into the pending flush
    entry.timer = setTimeout(() => {
      entry.timer = null;
      const flushed = entry.last;
      entry.last = null;
      if (!flushed || this.entries.get(topic) !== entry) return;
      for (const handler of [...entry.handlers]) {
        try {
          handler(flushed);
        } catch (error) {
          // One faulty consumer must not starve the others.
          console.error("realtime handler failed", error);
        }
      }
    }, this.options.coalesceMs ?? 250);
  }

  private notify() {
    for (const listener of [...this.listeners]) listener();
  }
}

/** Live operations mode asks the server more often than the quiet default (design States-2: every 15 s). */
export const LIVE_OPS_INTERVAL_MS = 15_000;
export const isLiveOpsTopic = (topic: string) => topic.endsWith(":ops");
export const liveOpsTopic = (
  workspaceId: string,
  eventId: string,
  entity: string,
) => `workspace:${workspaceId}:event:${eventId}:${entity}:ops`;

/**
 * The transport that works against today's API: a periodic "may have changed" hint per topic,
 * paused while the tab is hidden or the browser offline and fired once on resume. A push transport
 * replaces it behind the same interface.
 */
export function pollingTransport({
  intervalMs = 60_000,
  opsIntervalMs = LIVE_OPS_INTERVAL_MS,
}: { intervalMs?: number; opsIntervalMs?: number } = {}): RealtimeTransport {
  return {
    open(topic, deliver, setStatus) {
      const visible = () =>
        typeof document === "undefined" ||
        document.visibilityState === "visible";
      const online = () =>
        typeof navigator === "undefined" || navigator.onLine !== false;
      const sync = () => setStatus(online() ? "polling" : "offline");
      const hint = () => {
        sync();
        if (visible() && online()) deliver({ topic, kind: "poll" });
      };
      sync();
      const timer = setInterval(
        hint,
        isLiveOpsTopic(topic) ? opsIntervalMs : intervalMs,
      );
      const resume = () => {
        if (visible()) hint();
      };
      document.addEventListener?.("visibilitychange", resume);
      window.addEventListener?.("online", hint);
      window.addEventListener?.("offline", sync);
      return () => {
        clearInterval(timer);
        document.removeEventListener?.("visibilitychange", resume);
        window.removeEventListener?.("online", hint);
        window.removeEventListener?.("offline", sync);
      };
    },
  };
}

/** A transport driven by hand: tests, and screens demonstrating a feed before a channel exists. */
export function manualTransport() {
  const open = new Map<
    string,
    {
      deliver: (event: RealtimeEvent) => void;
      setStatus: (s: ConnectionStatus) => void;
    }[]
  >();
  const transport: RealtimeTransport = {
    open(topic, deliver, setStatus) {
      const slot = { deliver, setStatus };
      open.set(topic, [...(open.get(topic) ?? []), slot]);
      setStatus("live");
      return () => {
        open.set(
          topic,
          (open.get(topic) ?? []).filter((item) => item !== slot),
        );
      };
    },
  };
  return {
    transport,
    emit(topic: string, kind?: string) {
      for (const slot of open.get(topic) ?? []) slot.deliver({ topic, kind });
    },
    setStatus(topic: string, status: ConnectionStatus) {
      for (const slot of open.get(topic) ?? []) slot.setStatus(status);
    },
    openTopics: () =>
      [...open].filter(([, slots]) => slots.length > 0).map(([t]) => t),
  };
}
