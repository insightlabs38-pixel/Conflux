import { PersonRow, type PersonIdentity } from "../../components/Person";
import { useEffect, useState } from "react";
import { Button } from "../../components/Button";

type Judge = { judge: string; username: string; identity?: PersonIdentity };
type Invitation = {
  public_id: string;
  pool: string;
  judge: string;
  judge_username: string;
  status: string;
};

export function JudgeDirectoryPanel({
  workspaceId,
  eventId,
  poolId,
}: {
  workspaceId: string;
  eventId: string;
  poolId: string;
}) {
  const [judges, setJudges] = useState<Judge[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [judgeId, setJudgeId] = useState("");
  const [error, setError] = useState("");
  const base = `/api/v1/workspaces/${workspaceId}/`;
  const invitationUrl = `${base}events/${eventId}/judge-invitations/`;

  useEffect(() => {
    let active = true;
    Promise.all([
      fetch(`${base}judge-directory/`, { credentials: "include" }).then((r) => {
        if (!r.ok) throw new Error("Could not load judge directory.");
        return r.json() as Promise<Judge[]>;
      }),
      fetch(invitationUrl, { credentials: "include" }).then((r) => {
        if (!r.ok) throw new Error("Could not load judge invitations.");
        return r.json() as Promise<Invitation[]>;
      }),
    ])
      .then(([directory, existing]) => {
        if (active) {
          setJudges(directory);
          setInvitations(existing);
        }
      })
      .catch((cause: unknown) => {
        if (active) setError(String(cause));
      });
    return () => {
      active = false;
    };
  }, [base, invitationUrl]);

  async function invite() {
    setError("");
    try {
      const response = await fetch(invitationUrl, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pool: poolId, judge: judgeId }),
      });
      if (!response.ok) {
        const detail = (await response.json()) as {
          detail?: string;
          judge?: string[];
        };
        throw new Error(
          detail.detail || detail.judge?.join(" ") || "Could not invite judge.",
        );
      }
      const invitation = (await response.json()) as Invitation;
      setInvitations((items) => [
        invitation,
        ...items.filter((item) => item.public_id !== invitation.public_id),
      ]);
      setJudgeId("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    }
  }

  const poolInvitations = invitations.filter((item) => item.pool === poolId);
  return (
    <section aria-label="Judge invitations">
      <h4>Invite from workspace directory</h4>
      {error && <p role="alert">{error}</p>}
      <label>
        Judge{" "}
        <select
          value={judgeId}
          onChange={(event) => setJudgeId(event.target.value)}
        >
          <option value="">Choose a judge</option>
          {judges.map((judge) => (
            <option key={judge.judge} value={judge.judge}>
              {judge.identity?.display_name || judge.username}
            </option>
          ))}
        </select>
      </label>
      <Button disabled={!judgeId} onClick={() => void invite()}>
        Send invitation
      </Button>
      {judgeId &&
        judges
          .filter((item) => item.judge === judgeId)
          .map((item) => (
            <PersonRow
              key={item.judge}
              person={item.identity}
              fallback={item.username}
              role="Judge"
            />
          ))}
      {poolInvitations.length > 0 && (
        <ul>
          {poolInvitations.map((invitation) => (
            <li key={invitation.public_id}>
              {invitation.judge_username}: {invitation.status}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
