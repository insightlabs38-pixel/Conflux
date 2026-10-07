import { useMe, useSessionChanged, useSignOut } from "../hooks/useMe";
import { Button } from "../components/Button";
import { Icon } from "../components/Icon";
import { Avatar, PageHeader } from "../components/Foundation";
import { LoadingState } from "../components/LoadingState";
import { ErrorState } from "../components/ErrorState";
import { EmptyState } from "../components/EmptyState";
import { SignIn } from "./SignIn";

type Membership = {
  workspace: string;
  workspace_name: string;
  workspace_slug: string;
  role: string;
};

type LoadState = "loading" | "signed-out" | "ready" | "error";

// One entry per workspace even if the user holds multiple roles there (kept role is arbitrary).
export function dedupeWorkspaces(memberships: Membership[]): Membership[] {
  const byWorkspace = new Map<string, Membership>();
  for (const membership of memberships) {
    if (!byWorkspace.has(membership.workspace))
      byWorkspace.set(membership.workspace, membership);
  }
  return [...byWorkspace.values()];
}

export function WorkspaceSelector({
  onSelect,
}: {
  onSelect: (workspaceId: string, role: string) => void;
}) {
  const me = useMe();
  const signOutMutation = useSignOut();
  const sessionChanged = useSessionChanged();
  const loading = me.isPending || (me.isError && me.isFetching);
  const state: LoadState = loading
    ? "loading"
    : me.isError
      ? "error"
      : me.data === null
        ? "signed-out"
        : "ready";
  const workspaces = dedupeWorkspaces(
    (me.data?.memberships ?? []) as Membership[],
  );
  const error = me.error?.message ?? "Could not load your workspaces.";
  const reload = () => void me.refetch();
  const signOut = () => signOutMutation.mutateAsync();

  if (state === "loading")
    return <LoadingState label="Loading your workspaces…" />;
  if (state === "signed-out") return <SignIn onSignedIn={sessionChanged} />;
  if (state === "error") return <ErrorState message={error} onRetry={reload} />;
  if (workspaces.length === 0)
    return (
      <EmptyState title="You are not a member of any workspace yet.">
        <p>Ask your event organizer for an invitation to get started.</p>
      </EmptyState>
    );

  return (
    <section className="cx-workspaces">
      <PageHeader
        eyebrow="Your Conflux"
        title="Choose your workspace"
        description="Pick an event workspace to continue with your team, reviews, or event operations."
        actions={
          <Button variant="secondary" onClick={signOut}>
            Sign out
          </Button>
        }
      />
      <nav aria-label="Your workspaces">
        <ul className="cx-workspace-list">
          {workspaces.map((membership) => (
            <li key={membership.workspace}>
              <button
                type="button"
                className="cx-workspace-choice"
                aria-label={`${membership.workspace_name} (${membership.role})`}
                onClick={() => onSelect(membership.workspace, membership.role)}
              >
                <Avatar
                  name={
                    membership.workspace_name ||
                    membership.workspace_slug ||
                    "Workspace"
                  }
                />
                <span className="cx-workspace-choice__text">
                  <strong>{membership.workspace_name}</strong>
                  <span className="cx-workspace-choice__role">
                    {membership.role}
                  </span>
                </span>
                <span className="cx-workspace-choice__arrow">
                  <Icon name="arrow-right" />
                </span>
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </section>
  );
}
