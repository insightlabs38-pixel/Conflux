import { useEffect, useState, type FormEvent } from "react";

type Member = { user_public_id: string; username: string; role: string };
type Team = { public_id: string; name: string; members: Member[] };
type Status = { team: Team | null; my_role: string | null };
type Invite = {
  public_id: string;
  token: string;
  max_uses: number;
  use_count: number;
  expires_at: string | null;
};

function invitedToken(): string {
  return typeof window === "undefined"
    ? ""
    : (new URLSearchParams(window.location.search).get("invite") ?? "");
}

function inviteUrl(
  workspaceId: string,
  eventId: string,
  token: string,
): string {
  if (typeof window === "undefined") return token;
  const url = new URL(window.location.href);
  url.searchParams.set("workspace", workspaceId);
  url.searchParams.set("event", eventId);
  url.searchParams.set("invite", token);
  return url.toString();
}

function message(error: unknown): string {
  if (typeof error === "string") return error;
  if (error instanceof Error) return error.message;
  if (Array.isArray(error)) return error.map(message).join(" ");
  if (error && typeof error === "object") {
    return Object.entries(error)
      .map(([key, value]) => `${key}: ${message(value)}`)
      .join(" ");
  }
  return "Request failed.";
}

async function request<T>(
  path: string,
  method = "GET",
  body?: object,
): Promise<T> {
  const response = await fetch(path, {
    method,
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    let detail: unknown = `Request failed (${response.status}).`;
    try {
      detail = await response.json();
    } catch {
      /* Retain status message. */
    }
    throw new Error(message(detail));
  }
  return response.status === 204
    ? (undefined as T)
    : (response.json() as Promise<T>);
}

export function TeamPanel({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/`;
  const [status, setStatus] = useState<Status | null>(null);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [redeemToken, setRedeemToken] = useState(invitedToken);
  const [teamName, setTeamName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function refresh() {
    const nextStatus = await request<Status>(base + "my-team/");
    setStatus(nextStatus);
    if (nextStatus.team && nextStatus.my_role === "captain") {
      setInvites(await request<Invite[]>(base + "my-team/invites/"));
    } else {
      setInvites([]);
    }
  }

  useEffect(() => {
    let active = true;
    refresh().catch((cause: unknown) => {
      if (active) setError(message(cause));
    });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [base]);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (cause) {
      setError(message(cause));
    } finally {
      setBusy(false);
    }
  }

  function createTeam(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (!teamName.trim()) throw new Error("Team name is required.");
      await request(base + "my-team/", "POST", { name: teamName.trim() });
      setTeamName("");
      await refresh();
    });
  }

  function redeemInvite(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (!redeemToken.trim()) throw new Error("Invite token is required.");
      await request(base + "team-invites/redeem/", "POST", {
        token: redeemToken.trim(),
      });
      setRedeemToken("");
      await refresh();
    });
  }

  function leaveTeam() {
    void run(async () => {
      await request(base + "my-team/leave/", "POST");
      await refresh();
    });
  }

  function createInvite() {
    void run(async () => {
      await request(base + "my-team/invites/", "POST", { max_uses: 1 });
      await refresh();
    });
  }

  function revokeInvite(inviteId: string) {
    void run(async () => {
      await request(base + `my-team/invites/${inviteId}/`, "DELETE");
      await refresh();
    });
  }

  function transferCaptain(userPublicId: string) {
    void run(async () => {
      await request(base + "my-team/transfer-captain/", "POST", {
        user: userPublicId,
      });
      await refresh();
    });
  }

  return (
    <section aria-label="My team">
      <h2>My team</h2>
      {error && <p role="alert">{error}</p>}

      {!status ? (
        <p>Loading…</p>
      ) : status.team ? (
        <article>
          <h3>{status.team.name}</h3>
          <p>Your role: {status.my_role}</p>
          <ul aria-label="Team members">
            {status.team.members.map((member) => (
              <li key={member.user_public_id}>
                {member.username} ({member.role})
                {status.my_role === "captain" && member.role !== "captain" && (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => transferCaptain(member.user_public_id)}
                  >
                    Make captain
                  </button>
                )}
              </li>
            ))}
          </ul>
          <button type="button" disabled={busy} onClick={leaveTeam}>
            Leave team
          </button>

          {status.my_role === "captain" && (
            <section aria-label="Invite links">
              <h4>Invite links</h4>
              <ul>
                {invites.map((invite) => (
                  <li key={invite.public_id}>
                    <a href={inviteUrl(workspaceId, eventId, invite.token)}>
                      Invite link
                    </a>{" "}
                    ({invite.use_count}/{invite.max_uses} used)
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => revokeInvite(invite.public_id)}
                    >
                      Revoke
                    </button>
                  </li>
                ))}
              </ul>
              <button type="button" disabled={busy} onClick={createInvite}>
                Create invite link
              </button>
            </section>
          )}
        </article>
      ) : (
        <section aria-label="No team yet">
          <p>You are not on a team for this event yet.</p>
          <form onSubmit={createTeam}>
            <h3>Create a team</h3>
            <label>
              Team name{" "}
              <input
                value={teamName}
                onChange={(e) => setTeamName(e.target.value)}
                required
              />
            </label>
            <button disabled={busy}>Create team</button>
          </form>
          <form onSubmit={redeemInvite}>
            <h3>Join with an invite link</h3>
            <label>
              Invite token{" "}
              <input
                value={redeemToken}
                onChange={(e) => setRedeemToken(e.target.value)}
                required
              />
            </label>
            <button disabled={busy}>Join team</button>
          </form>
        </section>
      )}
    </section>
  );
}
