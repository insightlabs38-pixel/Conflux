import { useEffect, useState } from "react";

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
  onSelect: (workspaceId: string) => void;
}) {
  const [state, setState] = useState<LoadState>("loading");
  const [workspaces, setWorkspaces] = useState<Membership[]>([]);
  const [error, setError] = useState("");

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
  }, []);

  if (state === "loading") return <p>Loading your workspaces…</p>;
  if (state === "signed-out") return <p>Sign in to see your workspaces.</p>;
  if (state === "error") return <p role="alert">{error}</p>;
  if (workspaces.length === 0)
    return <p>You are not a member of any workspace yet.</p>;

  return (
    <nav aria-label="Your workspaces">
      <ul>
        {workspaces.map((membership) => (
          <li key={membership.workspace}>
            <button
              type="button"
              onClick={() => onSelect(membership.workspace)}
            >
              {membership.workspace_name} ({membership.role})
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
}
