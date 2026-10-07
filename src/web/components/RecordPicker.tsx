import { useId, useState } from "react";
import { useEntityPage, type EntityRow } from "../lib/entityQuery";

/**
 * Choose one existing record by its name. The event's entity query lists the records (so the server
 * decides who may see them); the person never types or reads an id. A long list is narrowed by
 * typing part of a name, and the server does the narrowing.
 */
export function RecordPicker({
  base,
  entity,
  field,
  label,
  value,
  onChange,
  noun,
}: {
  base: string;
  entity: string;
  /** The text field that names a record. */
  field: string;
  label: string;
  /** The chosen record's id, or "" for none. */
  value: string;
  onChange: (id: string) => void;
  /** Lower-case singular used in the empty and search text, e.g. "project". */
  noun: string;
}) {
  const [search, setSearch] = useState("");
  const searchId = useId();
  const page = useEntityPage<EntityRow & Record<string, unknown>>(
    base,
    entity,
    {
      columns: [field],
      sort: field,
      limit: 100,
      filter: search.trim()
        ? { field, op: "contains", value: search.trim() }
        : undefined,
    },
  );
  const rows = page.data?.rows ?? [];
  const total = page.data?.total ?? 0;
  return (
    <span className="cx-record-picker">
      <label htmlFor={searchId}>Find {noun}</label>{" "}
      <input
        id={searchId}
        type="search"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />{" "}
      <select
        aria-label={label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">
          {page.loading
            ? "Loading…"
            : page.error
              ? `Could not load ${noun}s`
              : `Choose a ${noun}…`}
        </option>
        {rows.map((row) => (
          <option key={row.id} value={row.id}>
            {String(row[field] ?? "")}
          </option>
        ))}
      </select>
      {!page.loading && !page.error && rows.length === 0 && (
        <span role="status"> No {noun} matches.</span>
      )}
      {total > rows.length && (
        <span role="status">
          {" "}
          Showing {rows.length} of {total}; type to narrow.
        </span>
      )}
    </span>
  );
}
