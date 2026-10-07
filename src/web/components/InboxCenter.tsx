import { useRef } from "react";
import { INBOX_PAGE, useInbox } from "../hooks/useInbox";
import { Icon } from "./Icon";
import { Status } from "./Status";
import { DestinationLink, useWorkspaceNavigation } from "./WorkspaceNavigation";

const SHOWN = 8;

/**
 * The notification center in the top bar: how many messages are waiting, and the latest ones to
 * read and mark read without leaving the page. It is a view of the member's inbox through the
 * existing endpoints (`useInbox`); opening it marks nothing, reading is an explicit act per message.
 * Roles with a Messages destination get a link to the full list; everyone gets one to their
 * notification preferences.
 */
export function InboxCenter() {
  const navigation = useWorkspaceNavigation();
  const {
    messages,
    unread,
    loading,
    loadError,
    actionError,
    markRead,
    reload,
  } = useInbox(navigation?.workspaceId ?? "");
  const details = useRef<HTMLDetailsElement>(null);
  if (!navigation) return null;
  const hasMessages = navigation.destinations.some(
    (item) => item.id === "messages",
  );
  const count = unread >= INBOX_PAGE ? `${INBOX_PAGE - 1}+` : String(unread);
  const label = unread
    ? `Notifications, ${count} unread`
    : "Notifications, none unread";
  const latest = messages.slice(0, SHOWN);
  return (
    <details
      ref={details}
      className="cx-inbox"
      onClick={(event) => {
        // following a link leaves the panel behind
        if (
          details.current &&
          (event.target as HTMLElement).closest(".cx-inbox__panel a")
        )
          details.current.open = false;
      }}
      onKeyDown={(event) => {
        if (event.key === "Escape" && details.current?.open) {
          event.stopPropagation();
          details.current.open = false;
          details.current.querySelector("summary")?.focus();
        }
      }}
    >
      <summary aria-label={label}>
        <Icon name="bell" size={20} />
        {unread > 0 && <span className="cx-inbox__count">{count}</span>}
      </summary>
      <div className="cx-inbox__panel">
        <p className="cx-inbox__title">Notifications</p>
        {actionError && <p role="alert">{actionError}</p>}
        {loadError && (
          <p role="alert">
            Could not load your inbox.{" "}
            <button type="button" onClick={() => void reload()}>
              Try again
            </button>
          </p>
        )}
        {loading && messages.length === 0 && <p role="status">Loading…</p>}
        {!loading && !loadError && messages.length === 0 && (
          <p role="status">You are all caught up.</p>
        )}
        <ul>
          {latest.map((message) => (
            <li
              key={message.public_id}
              className={message.read_at ? "" : "cx-inbox__unread"}
            >
              <p className="cx-inbox__subject">
                {!message.read_at && <Status tone="info">New</Status>}{" "}
                <strong>{message.subject}</strong>
              </p>
              <p className="cx-inbox__body">{message.body}</p>
              <p className="cx-inbox__meta">
                {message.event_name} ·{" "}
                {new Date(message.created_at).toLocaleString("en-US", {
                  month: "short",
                  day: "numeric",
                  hour: "numeric",
                  minute: "2-digit",
                })}
                {!message.read_at && (
                  <>
                    {" "}
                    <button
                      type="button"
                      className="cx-inbox__read"
                      onClick={() => void markRead(message.public_id)}
                    >
                      Mark read
                    </button>
                  </>
                )}
              </p>
            </li>
          ))}
        </ul>
        {messages.length > SHOWN && (
          <p className="cx-inbox__meta">
            Showing the latest {SHOWN} of {messages.length}.
          </p>
        )}
        <p className="cx-inbox__footer">
          {hasMessages && (
            <DestinationLink id="messages" className="cx-account__link">
              All messages
            </DestinationLink>
          )}
          <DestinationLink
            id="profile"
            hash="notification-preferences"
            className="cx-account__link"
          >
            Notification preferences
          </DestinationLink>
        </p>
      </div>
    </details>
  );
}
