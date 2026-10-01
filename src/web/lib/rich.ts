import { apiJson } from "./api";

/**
 * The client half of the rich-content primitive (PD-F002-B02-T02). The server turns source text
 * into a closed tree of nodes (`core/rich.py`); the browser only draws that tree, so no HTML from
 * a participant or an organizer is ever injected into the page. A profile names how the source is
 * read: `story` is Markdown, `page` is the organizer's allowlist HTML.
 */
export type RichProfile = "story" | "page";

type Inline =
  | { type: "text" | "code_span"; text: string }
  | { type: "break" }
  | { type: "emphasis" | "strong"; children: RichNode[] }
  | { type: "link"; href: string; children: RichNode[] };

type Block =
  | { type: "paragraph" | "quote" | "item"; children: RichNode[] }
  | { type: "heading"; level: number; children: RichNode[] }
  | { type: "list"; ordered: boolean; start: number; children: RichNode[] }
  | {
      type: "code";
      language: string;
      text: string;
      tokens: [string, string][];
    }
  | { type: "table"; children: RichNode[] }
  | { type: "row"; header: boolean; children: RichNode[] }
  | {
      type: "cell";
      align: "left" | "center" | "right" | null;
      children: RichNode[];
    }
  | { type: "rule" };

export type RichNode = Inline | Block;
export type RichTree = { type: "doc"; children: RichNode[] };

export type RichPreview = {
  profile: RichProfile;
  length: number;
  max_length: number;
  tree: RichTree;
};

export const previewUrl = (workspaceId: string) =>
  `/api/v1/workspaces/${workspaceId}/rich/preview/`;

export const previewRich = (
  workspaceId: string,
  profile: RichProfile,
  source: string,
  signal?: AbortSignal,
) =>
  apiJson<RichPreview>(
    previewUrl(workspaceId),
    "POST",
    { profile, source },
    signal,
  );

/** The same schemes the server allows: none (a relative link), http, https and mailto. */
export function safeHref(href: string): boolean {
  const match = /^\s*([a-z][a-z0-9+.-]*):/i.exec(href);
  return !match || ["http", "https", "mailto"].includes(match[1].toLowerCase());
}

/** The text of a tree without its structure (for summaries and assistive announcements). */
export function plainText(node: RichNode | RichTree): string {
  if ("text" in node && typeof node.text === "string") return node.text;
  if (node.type === "break") return "\n";
  const children = "children" in node ? node.children : [];
  const text = children.map(plainText).join("");
  return ["paragraph", "heading", "item", "row", "quote"].includes(node.type)
    ? `${text}\n`
    : text;
}
