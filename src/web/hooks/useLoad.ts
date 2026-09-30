import { useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiRequest, orNull, serverMessage } from "../lib/api";

export type Loaded<T> = {
  data: T | null;
  error: ApiError | null;
  loading: boolean;
  /** Refetch now; resolves when the fresh answer (or failure) is in. Does nothing while `url` is null. */
  reload: () => Promise<void>;
  /** Apply a server-confirmed change (e.g. a mutation's response) to what is shown, without a refetch. */
  update: (change: (current: T | null) => T | null) => void;
};

type Options = {
  /** Message for a failed response (defaults to the server's detail). */
  describe?: (status: number, detail: unknown) => string;
  /** Statuses that mean "nothing there for you" (e.g. 404): `data` is null and there is no error. */
  absent?: number[];
};

/**
 * GET `url` (skipped while null) on the server-state layer: concurrent users of the same URL share
 * one request, it is cancelled on unmount, and it always revalidates on mount (staleTime 0) so
 * panels never show data older than their last visit. Failures surface at once with the panel's own
 * "Try again" (`reload`); there is no silent backoff retry that would delay the error state.
 * This is the default for a panel that loads one resource on mount (PD-B04-T07): do not hand-roll
 * `useEffect` + request + `useState`.
 */
export function useLoad<T>(
  url: string | null,
  { describe, absent = [] }: Options = {},
): Loaded<T> {
  const client = useQueryClient();
  const key = ["load", url, absent.join(",")];
  const query = useQuery({
    queryKey: key,
    queryFn: ({ signal }) => {
      const request = apiRequest<T>(url as string, {
        signal,
        describe:
          describe ??
          ((status, detail) =>
            detail === undefined
              ? `Request failed (${status}).`
              : serverMessage(detail)),
      });
      // A query may not resolve to undefined; "nothing" (204, null body) is null.
      return (absent.length ? orNull(request, ...absent) : request).then(
        (value) => value ?? null,
      );
    },
    enabled: url !== null,
    staleTime: 0,
    retry: false,
  });
  const failed = query.isError && !query.isFetching;
  const error = failed
    ? query.error instanceof ApiError
      ? query.error
      : new ApiError(0, serverMessage(query.error))
    : null;
  const reload = useCallback(
    () =>
      url === null ? Promise.resolve() : query.refetch().then(() => undefined),
    [query, url],
  );
  const cacheKey = key.join("\u0000");
  const update = useCallback(
    (change: (current: T | null) => T | null) =>
      client.setQueryData<T | null>(key, (current) => change(current ?? null)),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [client, cacheKey],
  );
  return {
    data: failed || url === null ? null : (query.data ?? null),
    error,
    loading: url !== null && query.isFetching,
    reload,
    update,
  };
}
