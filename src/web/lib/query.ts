import {
  QueryClient,
  type DefaultOptions,
  type QueryKey,
} from "@tanstack/react-query";
import { ApiError } from "./api";

/**
 * Server-state defaults (PD-B04-T02).
 * - Dedupe/cache: identical query keys share one request and stay fresh for `staleTime`.
 * - Retry: only failures that can succeed later (network errors, 5xx, 429) are retried, at most
 *   twice with backoff; 4xx answers (401/403/404/validation) are final and surface immediately.
 * - No refetch on window focus/reconnect by default: workspaces keep unsaved drafts, and a silent
 *   refetch must not reshuffle data under the user. Screens that want live data opt in per query.
 * - Mutations never retry automatically (they may not be idempotent).
 */
export function shouldRetry(failureCount: number, error: unknown): boolean {
  if (failureCount >= 2) return false;
  if (error instanceof ApiError)
    return error.status >= 500 || error.status === 429;
  return !(error instanceof DOMException && error.name === "AbortError");
}

export const retryDelay = (attempt: number) =>
  Math.min(500 * 2 ** attempt, 4000);

const defaults: DefaultOptions = {
  queries: {
    staleTime: 30_000,
    gcTime: 5 * 60_000,
    retry: shouldRetry,
    retryDelay,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  },
  mutations: { retry: false },
};

export function createQueryClient(overrides: DefaultOptions["queries"] = {}) {
  return new QueryClient({
    defaultOptions: {
      ...defaults,
      queries: { ...defaults.queries, ...overrides },
    },
  });
}

/** Query keys in one place so invalidation is precise and greppable. */
export const queryKeys = {
  me: ["me"] as const,
  participantEvents: (workspaceId: string) =>
    ["workspaces", workspaceId, "participant-events"] as const,
  inbox: (workspaceId: string) => ["workspaces", workspaceId, "inbox"] as const,
};

/**
 * Standard optimistic-update wrapper for a mutation over one cached list/object: applies `apply` to
 * the cached value immediately, restores the snapshot if the mutation fails, and revalidates when
 * it settles. Pass the returned callbacks to `useMutation` alongside `mutationFn`.
 */
export function optimistic<TData, TVariables>(
  client: QueryClient,
  key: QueryKey,
  apply: (current: TData | undefined, variables: TVariables) => TData,
) {
  return {
    onMutate: async (variables: TVariables) => {
      await client.cancelQueries({ queryKey: key });
      const snapshot = client.getQueryData<TData>(key);
      client.setQueryData<TData>(key, (current) => apply(current, variables));
      return { snapshot };
    },
    onError: (
      _error: unknown,
      _variables: TVariables,
      context: { snapshot: TData | undefined } | undefined,
    ) => {
      client.setQueryData(key, context?.snapshot);
    },
    onSettled: () => client.invalidateQueries({ queryKey: key }),
  };
}
