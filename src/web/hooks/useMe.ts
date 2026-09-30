import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { MembershipSummarySchema, UserSummarySchema } from "@conflux/sdk";
import { apiCall, ApiError } from "../lib/api";
import { queryKeys } from "../lib/query";
import { useRealtimeHub } from "./useRealtime";

export type Me = UserSummarySchema;
export type Membership = MembershipSummarySchema;

/** `null` means signed out (401/403); other failures are errors the caller can retry. */
export async function fetchMe(signal?: AbortSignal): Promise<Me | null> {
  try {
    return await apiCall(
      "get_api_v1_accounts_me",
      {},
      {
        signal,
        describe: (status) => `Could not load your workspaces (${status}).`,
      },
    );
  } catch (error) {
    if (
      error instanceof ApiError &&
      (error.status === 401 || error.status === 403)
    )
      return null;
    throw error;
  }
}

/** The signed-in account and its memberships, shared by every screen that needs them. */
export function useMe() {
  return useQuery({
    queryKey: queryKeys.me,
    queryFn: ({ signal }) => fetchMe(signal),
  });
}

/**
 * Sign out, then reset every cached query: server state belongs to the session that loaded it, so
 * nothing from the previous account may be shown or reused by the next one.
 */
export function useSignOut() {
  const client = useQueryClient();
  const hub = useRealtimeHub();
  return useMutation({
    mutationFn: () =>
      apiCall("post_api_v1_accounts_logout", {}).catch(() => undefined),
    onSettled: () => {
      hub?.reset();
      return client.resetQueries();
    },
  });
}

/** Call after a successful sign-in: the session changed, so drop anything cached for the old one. */
export function useSessionChanged() {
  const client = useQueryClient();
  const hub = useRealtimeHub();
  return () => {
    hub?.reset();
    return client.resetQueries();
  };
}
