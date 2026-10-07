import { useEffect, useMemo, useState } from "react";
import { useQueries } from "@tanstack/react-query";
import { apiRequest } from "../lib/api";
import { entityBase, entityUrl, useEntityCatalogue } from "../lib/entityQuery";
import { SEARCH_TARGETS } from "../lib/searchTargets";

export const MIN_QUERY = 2;
export const PER_ENTITY = 5;
const DEBOUNCE_MS = 200;

export type EntityHit = {
  id: string;
  label: string;
  detail: string;
  view: string;
  section?: string;
};
export type EntityGroup = {
  key: string;
  nouns: string;
  hits: EntityHit[];
  total: number;
  /** This entity could not be searched (the others still are). */
  failed: boolean;
};

type Row = { id: string } & Record<string, unknown>;
type Page = { total: number; rows: Row[] };

/** A value that follows `value` once it has stopped changing for `ms`. */
function useDebounced<T>(value: T, ms: number): T {
  const [settled, setSettled] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setSettled(value), ms);
    return () => clearTimeout(timer);
  }, [value, ms]);
  return settled;
}

/**
 * Search the records of the selected event through the universal query engine. Only the entities
 * the server offers this person (their own catalogue) are asked, each with one `contains` filter on
 * its label field; the server authorizes and filters, nothing is filtered here. Reads go through
 * the server-state layer, so typing is debounced, a newer query cancels the one in flight and a
 * repeated query is answered from cache. The typed text is never put in a URL.
 */
export function useGlobalSearch({
  workspaceId,
  eventId,
  query,
}: {
  workspaceId: string;
  eventId: string;
  query: string;
}) {
  const typed = query.trim();
  const text = useDebounced(typed, DEBOUNCE_MS);
  const ready = workspaceId !== "" && eventId !== "";
  const active = typed.length >= MIN_QUERY && ready;
  const base = ready ? entityBase(workspaceId, eventId) : null;
  const catalogue = useEntityCatalogue(active ? base : null);
  const offered = useMemo(
    () =>
      (Array.isArray(catalogue.data) ? catalogue.data : []).filter(
        (entity) => SEARCH_TARGETS[entity.key],
      ),
    [catalogue.data],
  );
  const searching = active && text.length >= MIN_QUERY && base !== null;
  const results = useQueries({
    queries: offered.map((entity) => {
      const target = SEARCH_TARGETS[entity.key];
      const url = entityUrl(base ?? "", entity.key, {
        columns: [target.labelField, target.detailField].filter(
          Boolean,
        ) as string[],
        sort: target.labelField,
        limit: PER_ENTITY,
        filter: { field: target.labelField, op: "contains", value: text },
      });
      return {
        queryKey: ["global-search", url],
        queryFn: ({ signal }: { signal: AbortSignal }) =>
          apiRequest<Page>(url, { signal }),
        enabled: searching,
        staleTime: 30_000,
        retry: false,
      };
    }),
  });
  const groups: EntityGroup[] = searching
    ? offered.map((entity, at) => {
        const target = SEARCH_TARGETS[entity.key];
        const result = results[at];
        const page = result?.data;
        return {
          key: entity.key,
          nouns: target.nouns,
          total: page?.total ?? 0,
          failed: !!result?.isError,
          hits: (page?.rows ?? []).map((row) => ({
            id: row.id,
            label: String(row[target.labelField] ?? ""),
            detail: target.detailField
              ? String(row[target.detailField] ?? "")
              : "",
            view: target.view,
            section: target.section,
          })),
        };
      })
    : [];
  return {
    groups,
    // still typing, loading the catalogue, or any entity read in flight
    pending:
      active &&
      (typed !== text ||
        catalogue.loading ||
        results.some((result) => result.isPending && result.isFetching)),
    active,
  };
}
