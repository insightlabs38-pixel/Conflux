import { apiJson } from "./api";

/**
 * The client half of the event timeline (PD-F002-B01-T08). The server derives and orders the items,
 * judges the conflicts and says, per item, which existing domain endpoint changes its times
 * (`write`); the client shows event-zone wall times and sends changes to that endpoint. A time is
 * never saved here and a conflict never blocks anything: conflicts are advice.
 */
export type TimelineWrite = {
  method: "PATCH" | "PUT" | "POST";
  path: string;
  fields: { starts_at: string; ends_at: string };
  extra: Record<string, unknown>;
};

export type TimelineItem = {
  kind: string;
  kind_label: string;
  key: string;
  label: string;
  starts_at: string;
  ends_at: string | null;
  /** Event-zone ISO strings with their offset, e.g. 2027-03-06T10:00:00-05:00. */
  local_starts_at: string;
  local_ends_at: string | null;
  dst_note: string | null;
  source: Record<string, unknown>;
  editable: boolean;
  write: TimelineWrite | null;
  note: string;
};

export type TimelineConflict = {
  code: string;
  severity: "advisory";
  message: string;
  items: string[];
};

export type Timeline = {
  event: string;
  timezone: string;
  total: number;
  items: TimelineItem[];
  conflicts: TimelineConflict[];
};

export function timelineUrl(
  workspaceId: string,
  eventId: string,
  params: { from?: string; to?: string; kinds?: string[]; limit?: number } = {},
): string {
  const query = new URLSearchParams();
  if (params.from) query.set("from", params.from);
  if (params.to) query.set("to", params.to);
  if (params.kinds?.length) query.set("kinds", params.kinds.join(","));
  if (params.limit) query.set("limit", String(params.limit));
  const text = query.toString();
  return `/api/v1/workspaces/${workspaceId}/events/${eventId}/timeline/${text ? `?${text}` : ""}`;
}

/** Wall-clock parts of a server local ISO string, read as written (the event's own clock). */
export function wall(local: string): { date: string; time: string } {
  return { date: local.slice(0, 10), time: local.slice(11, 16) };
}

/** `<input type="datetime-local">` value for a server local ISO string. */
export const toLocalInput = (local: string): string => local.slice(0, 16);

/** A calendar day as a heading ("Saturday, March 6"), independent of the viewer's zone. */
export function dayHeading(date: string): string {
  const [y, m, d] = date.split("-").map(Number);
  return new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  }).format(new Date(Date.UTC(y, m - 1, d)));
}

/** "10:00", "10:00–11:30", or with the day when it spans days ("Mar 1 07:00 – Mar 5 07:00"). */
export function rangeText(item: TimelineItem): string {
  const start = wall(item.local_starts_at);
  if (!item.local_ends_at) return start.time;
  const end = wall(item.local_ends_at);
  if (start.date === end.date) return `${start.time}–${end.time}`;
  const short = (date: string) => dayHeading(date).split(", ")[1];
  return `${short(start.date)} ${start.time} – ${short(end.date)} ${end.time}`;
}

/** Minutes the zone is ahead of UTC at one instant. */
function offsetMinutes(utcMs: number, timeZone: string): number {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hourCycle: "h23",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).formatToParts(new Date(utcMs));
  const n = (type: string) => Number(parts.find((p) => p.type === type)!.value);
  const asUtc = Date.UTC(
    n("year"),
    n("month") - 1,
    n("day"),
    n("hour"),
    n("minute"),
    n("second"),
  );
  return (asUtc - Math.floor(utcMs / 1000) * 1000) / 60000;
}

/**
 * The UTC instant of a wall time in the event's zone (`YYYY-MM-DDTHH:mm`). A time that does not
 * exist (the hour skipped when clocks go forward) lands just after the gap; a time that happens
 * twice (clocks go back) is read as the first one.
 */
export function zonedToUtc(local: string, timeZone: string): string {
  const [date, time] = local.split("T");
  const [y, m, d] = date.split("-").map(Number);
  const [hh, mm] = time.split(":").map(Number);
  const wallMs = Date.UTC(y, m - 1, d, hh, mm);
  const day = 86400000;
  // The offsets in force a day before and a day after bracket any transition near this time.
  const offsets = new Set([
    offsetMinutes(wallMs - day, timeZone),
    offsetMinutes(wallMs + day, timeZone),
  ]);
  const valid = [...offsets]
    .map((offset) => wallMs - offset * 60000)
    .filter(
      (instant) =>
        instant + offsetMinutes(instant, timeZone) * 60000 === wallMs,
    )
    .sort((a, b) => a - b);
  // No valid reading means the wall time falls in the skipped hour: use the offset from before it.
  const before = offsetMinutes(wallMs - day, timeZone);
  return new Date(valid[0] ?? wallMs - before * 60000).toISOString();
}

/** Send new times to the domain endpoint the item names; the domain validates and audits. */
export function saveTimes(
  workspaceId: string,
  eventId: string,
  item: TimelineItem,
  startsAt: string,
  endsAt: string | null,
) {
  const write = item.write;
  if (!write) throw new Error("These times cannot be changed here.");
  const path = `/api/v1/${write.path
    .replace("{workspace}", workspaceId)
    .replace("{event}", eventId)}`;
  return apiJson<unknown>(path, write.method, {
    ...write.extra,
    [write.fields.starts_at]: startsAt,
    ...(endsAt !== null ? { [write.fields.ends_at]: endsAt } : {}),
  });
}
