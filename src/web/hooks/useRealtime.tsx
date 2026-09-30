import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import { useQueryClient, type QueryKey } from "@tanstack/react-query";
import {
  type ConnectionStatus,
  type RealtimeEvent,
  type RealtimeHub,
} from "../lib/realtime";

const HubContext = createContext<RealtimeHub | null>(null);

/** Supplies the session's hub. Without one (tests, embeds) every realtime hook is a no-op. */
export function RealtimeProvider({
  hub,
  children,
}: {
  hub: RealtimeHub;
  children: ReactNode;
}) {
  return <HubContext value={hub}>{children}</HubContext>;
}

export function useRealtimeHub(): RealtimeHub | null {
  return useContext(HubContext);
}

/** Run `handler` when a hint arrives for `topic` while this component is mounted and `enabled`. */
export function useRealtime(
  topic: string | null,
  handler: (event: RealtimeEvent) => void,
  enabled = true,
) {
  const hub = useRealtimeHub();
  const latest = useRef(handler);
  latest.current = handler;
  useEffect(() => {
    if (!hub || !topic || !enabled) return;
    return hub.subscribe(topic, (event) => latest.current(event));
  }, [hub, topic, enabled]);
}

/**
 * The standard consumer: a hint refetches the given server-state query. The hint carries no data,
 * so what the user sees is always what the server just authorized (lib/realtime.ts).
 */
export function useRealtimeInvalidate(
  topic: string | null,
  queryKey: QueryKey,
  enabled = true,
) {
  const client = useQueryClient();
  useRealtime(
    topic,
    () => void client.invalidateQueries({ queryKey }),
    enabled,
  );
}

export function useConnectionStatus(topic: string | null): ConnectionStatus {
  const hub = useRealtimeHub();
  return useSyncExternalStore(
    (listener) => (hub ? hub.onChange(listener) : () => {}),
    () => (hub && topic ? hub.status(topic) : "idle"),
    () => "idle",
  );
}
