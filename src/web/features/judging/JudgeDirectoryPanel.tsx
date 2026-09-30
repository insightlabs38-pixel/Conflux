import { PersonRow, type PersonIdentity } from "../../components/Person";
import { useState } from "react";
import { Button } from "../../components/Button";
import { apiRequest } from "../../lib/api";
import { useLoad } from "../../hooks/useLoad";

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
  const [judgeId, setJudgeId] = useState("");
  const [actionError, setActionError] = useState("");
  const base = `/api/v1/workspaces/${workspaceId}/`;
  const invitationUrl = `${base}events/${eventId}/judge-invitations/`;
  const directory = useLoad<Judge[]>(`${base}judge-directory/`, {
    describe: () => "Could not load judge directory.",
  });
  const existing = useLoad<Invitation[]>(invitationUrl, {
    describe: () => "Could not load judge invitations.",
  });
  const judges = directory.data ?? [];
  const invitations = existing.data ?? [];
  const error =
    actionError || directory.error?.message || existing.error?.message || "";

  async function invite() {
    setActionError("");
    try {
      const invitation = await apiRequest<Invitation>(invitationUrl, {
        method: "POST",
        body: { pool: poolId, judge: judgeId },
        describe: (_status, detail) => {
          const problem = (detail ?? {}) as {
            detail?: string;
            judge?: string[];
          };
          return (
            problem.detail ||
            problem.judge?.join(" ") ||
            "Could not invite judge."
          );
        },
      });
      existing.update((items) => [
        invitation,
        ...(items ?? []).filter(
          (item) => item.public_id !== invitation.public_id,
        ),
      ]);
      setJudgeId("");
    } catch (cause) {
      setActionError(cause instanceof Error ? cause.message : String(cause));
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
