import type { ReactNode } from "react";
import { safeHref, type RichNode, type RichTree } from "../lib/rich";

/**
 * Draws a rich-content tree (`lib/rich.ts`). Only the node set the server can produce is drawn;
 * anything else is skipped, and every piece of text goes in as a React text child, so content
 * from participants cannot become markup. A link is drawn as a link only on a safe scheme.
 */
export function RichDoc({
  tree,
  label,
}: {
  tree: RichTree;
  /** Names the region when it stands alone (a preview); omit inside a page that already does. */
  label?: string;
}) {
  return (
    <div
      className="cx-rich"
      role={label ? "region" : undefined}
      aria-label={label}
    >
      {nodes(tree.children)}
    </div>
  );
}

function nodes(list: RichNode[]): ReactNode[] {
  return list.map((node, index) => <Node key={index} node={node} />);
}

function Node({ node }: { node: RichNode }): ReactNode {
  switch (node.type) {
    case "text":
      return node.text;
    case "code_span":
      return <code>{node.text}</code>;
    case "break":
      return <br />;
    case "emphasis":
      return <em>{nodes(node.children)}</em>;
    case "strong":
      return <strong>{nodes(node.children)}</strong>;
    case "link":
      return safeHref(node.href) ? (
        <a href={node.href} rel="noopener noreferrer nofollow">
          {nodes(node.children)}
        </a>
      ) : (
        <>{nodes(node.children)}</>
      );
    case "paragraph":
      return <p>{nodes(node.children)}</p>;
    case "heading": {
      const Tag = `h${Math.min(Math.max(node.level, 2), 6)}` as
        "h2" | "h3" | "h4" | "h5" | "h6";
      return <Tag>{nodes(node.children)}</Tag>;
    }
    case "quote":
      return <blockquote>{nodes(node.children)}</blockquote>;
    case "list": {
      const items = nodes(node.children);
      return node.ordered ? (
        <ol start={node.start === 1 ? undefined : node.start}>{items}</ol>
      ) : (
        <ul>{items}</ul>
      );
    }
    case "item":
      return <li>{nodes(node.children)}</li>;
    case "code":
      return (
        <pre
          tabIndex={0}
          role="group"
          aria-label={node.language ? `${node.language} code` : "Code"}
        >
          <code data-language={node.language || undefined}>
            {node.tokens.map(([kind, text], index) =>
              kind && kind !== "w" ? (
                <span key={index} className={`cx-tok cx-tok-${kind}`}>
                  {text}
                </span>
              ) : (
                text
              ),
            )}
          </code>
        </pre>
      );
    case "table": {
      const head = node.children.filter(
        (row) => row.type === "row" && row.header,
      );
      const body = node.children.filter(
        (row) => row.type === "row" && !row.header,
      );
      return (
        <div
          className="cx-rich__table"
          role="region"
          tabIndex={0}
          aria-label="Table"
        >
          <table>
            {head.length > 0 && <thead>{nodes(head)}</thead>}
            {body.length > 0 && <tbody>{nodes(body)}</tbody>}
          </table>
        </div>
      );
    }
    case "row":
      return (
        <tr>
          {node.children.map((cell, index) =>
            cell.type === "cell" ? (
              <Cell key={index} node={cell} header={node.header} />
            ) : null,
          )}
        </tr>
      );
    case "rule":
      return <hr />;
    default:
      return null;
  }
}

function Cell({
  node,
  header,
}: {
  node: Extract<RichNode, { type: "cell" }>;
  header: boolean;
}) {
  const style = node.align ? { textAlign: node.align } : undefined;
  return header ? (
    <th scope="col" style={style}>
      {nodes(node.children)}
    </th>
  ) : (
    <td style={style}>{nodes(node.children)}</td>
  );
}
