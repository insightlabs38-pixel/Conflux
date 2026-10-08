import { useState } from "react";
import {
  type EntityDay,
  type EntityRow,
  type FilterNode,
} from "../lib/entityQuery";
import {
  currentMonth,
  dayConditions,
  dayTitle,
  monthTitle,
  monthWeeks,
  shiftMonth,
  WEEKDAYS,
} from "../lib/calendar";
import { BucketRows } from "./GroupedRows";
import { Button } from "./Button";
import type { GridColumn, GridDensity } from "./DataGrid";

/**
 * Rows placed on the days of one month by a date field (spec 006, PD-F006-B03-T01). The server
 * counts them per UTC day for the current filter and search; a day with rows is a button that opens
 * them beneath through the ordinary query with the day as two conditions. A real table (weekday
 * headers, one labelled button per day with rows) so it reads without sight, and days are UTC, as
 * every date in the lists is.
 */
export function CalendarLayout({
  base,
  entity,
  label,
  fieldKey,
  fieldLabel,
  month,
  onMonth,
  days,
  total,
  filter,
  search,
  sort,
  columnKeys,
  columns,
  density,
  rowLabel,
  actions,
}: {
  base: string;
  entity: string;
  label: string;
  fieldKey: string;
  fieldLabel: string;
  month: string;
  onMonth: (month: string) => void;
  days: EntityDay[];
  total: number;
  filter: FilterNode | null;
  search: string;
  sort: string;
  columnKeys: string[];
  columns: GridColumn<EntityRow>[];
  density: GridDensity;
  rowLabel?: (row: EntityRow) => string;
  actions?: (row: EntityRow) => React.ReactNode;
}) {
  const [picked, setPicked] = useState("");
  const counts = new Map(days.map((d) => [d.date, d.count]));
  const step = (by: number) => {
    const next = shiftMonth(month, by);
    if (next) {
      setPicked("");
      onMonth(next);
    }
  };
  const open = picked && counts.has(picked) ? picked : "";
  return (
    <div className="cx-calendar">
      <div className="cx-calendar__nav" role="group" aria-label="Month">
        <Button
          size="sm"
          onClick={() => step(-1)}
          disabled={!shiftMonth(month, -1)}
        >
          Previous month
        </Button>
        <h3 className="cx-calendar__title" aria-live="polite">
          {monthTitle(month)}
        </h3>
        <Button
          size="sm"
          onClick={() => step(1)}
          disabled={!shiftMonth(month, 1)}
        >
          Next month
        </Button>
        <Button
          size="sm"
          variant="ghost"
          disabled={month === currentMonth()}
          onClick={() => {
            setPicked("");
            onMonth(currentMonth());
          }}
        >
          This month
        </Button>
      </div>
      <p className="cx-muted" role="status">
        {total === 0
          ? `No ${label.toLowerCase()} by ${fieldLabel.toLowerCase()} in ${monthTitle(month)}.`
          : `${total.toLocaleString("en-US")} ${label.toLowerCase()} by ${fieldLabel.toLowerCase()} in ${monthTitle(month)}. Days are UTC.`}
      </p>
      <div
        className="cx-scroll-region"
        tabIndex={0}
        role="region"
        aria-label={`${label} by ${fieldLabel}, ${monthTitle(month)}`}
      >
        <table className="cx-calendar__table">
          <caption>
            {label} by {fieldLabel}, {monthTitle(month)}
          </caption>
          <thead>
            <tr>
              {WEEKDAYS.map((day) => (
                <th scope="col" key={day}>
                  <abbr title={day}>{day.slice(0, 3)}</abbr>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {monthWeeks(month).map((week, w) => (
              <tr key={w}>
                {week.map((day, d) => {
                  if (!day)
                    return <td key={d} className="cx-calendar__blank" />;
                  const count = counts.get(day) ?? 0;
                  const number = Number(day.slice(8));
                  return (
                    <td
                      key={d}
                      className="cx-calendar__day"
                      aria-current={day === open ? "date" : undefined}
                    >
                      {count === 0 ? (
                        <span className="cx-muted">{number}</span>
                      ) : (
                        <button
                          type="button"
                          className="cx-calendar__open"
                          aria-expanded={day === open}
                          aria-label={`${dayTitle(day)}: ${count.toLocaleString("en-US")} ${count === 1 ? "row" : "rows"}. ${day === open ? "Hide" : "Show"} them`}
                          onClick={() => setPicked(day === open ? "" : day)}
                        >
                          <span>{number}</span>
                          <strong>{count.toLocaleString("en-US")}</strong>
                        </button>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {open && (
        <section aria-label={dayTitle(open)} className="cx-calendar__rows">
          <h3 className="cx-calendar__title">{dayTitle(open)}</h3>
          <BucketRows
            key={open}
            base={base}
            entity={entity}
            label={label}
            filter={{
              and: [
                ...(filter ? [filter] : []),
                ...dayConditions(fieldKey, open),
              ],
            }}
            search={search}
            sort={sort}
            columnKeys={columnKeys}
            columns={columns}
            density={density}
            rowLabel={rowLabel}
            actions={actions}
          />
        </section>
      )}
    </div>
  );
}
