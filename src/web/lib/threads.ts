import { apiJson } from "./api";

/**
 * The client half of threads (PD-F002-B01-T07): comments on one subject for one closed audience.
 * Who may read or write is the server's decision (the subject's registration); the client only
 * names the subject and the audience and shows what it is given. Text is plain: it is rendered as
 * text and never interpreted.
 */
export type Audience =
  "organizers" | "judges" | "participants" | "project_team" | "public";

export type ThreadComment = {
  public_id: string;
  author: { public_id: string; username: string };
  body: string;
  removed: boolean;
  edited: boolean;
  mentions: string[];
  created_at: string;
  can_edit: boolean;
  can_remove: boolean;
  replies: ThreadComment[];
};

export type Thread = {
  subject: { type: string; id: string; label: string };
  audience: Audience;
  can_post: boolean;
  total: number;
  comments: ThreadComment[];
};

export const MAX_BODY = 4000;

export type Subject = {
  workspaceId: string;
  eventId: string;
  type: string;
  id: string;
  audience: Audience;
};

const eventBase = (workspaceId: string, eventId: string) =>
  `/api/v1/workspaces/${workspaceId}/events/${eventId}/`;
export const threadUrl = (s: Subject) =>
  `${eventBase(s.workspaceId, s.eventId)}threads/${s.type}/${encodeURIComponent(s.id)}/${s.audience}/`;
const commentUrl = (s: Subject, id: string) =>
  `${eventBase(s.workspaceId, s.eventId)}thread-comments/${id}/`;

export const postComment = (s: Subject, body: string, parent?: string) =>
  apiJson<ThreadComment>(threadUrl(s), "POST", {
    body,
    ...(parent ? { parent } : {}),
  });
export const editComment = (s: Subject, id: string, body: string) =>
  apiJson<ThreadComment>(commentUrl(s, id), "PATCH", { body });
export const removeComment = (s: Subject, id: string) =>
  apiJson<ThreadComment>(commentUrl(s, id), "DELETE");

/** Usernames of everyone who has written in the thread: people known to be able to read it. */
export function knownPeople(thread: Thread): string[] {
  const names = new Set<string>();
  const walk = (comments: ThreadComment[]) =>
    comments.forEach((c) => {
      if (!c.removed) names.add(c.author.username);
      walk(c.replies);
    });
  walk(thread.comments);
  return [...names].sort();
}
