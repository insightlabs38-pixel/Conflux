import { useEffect, useState } from "react";
import { Button } from "../../components/Button";

type Invitation = {
  public_id: string;
  event_name: string;
  pool_name: string;
  status: string;
};

export function JudgeInvitationInbox({ workspaceId }: { workspaceId: string }) {
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [error, setError] = useState("");
  const base = `/api/v1/workspaces/${workspaceId}/my-judge-invitations/`;

  useEffect(() => {
    let active = true;
    fetch(base, { credentials: "include" })
      .then((response) => {
        if (!response.ok) throw new Error("Could not load judge invitations.");
        return response.json() as Promise<Invitation[]>;
      })
      .then((items) => {
        if (active) setInvitations(items);
      })
      .catch((cause: unknown) => {
        if (active) setError(String(cause));
      });
    return () => {
      active = false;
    };
  }, [base]);

  async function respond(
    invitation: Invitation,
    decision: "accept" | "decline",
  ) {
    setError("");
    try {
      const response = await fetch(`${base}${invitation.public_id}/respond/`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision }),
      });
      if (!response.ok) throw new Error("Could not respond to invitation.");
      const updated = (await response.json()) as Invitation;
      setInvitations((items) =>
        items.map((item) =>
          item.public_id === updated.public_id ? updated : item,
        ),
      );
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
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
