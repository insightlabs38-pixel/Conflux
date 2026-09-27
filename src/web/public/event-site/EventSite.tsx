import { useEffect, useState } from "react";
import { AppShell } from "../../components/AppShell";
import { Badge } from "../../components/Badge";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";

type Track = { public_id: string; name: string; description: string };
type BasePrize = {
  public_id: string;
  name: string;
  description: string;
  kind: string;
  amount: string | null;
  currency: string;
  track: string | null;
};
type PublicEvent = {
  public_id: string;
  name: string;
  description: string;
  timezone: string;
  starts_at: string | null;
  ends_at: string | null;
  status: string;
  tracks: Track[];
  base_prizes: BasePrize[];
};

function formatSchedule(event: PublicEvent): string | null {
  if (!event.starts_at || !event.ends_at) return null;
  const options: Intl.DateTimeFormatOptions = {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: event.timezone,
  };
  const start = new Date(event.starts_at).toLocaleString(undefined, options);
  const end = new Date(event.ends_at).toLocaleString(undefined, options);
  return `${start} – ${end} (${event.timezone})`;
}

function formatPrize(prize: BasePrize): string {
  if (prize.kind === "cash" && prize.amount) {
    return `${prize.currency} ${prize.amount}`;
  }
  return prize.kind[0].toUpperCase() + prize.kind.slice(1);
}

/** Default public landing page for an open event: name, schedule, tracks and
 * prizes. This is a strong default (UI-003); the organizer page builder
 * (C-B12/PAGE-002) layers richer, configurable blocks on top of it later. */
export function EventSite({ eventId }: { eventId: string }) {
  const [event, setEvent] = useState<PublicEvent | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    setError("");
    fetch(`/api/v1/events/${eventId}/`)
      .then((response) => {
        if (!response.ok) throw new Error(`Event not found (${response.status}).`);
        return response.json() as Promise<PublicEvent>;
      })
      .then(setEvent)
      .catch((cause: unknown) =>
        setError(cause instanceof Error ? cause.message : "Could not load this event."),
      )
      .finally(() => setLoading(false));
  };

  useEffect(load, [eventId]);

  const schedule = event ? formatSchedule(event) : null;

  return (
    <AppShell brandAs="p">
      {loading && <LoadingState label="Loading event…" />}
      {!loading && error && <ErrorState message={error} onRetry={load} />}
      {!loading && !error && event && (
        <article aria-label={`${event.name} event page`}>
          <h1>{event.name}</h1>
          <Badge tone="info">{event.status}</Badge>
          {schedule && <p>{schedule}</p>}
          {event.description && <p>{event.description}</p>}

          <section aria-label="Tracks">
            <h2>Tracks</h2>
            {event.tracks.length === 0 ? (
              <EmptyState title="Tracks will be announced soon." />
            ) : (
              <ul>
                {event.tracks.map((track) => (
                  <li key={track.public_id}>
                    <Card title={track.name}>
                      {track.description && <p>{track.description}</p>}
                    </Card>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section aria-label="Prizes">
            <h2>Prizes</h2>
            {event.base_prizes.length === 0 ? (
              <EmptyState title="Prizes will be announced soon." />
            ) : (
              <ul>
                {event.base_prizes.map((prize) => (
                  <li key={prize.public_id}>
                    <Card title={prize.name}>
                      <p>{formatPrize(prize)}</p>
                      {prize.description && <p>{prize.description}</p>}
                    </Card>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </article>
      )}
    </AppShell>
  );
}
