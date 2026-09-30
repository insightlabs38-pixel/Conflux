import { PersonRow, type PersonIdentity } from "../../components/Person";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useUrlParam } from "../../lib/urlState";
import { appHref, routes } from "../../lib/routes";
import { apiJson, describeProblem } from "../../lib/api";
import { useLoad } from "../../hooks/useLoad";

type Member = {
  user_public_id: string;
  username: string;
  role: string;
  identity?: PersonIdentity;
};
type Team = { public_id: string; name: string; members: Member[] };
type Status = { team: Team | null; my_role: string | null };
type Invite = {
  public_id: string;
  token: string;
  max_uses: number;
  use_count: number;
  expires_at: string | null;
};

function inviteUrl(
  workspaceId: string,
  eventId: string,
  token: string,
): string {
  if (typeof window === "undefined") return token;
  const query = new URLSearchParams({ event: eventId, invite: token });
  return `${window.location.origin}${appHref(routes.workspace(workspaceId, "team"))}?${query}`;
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

export function TeamPanel({
  workspaceId,
  eventId,
  onTeamChange,
}: {
  workspaceId: string;
  eventId: string;
  onTeamChange?: () => void;
}) {
  // `invite` is a single-use entry token (lib/urlState.ts): read once, removed once redeemed.
  const [inviteParam, setInviteParam] = useUrlParam("invite");
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/`;
  const [redeemToken, setRedeemToken] = useState(inviteParam);
  const [teamName, setTeamName] = useState("");
  const [actionError, setActionError] = useState("");
  const [busy, setBusy] = useState(false);
  const teamFingerprint = useRef<string | null>(null);

  const team = useLoad<Status>(base + "my-team/", {
    describe: describeProblem,
  });
  const status = team.data;
  const captain = !!status?.team && status.my_role === "captain";
  const inviteLoad = useLoad<Invite[]>(
    captain ? base + "my-team/invites/" : null,
    {
      describe: describeProblem,
    },
  );
  const invites = captain ? (inviteLoad.data ?? []) : [];
  const error =
    actionError || team.error?.message || inviteLoad.error?.message || "";

  async function refresh() {
    await Promise.all([team.reload(), inviteLoad.reload()]);
  }

  // Tell the parent when membership actually changes (joined, left, role changed).
  useEffect(() => {
    if (!status) return;
    const fingerprint = `${status.team?.public_id ?? ""}:${status.my_role ?? ""}`;
    if (teamFingerprint.current !== fingerprint) {
      teamFingerprint.current = fingerprint;
      onTeamChange?.();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setActionError("");
    try {
      await action();
    } catch (cause) {
      setActionError(message(cause));
    } finally {
      setBusy(false);
    }
  }

  function createTeam(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (!teamName.trim()) throw new Error("Team name is required.");
      await apiJson(base + "my-team/", "POST", { name: teamName.trim() });
      setTeamName("");
      await refresh();
    });
  }

  function redeemInvite(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (!redeemToken.trim()) throw new Error("Invite token is required.");
      await apiJson(base + "team-invites/redeem/", "POST", {
        token: redeemToken.trim(),
      });
      setRedeemToken("");
      setInviteParam("", { replace: true });
      await refresh();
    });
  }

  function leaveTeam() {
    void run(async () => {
      await apiJson(base + "my-team/leave/", "POST");
      await refresh();
    });
  }

  function createInvite() {
    void run(async () => {
      await apiJson(base + "my-team/invites/", "POST", { max_uses: 1 });
      await refresh();
    });
  }

  function revokeInvite(inviteId: string) {
    void run(async () => {
      await apiJson(base + `my-team/invites/${inviteId}/`, "DELETE");
      await refresh();
    });
  }

  function transferCaptain(userPublicId: string) {
    void run(async () => {
      await apiJson(base + "my-team/transfer-captain/", "POST", {
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
        <article className="cx-team-workspace">
          <h3>{status.team.name}</h3>
          <p>Your role: {status.my_role}</p>
          <ul className="cx-team-roster" aria-label="Team members">
            {status.team.members.map((member) => (
              <li key={member.user_public_id}>
                <PersonRow
                  person={member.identity}
                  fallback={member.username}
                  role={member.role}
                >
                  {status.my_role === "captain" &&
                    member.role !== "captain" && (
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => transferCaptain(member.user_public_id)}
                      >
                        Make captain
                      </button>
                    )}
                </PersonRow>
              </li>
            ))}
          </ul>
          <button type="button" disabled={busy} onClick={leaveTeam}>
            Leave team
          </button>

          {status.my_role === "captain" && (
            <section className="cx-team-invites" aria-label="Invite links">
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
        <section className="cx-team-empty" aria-label="No team yet">
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
