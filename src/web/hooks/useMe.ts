import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiRequest, ApiError } from "../lib/api";
import { queryKeys } from "../lib/query";

export type Membership = {
  workspace: string;
  workspace_name?: string;
  workspace_slug?: string;
  role: string;
};
export type Me = {
  public_id?: string;
  username?: string;
  memberships?: Membership[];
};

/** `null` means signed out (401/403); other failures are errors the caller can retry. */
export async function fetchMe(signal?: AbortSignal): Promise<Me | null> {
  try {
    return await apiRequest<Me>("/api/v1/accounts/me/", {
      signal,
      describe: (status) => `Could not load your workspaces (${status}).`,
    });
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
  return useMutation({
    mutationFn: () =>
      apiRequest<void>("/api/v1/accounts/logout/", { method: "POST" }).catch(
        () => undefined,
      ),
    onSettled: () => client.resetQueries(),
  });
}

/** Call after a successful sign-in: the session changed, so drop anything cached for the old one. */
export function useSessionChanged() {
  const client = useQueryClient();
  return () => client.resetQueries();
}
