import type { FilterNode } from "./entityQuery";

/**
 * Month arithmetic for the calendar layout (PD-F006-B03-T01). The server places rows on UTC days
 * (`core.query.run_days`), so every day here is a UTC calendar date written `2027-03-05` and a
 * month `2027-03`; nothing depends on the browser's time zone. Weeks start on Monday.
 */
const MONTH = /^(\d{4})-(0[1-9]|1[0-2])$/;

export function isMonth(text: string): boolean {
  const found = MONTH.exec(text);
  return !!found && Number(found[1]) >= 1970 && Number(found[1]) <= 2200;
}

export function currentMonth(now: Date = new Date()): string {
  return now.toISOString().slice(0, 7);
}

/** The month `by` months from `month` (negative for earlier), or null outside the supported years. */
export function shiftMonth(month: string, by: number): string | null {
  const found = MONTH.exec(month);
  if (!found) return null;
  const at = Number(found[1]) * 12 + (Number(found[2]) - 1) + by;
  const year = Math.floor(at / 12);
  if (year < 1970 || year > 2200) return null;
  return `${String(year).padStart(4, "0")}-${String((at % 12) + 1).padStart(2, "0")}`;
}

export function monthTitle(month: string): string {
  const [year, number] = month.split("-").map(Number);
  return new Date(Date.UTC(year, number - 1, 1)).toLocaleString("en-US", {
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  });
}

export function dayTitle(day: string): string {
  return new Date(`${day}T00:00:00Z`).toLocaleString("en-US", {
    dateStyle: "long",
    timeZone: "UTC",
  });
}

export const WEEKDAYS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
] as const;

/** The weeks of a month as rows of seven cells: a date, or null before the 1st and after the last. */
export function monthWeeks(month: string): (string | null)[][] {
  const [year, number] = month.split("-").map(Number);
  const first = new Date(Date.UTC(year, number - 1, 1));
  const length = new Date(Date.UTC(year, number, 0)).getUTCDate();
  const lead = (first.getUTCDay() + 6) % 7; // Monday = 0
  const cells: (string | null)[] = [
    ...Array<null>(lead).fill(null),
    ...Array.from(
      { length },
      (_, i) => `${month}-${String(i + 1).padStart(2, "0")}`,
    ),
  ];
  while (cells.length % 7 !== 0) cells.push(null);
  return Array.from({ length: cells.length / 7 }, (_, w) =>
    cells.slice(w * 7, w * 7 + 7),
  );
}

export function nextDay(day: string): string {
  return new Date(Date.parse(`${day}T00:00:00Z`) + 86_400_000)
    .toISOString()
    .slice(0, 10);
}

/** A day as two ordinary conditions (from midnight UTC, before the next midnight), to join with AND. */
export function dayConditions(field: string, day: string): FilterNode[] {
  return [
    { field, op: "gte", value: day },
    { field, op: "lt", value: nextDay(day) },
  ];
}
