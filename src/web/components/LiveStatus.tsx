import { useEffect, useState } from "react";
import { useConnectionStatus } from "../hooks/useRealtime";
import { dataAge, describeHealth } from "../lib/liveOps";
import { LIVE_OPS_INTERVAL_MS } from "../lib/realtime";

/**
 * The health line of a list in live operations mode: connection word, why, and how old the data is.
 * Only a change of connection is announced (polite); the ticking age is not, so it never chatters.
 */
export function LiveStatus({
  topic,
  updatedAt,
}: {
  topic: string;
  updatedAt: number | null;
}) {
  const status = useConnectionStatus(topic);
  const health = describeHealth(status, LIVE_OPS_INTERVAL_MS / 1000);
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  return (
    <div className="cx-live" data-tone={health.tone}>
      <span className="cx-live__state" role="status" aria-live="polite">
        <span className="cx-live__dot" aria-hidden="true" />
        Live operations · {health.word}
      </span>
      <span className="cx-live__detail">{health.detail}</span>
      <span className="cx-live__age">{dataAge(now, updatedAt)}</span>
    </div>
  );
}
