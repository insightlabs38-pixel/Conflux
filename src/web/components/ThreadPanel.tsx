import { useState } from "react";
import { useLoad } from "../hooks/useLoad";
import { describeProblem } from "../lib/api";
import {
  MAX_BODY,
  editComment,
  knownPeople,
  postComment,
  removeComment,
  threadUrl,
  type Subject,
  type Thread,
  type ThreadComment,
} from "../lib/threads";
import { Button } from "./Button";
import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";
import { LoadingState } from "./LoadingState";

/**
 * One thread: comments, one level of replies, edit and remove, and a composer. Everything that
 * decides access lives on the server; this shows `can_post`, `can_edit` and `can_remove` as given.
 * Text is rendered as text (never as markup or links), and a removed comment shows only a notice.
 */
export function ThreadPanel({ subject }: { subject: Subject }) {
  const load = useLoad<Thread>(threadUrl(subject), {
    describe: describeProblem,
  });
  const [problem, setProblem] = useState("");
  const [busy, setBusy] = useState(false);
  const [draft, setDraft] = useState("");
  const thread = load.data;

  async function run(work: () => Promise<unknown>): Promise<boolean> {
    setBusy(true);
    setProblem("");
    try {
      await work();
      await load.reload();
      return true;
    } catch (error) {
      setProblem(error instanceof Error ? error.message : "That did not work.");
      return false;
    } finally {
      setBusy(false);
    }
  }

  if (load.error)
    return <ErrorState message={load.error.message} onRetry={load.reload} />;
  if (!thread) return <LoadingState label="Loading notes…" />;
  const people = knownPeople(thread);

  return (
    <div className="cx-thread">
      {thread.total === 0 && (
        <EmptyState title="No notes yet">
          {thread.can_post
            ? "Write the first one below."
            : "Nothing has been written here."}
        </EmptyState>
      )}
      {thread.total > thread.comments.length && (
        <p className="cx-muted">
          Showing the first {thread.comments.length} of {thread.total}.
        </p>
      )}
      <ul aria-label="Comments" className="cx-plain-list">
        {thread.comments.map((comment) => (
          <CommentItem
            key={comment.public_id}
            comment={comment}
            subject={subject}
            canPost={thread.can_post}
            people={people}
            busy={busy}
            run={run}
          />
        ))}
      </ul>
      {problem && <p role="alert">{problem}</p>}
      {thread.can_post ? (
        <Composer
          label="New note"
          draft={draft}
          setDraft={setDraft}
          busy={busy}
          people={people}
          submit="Post note"
          onSubmit={async () => {
            if (await run(() => postComment(subject, draft))) setDraft("");
          }}
        />
      ) : (
        <p className="cx-muted">
          You can read this thread but not write in it.
        </p>
      )}
    </div>
  );
}

function CommentItem({
  comment,
  subject,
  canPost,
  people,
  busy,
  run,
  isReply = false,
}: {
  comment: ThreadComment;
  subject: Subject;
  canPost: boolean;
  people: string[];
  busy: boolean;
  run: (work: () => Promise<unknown>) => Promise<boolean>;
  isReply?: boolean;
}) {
  const [mode, setMode] = useState<"" | "reply" | "edit" | "remove">("");
  const [text, setText] = useState("");
  const close = () => {
    setMode("");
    setText("");
  };
  return (
    <li>
      <p className="cx-muted">
        <strong>@{comment.author.username}</strong>{" "}
        <time dateTime={comment.created_at}>
          {new Date(comment.created_at).toLocaleString()}
        </time>
        {comment.edited ? " · edited" : ""}
      </p>
      {comment.removed ? (
        <p className="cx-muted">
          <em>This comment was removed.</em>
        </p>
      ) : (
        <p className="cx-thread__body">{comment.body}</p>
      )}
      {mode === "edit" && (
        <Composer
          label="Edit note"
          draft={text}
          setDraft={setText}
          busy={busy}
          people={people}
          submit="Save"
          onCancel={close}
          onSubmit={async () => {
            if (await run(() => editComment(subject, comment.public_id, text)))
              close();
          }}
        />
      )}
      {mode === "reply" && (
        <Composer
          label={`Reply to @${comment.author.username}`}
          draft={text}
          setDraft={setText}
          busy={busy}
          people={people}
          submit="Post reply"
          onCancel={close}
          onSubmit={async () => {
            if (await run(() => postComment(subject, text, comment.public_id)))
              close();
          }}
        />
      )}
      {mode === "remove" && (
        <p role="group" aria-label="Confirm removal">
          Remove this comment? Its text is erased and cannot be restored.{" "}
          <Button
            variant="danger"
            disabled={busy}
            onClick={async () => {
              if (await run(() => removeComment(subject, comment.public_id)))
                close();
            }}
          >
            Remove
          </Button>{" "}
          <Button variant="secondary" onClick={close}>
            Keep
          </Button>
        </p>
      )}
      {mode === "" && !comment.removed && (
        <p>
          {canPost && !isReply && (
            <Button variant="secondary" onClick={() => setMode("reply")}>
              Reply
            </Button>
          )}{" "}
          {comment.can_edit && (
            <Button
              variant="secondary"
              onClick={() => {
                setText(comment.body);
                setMode("edit");
              }}
            >
              Edit
            </Button>
          )}{" "}
          {comment.can_remove && (
            <Button variant="secondary" onClick={() => setMode("remove")}>
              Remove
            </Button>
          )}
        </p>
      )}
      {comment.replies.length > 0 && (
        <ul aria-label={`Replies to @${comment.author.username}`}>
          {comment.replies.map((reply) => (
            <CommentItem
              key={reply.public_id}
              comment={reply}
              subject={subject}
              canPost={canPost}
              people={people}
              busy={busy}
              run={run}
              isReply
            />
          ))}
        </ul>
      )}
    </li>
  );
}

function Composer({
  label,
  draft,
  setDraft,
  busy,
  people,
  submit,
  onSubmit,
  onCancel,
}: {
  label: string;
  draft: string;
  setDraft: (value: string) => void;
  busy: boolean;
  people: string[];
  submit: string;
  onSubmit: () => void;
  onCancel?: () => void;
}) {
  const empty = draft.trim() === "";
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        if (!empty && !busy) onSubmit();
      }}
    >
      <label>
        {label}
        <textarea
          value={draft}
          maxLength={MAX_BODY}
          rows={3}
          onChange={(e) => setDraft(e.target.value)}
          aria-describedby="thread-hint"
        />
      </label>
      <p id="thread-hint" className="cx-muted">
        Plain text, {draft.length}/{MAX_BODY}. Write @username to notify someone
        who can read this.
        {people.length > 0 && (
          <>
            {" "}
            Add:{" "}
            {people.map((name) => (
              <button
                key={name}
                type="button"
                className="cx-link-button"
                onClick={() =>
                  setDraft(
                    `${draft}${draft && !/\s$/.test(draft) ? " " : ""}@${name} `,
                  )
                }
              >
                @{name}
              </button>
            ))}
          </>
        )}
      </p>
      <Button variant="primary" type="submit" disabled={empty || busy}>
        {submit}
      </Button>{" "}
      {onCancel && (
        <Button variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
      )}
    </form>
  );
}
