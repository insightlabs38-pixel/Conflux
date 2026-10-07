import { useId, useState } from "react";
import { useLoad } from "../hooks/useLoad";
import { describeProblem } from "../lib/api";
import { entityUrl } from "../lib/entityQuery";

export type PickerOption = { id: string; label: string };
/** Where the choices come from: the URL for what the person typed, and how to read the answer. */
export type PickerSource = {
  url: (search: string) => string;
  read: (data: unknown) => { options: PickerOption[]; total: number };
};

type EntityPage = { total: number; rows: Record<string, unknown>[] };

/**
 * Records of the universal entity query, named by one field. `idField` names the field that holds the
 * id when it is not the row's own (a team is found through its project).
 */
export function entitySource(
  base: string,
  entity: string,
  labelField: string,
  idField?: string,
): PickerSource {
  return {
    url: (search) =>
      entityUrl(base, entity, {
        columns: idField ? [labelField, idField] : [labelField],
        sort: labelField,
        limit: 100,
        filter: search.trim()
          ? { field: labelField, op: "contains", value: search.trim() }
          : idField
            ? { field: labelField, op: "is_null", value: false }
            : undefined,
      }),
    read: (data) => {
      const page = data as EntityPage;
      const seen = new Set<string>();
      const options: PickerOption[] = [];
      for (const row of page.rows ?? []) {
        const id = String(idField ? (row[idField] ?? "") : row.id);
        if (!id || seen.has(id)) continue;
        seen.add(id);
        options.push({ id, label: String(row[labelField] ?? "") });
      }
      return { options, total: page.total ?? options.length };
    },
  };
}

/** The workspace's participants by username (organizers only), for choosing a person. */
export function participantSource(workspaceId: string): PickerSource {
  return {
    url: (search) => {
      const params = new URLSearchParams({ limit: "100" });
      if (search.trim()) params.set("q", search.trim());
      return `/api/v1/workspaces/${workspaceId}/portfolio/participants/?${params}`;
    },
    read: (data) => {
      const page = data as {
        total: number;
        results: { user: string; username: string }[];
      };
      return {
        options: (page.results ?? []).map((r) => ({
          id: r.user,
          label: r.username,
        })),
        total: page.total ?? 0,
      };
    },
  };
}

/**
 * Choose one existing record by its name. The server decides who may see the records; the person
 * never types or reads an id. A long list is narrowed by typing part of a name, and the server does
 * the narrowing.
 */
export function RecordPicker({
  source,
  label,
  value,
  onChange,
  noun,
}: {
  source: PickerSource;
  label: string;
  /** The chosen record's id, or "" for none. */
  value: string;
  onChange: (id: string) => void;
  /** Lower-case singular used in the empty and search text, e.g. "project". */
  noun: string;
}) {
  const [search, setSearch] = useState("");
  const searchId = useId();
  const loaded = useLoad<unknown>(source.url(search), {
    describe: describeProblem,
  });
  const { options, total } = loaded.data
    ? source.read(loaded.data)
    : { options: [], total: 0 };
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
          {loaded.loading
            ? "Loading…"
            : loaded.error
              ? `Could not load ${noun}s`
              : `Choose a ${noun}…`}
        </option>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.label}
          </option>
        ))}
      </select>
      {!loaded.loading && !loaded.error && options.length === 0 && (
        <span role="status"> No {noun} matches.</span>
      )}
      {total > options.length && (
        <span role="status">
          {" "}
          Showing {options.length} of {total}; type to narrow.
        </span>
      )}
    </span>
  );
}
