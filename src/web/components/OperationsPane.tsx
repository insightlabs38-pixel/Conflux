import { useId } from "react";
import { useLocation } from "react-router";
import { useInbox } from "../hooks/useInbox";
import { useRealtime } from "../hooks/useRealtime";
import { actionWords, ago, useRecentActions } from "../hooks/useRecentActions";
import { useReadiness } from "../hooks/useReadiness";
import { useMe } from "../hooks/useMe";
import { liveOpsTopic } from "../lib/realtime";
import {
  OPS_PANES,
  setOpsPane,
  useOpsPane,
  type OpsPane,
} from "../lib/shellPreferences";
import { useWideDisplay } from "../hooks/useWideDisplay";
import { LiveStatus } from "./LiveStatus";
import { ReadinessPanel } from "../features/event-builder/ReadinessPanel";
import { DestinationLink, useWorkspaceNavigation } from "./WorkspaceNavigation";

const NAMES: Record<OpsPane, string> = {
  attention: "Needs attention",
  actions: "Your recent actions",
  inbox: "Inbox",
};

/**
 * The second pane of operations mode (spec 005, PD-F005-B03-T03), shown beside the page from 1800px
 * and only while the person has it on. It watches one thing at a time, read-only and live: what
 * still needs attention before launch (the readiness list), the person's own latest actions (audit
 * log) or their inbox. Every panel is an existing server read; the pane owns no data and no rules.
 * Choosing what it watches is a device choice. Refreshes arrive as realtime hints (the 15 s live
 * topic) and its health line is the one the live lists use.
 */
export function OperationsHost() {
  const user = useMe().data?.public_id ?? "";
  const pane = useOpsPane(user);
  const wide = useWideDisplay();
  return wide && pane ? <OperationsPane pane={pane} /> : null;
}

function OperationsPane({ pane }: { pane: OpsPane }) {
  const navigation = useWorkspaceNavigation();
  const location = useLocation();
  const user = useMe().data?.public_id ?? "";
  const heading = useId();
  const workspaceId = navigation?.workspaceId ?? "";
  const organizer =
    navigation?.role === "organizer" || navigation?.role === "admin";
  const eventId = new URLSearchParams(location.search).get("event") ?? "";
  const offered = OPS_PANES.filter((name) => name === "inbox" || organizer);
  const shown = offered.includes(pane) ? pane : "inbox";
  const topic = liveOpsTopic(workspaceId, eventId || "none", "pane");

  const readiness = useReadiness(
    workspaceId,
    shown === "attention" ? eventId : null,
  );
  const actions = useRecentActions(
    workspaceId,
    shown === "actions" && organizer,
    12,
  );
  const inbox = useInbox(workspaceId, { live: false });
  useRealtime(topic, () => {
    if (shown === "attention") void readiness.reload();
    if (shown === "actions") void actions.reload();
    if (shown === "inbox") void inbox.reload();
  });
  const updatedAt =
    shown === "attention"
      ? (readiness.updatedAt ?? null)
      : shown === "actions"
        ? actions.updatedAt
        : inbox.updatedAt;

  return (
    <aside className="cx-ops" aria-labelledby={heading}>
      <div className="cx-ops__head">
        <h2 id={heading}>Operations</h2>
        <button type="button" onClick={() => setOpsPane(user, "")}>
          Close pane
        </button>
      </div>
      <div role="group" aria-label="Pane shows" className="cx-ops__choice">
        {offered.map((name) => (
          <button
            key={name}
            type="button"
            aria-pressed={name === shown}
            onClick={() => setOpsPane(user, name)}
          >
            {NAMES[name]}
          </button>
        ))}
      </div>
      <LiveStatus topic={topic} updatedAt={updatedAt} />
      {shown === "attention" &&
        (eventId ? (
          <ReadinessPanel load={readiness} />
        ) : (
          <p className="cx-muted">
            Choose an event to see what needs attention.
          </p>
        ))}
      {shown === "actions" &&
        (actions.failed ? (
          <p role="alert">
            Your recent actions could not load.{" "}
            <button type="button" onClick={() => void actions.reload()}>
              Try again
            </button>
          </p>
        ) : actions.actions.length === 0 ? (
          <p className="cx-muted">No recent actions.</p>
        ) : (
          <ul className="cx-ops__list">
            {actions.actions.map((action) => (
              <li key={action.public_id}>
                <span>{actionWords(action.action)}</span>
                <span className="cx-muted">{ago(action.created_at)}</span>
              </li>
            ))}
          </ul>
        ))}
      {shown === "inbox" && (
        <>
          {inbox.loadError && (
            <p role="alert">
              Could not load your inbox.{" "}
              <button type="button" onClick={() => void inbox.reload()}>
                Try again
              </button>
            </p>
          )}
          {!inbox.loading &&
            !inbox.loadError &&
            inbox.messages.length === 0 && (
              <p className="cx-muted">You are all caught up.</p>
            )}
          <ul className="cx-ops__list">
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
      )}
    </aside>
  );
}
