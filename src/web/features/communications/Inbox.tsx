import { Status } from "../../components/Status";
import { Card } from "../../components/Card";
import { useInbox } from "../../hooks/useInbox";

export function Inbox({ workspaceId }: { workspaceId: string }) {
  // the header notification center keeps this query live; a second subscriber would double the reads
  const { messages, error, markRead } = useInbox(workspaceId, { live: false });
  if (messages.length === 0 && !error) return null;

  return (
    <Card title="Inbox">
      {error && <p role="alert">{error}</p>}
      <ul>
        {messages.map((message) => (
          <li key={message.public_id}>
            {!message.read_at && <Status tone="info">new</Status>}{" "}
            <strong>{message.subject}</strong> ({message.event_name}):{" "}
            {message.body}
            {!message.read_at && (
              <>
                {" "}
                <button
                  type="button"
                  onClick={() => void markRead(message.public_id)}
                >
                  Mark read
                </button>
              </>
            )}
          </li>
        ))}
      </ul>
    </Card>
  );
}
