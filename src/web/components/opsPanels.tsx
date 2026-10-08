import { useEffect } from "react";
import { useInbox } from "../hooks/useInbox";
import { useReadiness } from "../hooks/useReadiness";
import { useRealtime } from "../hooks/useRealtime";
import { actionWords, ago, useRecentActions } from "../hooks/useRecentActions";
import { ReadinessPanel } from "../features/event-builder/ReadinessPanel";
import { registerOpsPanel, type OpsPanelContext } from "../lib/opsPanels";
import { DestinationLink, useWorkspaceNavigation } from "./WorkspaceNavigation";

/** What still needs attention before launch: the readiness list the Setup page reads. */
function Attention({ workspaceId, eventId, topic, report }: OpsPanelContext) {
  const readiness = useReadiness(workspaceId, eventId || null);
  useRealtime(topic, () => void readiness.reload());
  useEffect(
    () => report(readiness.updatedAt ?? null),
    [readiness.updatedAt, report],
  );
  return eventId ? (
    <ReadinessPanel load={readiness} />
  ) : (
    <p className="cx-muted">Choose an event to see what needs attention.</p>
  );
}

/** The person's own latest actions, from the audit log. */
function Actions({ workspaceId, organizer, topic, report }: OpsPanelContext) {
  const actions = useRecentActions(workspaceId, organizer, 12);
  useRealtime(topic, () => void actions.reload());
  useEffect(() => report(actions.updatedAt), [actions.updatedAt, report]);
  if (actions.failed)
    return (
      <p role="alert">
        Your recent actions could not load.{" "}
        <button type="button" onClick={() => void actions.reload()}>
          Try again
        </button>
      </p>
    );
  if (actions.actions.length === 0)
    return <p className="cx-muted">No recent actions.</p>;
  return (
    <ul className="cx-opspane__list">
      {actions.actions.map((action) => (
        <li key={action.public_id}>
          <span>{actionWords(action.action)}</span>
          <span className="cx-muted">{ago(action.created_at)}</span>
        </li>
      ))}
    </ul>
  );
}

/** The inbox, newest first; the header's notification center keeps the cache fresh. */
function Inbox({ workspaceId, topic, report }: OpsPanelContext) {
  const navigation = useWorkspaceNavigation();
  const inbox = useInbox(workspaceId, { live: false });
  useRealtime(topic, () => void inbox.reload());
  useEffect(() => report(inbox.updatedAt), [inbox.updatedAt, report]);
  return (
    <>
      {inbox.loadError && (
        <p role="alert">
          Could not load your inbox.{" "}
          <button type="button" onClick={() => void inbox.reload()}>
            Try again
          </button>
        </p>
      )}
      {!inbox.loading && !inbox.loadError && inbox.messages.length === 0 && (
        <p className="cx-muted">You are all caught up.</p>
      )}
      <ul className="cx-opspane__list">
        {inbox.messages.slice(0, 12).map((message) => (
          <li
            key={message.public_id}
            data-unread={!message.read_at || undefined}
          >
            <span>
              {!message.read_at && (
                <span className="cx-visually-hidden">New: </span>
              )}
              {message.subject}
            </span>
            <span className="cx-muted">{ago(message.created_at)}</span>
          </li>
        ))}
      </ul>
      {navigation?.destinations.some((item) => item.id === "messages") && (
        <DestinationLink id="messages">Open messages</DestinationLink>
      )}
    </>
  );
}

registerOpsPanel({
  id: "attention",
  label: "Needs attention",
  when: (w) => w.organizer,
  Panel: Attention,
});
registerOpsPanel({
  id: "actions",
  label: "Your recent actions",
  when: (w) => w.organizer,
  Panel: Actions,
});
registerOpsPanel({ id: "inbox", label: "Inbox", Panel: Inbox });
