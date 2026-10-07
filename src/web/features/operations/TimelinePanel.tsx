import { useMemo, useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { useLoad } from "../../hooks/useLoad";
import { describeProblem } from "../../lib/api";
import {
  dayHeading,
  rangeText,
  saveTimes,
  timelineUrl,
  toLocalInput,
  wall,
  zonedToUtc,
  type Timeline,
  type TimelineItem,
} from "../../lib/timeline";

/**
 * Everything time-boxed about the event in one ordered list, in the event's own clock: dates,
 * registration and submission windows, agenda, office hours, voting, publication and reminders.
 * Conflicts are advice and never block. A time is changed through the domain endpoint each item
 * names (which validates and audits it); this panel only sends it there.
 */
export function TimelinePanel({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const [kinds, setKinds] = useState<string[]>([]);
  const everything = useLoad<Timeline>(
    timelineUrl(workspaceId, eventId, { limit: 500 }),
    {
      describe: describeProblem,
    },
  );
  const shown = useLoad<Timeline>(
    timelineUrl(workspaceId, eventId, { kinds, limit: 500 }),
    { describe: describeProblem },
  );
  const [editing, setEditing] = useState<string | null>(null);
  // A malformed answer degrades to an empty timeline instead of crashing the tab.
  const raw = shown.data;
  const timeline = useMemo<Timeline | null>(
    () =>
      raw
        ? {
            ...raw,
            items: Array.isArray(raw.items) ? raw.items : [],
            conflicts: Array.isArray(raw.conflicts) ? raw.conflicts : [],
          }
        : null,
    [raw],
  );

  const available = useMemo(() => {
    const seen = new Map<string, string>();
    (everything.data?.items ?? []).forEach((i) =>
      seen.set(i.kind, i.kind_label),
    );
    return [...seen];
  }, [everything.data]);
  const conflicted = useMemo(
    () => new Set((timeline?.conflicts ?? []).flatMap((c) => c.items)),
    [timeline],
  );
  const days = useMemo(() => {
    const byDay = new Map<string, TimelineItem[]>();
    (timeline?.items ?? []).forEach((item) => {
      const day = wall(item.local_starts_at).date;
      byDay.set(day, [...(byDay.get(day) ?? []), item]);
    });
    return [...byDay];
  }, [timeline]);

  async function reload() {
    await Promise.all([shown.reload(), everything.reload()]);
  }

  return (
    <Card title="Timeline">
      {shown.loading && !timeline && (
        <LoadingState label="Loading the timeline…" />
      )}
      {shown.error && (
        <ErrorState message={shown.error.message} onRetry={shown.reload} />
      )}
      {timeline && (
        <>
          <p className="cx-muted">
            Times are in the event&apos;s time zone ({timeline.timezone}).
          </p>
          {available.length > 1 && (
            <fieldset>
              <legend>Show</legend>
              {available.map(([key, label]) => (
                <label key={key}>
                  <input
                    type="checkbox"
                    checked={kinds.length === 0 || kinds.includes(key)}
                    onChange={(e) => {
                      const current = kinds.length
                        ? kinds
                        : available.map(([k]) => k);
                      const next = e.target.checked
                        ? [...current, key]
                        : current.filter((k) => k !== key);
                      setKinds(next.length === available.length ? [] : next);
                    }}
                  />{" "}
                  {label}{" "}
                </label>
              ))}
            </fieldset>
          )}
          {timeline.conflicts.length > 0 && (
            <section aria-label="Scheduling conflicts">
              <h4>Worth a look</h4>
              <ul>
                {timeline.conflicts.map((conflict) => (
                  <li key={conflict.code + conflict.items.join("|")}>
                    {conflict.message}
                  </li>
                ))}
              </ul>
              <p className="cx-muted">
                These are only advice; nothing is blocked.
              </p>
            </section>
          )}
          {timeline.items.length === 0 && (
            <EmptyState title="Nothing scheduled">
              Dates, windows, sessions and reminders appear here once they are
              set.
            </EmptyState>
          )}
          {timeline.total > timeline.items.length && (
            <p className="cx-muted">
              Showing {timeline.items.length} of {timeline.total}.
            </p>
          )}
          {days.map(([day, items]) => (
            <section key={day} aria-label={dayHeading(day)}>
              <h4>{dayHeading(day)}</h4>
              <ul className="cx-plain-list">
                {items.map((item) => (
                  <li key={item.key}>
                    <p>
                      <time>{rangeText(item)}</time>{" "}
                      <strong>{item.label}</strong>{" "}
                      <Badge>{item.kind_label}</Badge>
                      {conflicted.has(item.key) && (
                        <>
                          {" "}
                          <Badge tone="warning">Conflict</Badge>
                        </>
                      )}
                    </p>
                    {item.dst_note && (
                      <p className="cx-muted">{item.dst_note}</p>
                    )}
                    {item.note && <p className="cx-muted">{item.note}</p>}
                    {item.editable && editing !== item.key && (
                      <Button
                        variant="secondary"
                        aria-label={`Change the times of ${item.label}`}
                        onClick={() => setEditing(item.key)}
                      >
                        Change times
                      </Button>
                    )}
                    {editing === item.key && (
                      <TimesForm
                        item={item}
                        timezone={timeline.timezone}
                        workspaceId={workspaceId}
                        eventId={eventId}
                        onDone={async (saved) => {
                          setEditing(null);
                          if (saved) await reload();
                        }}
                      />
                    )}
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </>
      )}
    </Card>
  );
}

function TimesForm({
  item,
  timezone,
  workspaceId,
  eventId,
  onDone,
}: {
  item: TimelineItem;
  timezone: string;
  workspaceId: string;
  eventId: string;
  onDone: (saved: boolean) => void;
}) {
  const [starts, setStarts] = useState(toLocalInput(item.local_starts_at));
  const [ends, setEnds] = useState(
    item.local_ends_at ? toLocalInput(item.local_ends_at) : "",
  );
  const [problem, setProblem] = useState("");
  const [busy, setBusy] = useState(false);
  const window = item.local_ends_at !== null;

  async function save() {
    setBusy(true);
    setProblem("");
    try {
      await saveTimes(
        workspaceId,
        eventId,
        item,
        zonedToUtc(starts, timezone),
        window && ends ? zonedToUtc(ends, timezone) : null,
      );
      onDone(true);
    } catch (error) {
      setProblem(error instanceof Error ? error.message : "That did not work.");
      setBusy(false);
    }
  }

  return (
    <form
      aria-label={`Times of ${item.label}`}
      onSubmit={(event) => {
        event.preventDefault();
        void save();
      }}
    >
      <label>
        {window ? "Starts" : "At"}{" "}
        <input
          type="datetime-local"
          required
          value={starts}
          onChange={(e) => setStarts(e.target.value)}
        />
      </label>{" "}
      {window && (
        <label>
          Ends{" "}
          <input
            type="datetime-local"
            required
            value={ends}
            onChange={(e) => setEnds(e.target.value)}
          />
        </label>
      )}{" "}
      <span className="cx-muted">({timezone})</span>{" "}
      <Button variant="primary" type="submit" disabled={busy}>
        Save
      </Button>{" "}
      <Button variant="secondary" disabled={busy} onClick={() => onDone(false)}>
        Cancel
      </Button>
      {problem && <p role="alert">{problem}</p>}
    </form>
  );
}
