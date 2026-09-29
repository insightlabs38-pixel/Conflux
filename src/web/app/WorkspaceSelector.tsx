import { useCallback, useEffect, useState } from "react";
import { Button } from "../components/Button";
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

type MeResponse = {
  public_id: string;
  username: string;
  memberships: Membership[];
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

async function fetchMe(): Promise<MeResponse | null> {
  const response = await fetch("/api/v1/accounts/me/", {
    credentials: "include",
  });
  if (response.status === 401 || response.status === 403) return null;
  if (!response.ok)
    throw new Error(`Could not load your workspaces (${response.status}).`);
  return response.json();
}

export function WorkspaceSelector({
  onSelect,
}: {
  onSelect: (workspaceId: string, role: string) => void;
}) {
  const [state, setState] = useState<LoadState>("loading");
  const [workspaces, setWorkspaces] = useState<Membership[]>([]);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const reload = useCallback(() => {
    setState("loading");
    setAttempt((count) => count + 1);
  }, []);
  const signOut = useCallback(async () => {
    await fetch("/api/v1/accounts/logout/", {
      method: "POST",
      credentials: "include",
    }).catch(() => undefined);
    reload();
  }, [reload]);

  useEffect(() => {
    let active = true;
    fetchMe()
      .then((me) => {
        if (!active) return;
        if (!me) {
          setState("signed-out");
          return;
        }
        setWorkspaces(dedupeWorkspaces(me.memberships));
        setState("ready");
      })
      .catch((cause: unknown) => {
        if (!active) return;
        setError(
          cause instanceof Error
            ? cause.message
            : "Could not load your workspaces.",
        );
        setState("error");
      });
    return () => {
      active = false;
    };
  }, [attempt]);

  if (state === "loading")
    return <LoadingState label="Loading your workspaces…" />;
  if (state === "signed-out") return <SignIn onSignedIn={reload} />;
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
                <span className="cx-workspace-choice__arrow" aria-hidden="true">
                  →
                </span>
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </section>
  );
}
