import { useState } from "react";
import { Button } from "../../components/Button";
import { apiRequest } from "../../lib/api";
import { useLoad } from "../../hooks/useLoad";

type Invitation = {
  public_id: string;
  event_name: string;
  pool_name: string;
  status: string;
};

export function JudgeInvitationInbox({ workspaceId }: { workspaceId: string }) {
  const base = `/api/v1/workspaces/${workspaceId}/my-judge-invitations/`;
  const list = useLoad<Invitation[]>(base, {
    describe: () => "Could not load judge invitations.",
  });
  const invitations = list.data ?? [];
  const [actionError, setActionError] = useState("");
  const error = actionError || (list.error?.message ?? "");

  async function respond(
    invitation: Invitation,
    decision: "accept" | "decline",
  ) {
    setActionError("");
    try {
      const updated = await apiRequest<Invitation>(
        `${base}${invitation.public_id}/respond/`,
        {
          method: "POST",
          body: { decision },
          describe: () => "Could not respond to invitation.",
        },
      );
      list.update((items) =>
        (items ?? []).map((item) =>
          item.public_id === updated.public_id ? updated : item,
        ),
      );
    } catch (cause) {
      setActionError(cause instanceof Error ? cause.message : String(cause));
    }
  }

  const pending = invitations.filter(
    (invitation) => invitation.status === "pending",
  );
  return (
    <section aria-label="Judge invitations">
      <h3>Judge invitations</h3>
      {error && <p role="alert">{error}</p>}
      {pending.length === 0 ? (
        <p>No pending invitations.</p>
      ) : (
        <ul>
          {pending.map((invitation) => (
            <li key={invitation.public_id}>
              {invitation.event_name} · {invitation.pool_name}{" "}
              <Button onClick={() => void respond(invitation, "accept")}>
                Accept
              </Button>{" "}
              <Button onClick={() => void respond(invitation, "decline")}>
                Decline
              </Button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
