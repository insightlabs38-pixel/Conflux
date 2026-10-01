import {
  pathLabel,
  summary,
  valueText,
  type Change,
  type Diff,
  type DiffLine,
} from "../lib/versions";

const OP_LABEL: Record<Change["op"], string> = {
  added: "Added",
  removed: "Removed",
  changed: "Changed",
  moved: "Moved",
};

function Value({ value, clipped }: { value: unknown; clipped: boolean }) {
  return (
    <code className="cx-diff__value">
      {clipped && typeof value === "string" ? value : valueText(value)}
      {clipped && <span className="cx-muted"> (shortened)</span>}
    </code>
  );
}

function ChangeRow({ change }: { change: Change }) {
  return (
    <li className={`cx-diff__change cx-diff__change--${change.op}`}>
      <span className="cx-diff__op">{OP_LABEL[change.op]}</span>{" "}
      <span className="cx-diff__path">{pathLabel(change.path)}</span>
      {change.op === "moved" ? (
        <>
          {" "}
          from position {Number(change.before) + 1} to{" "}
          {Number(change.after) + 1}
        </>
      ) : (
        <div className="cx-diff__values">
          {change.op !== "added" && (
            <del>
              <span className="cx-visually-hidden">Before: </span>
              <Value value={change.before} clipped={change.clipped} />
            </del>
          )}
          {change.op === "changed" && " "}
          {change.op !== "removed" && (
            <ins>
              <span className="cx-visually-hidden">After: </span>
              <Value value={change.after} clipped={change.clipped} />
            </ins>
          )}
        </div>
      )}
    </li>
  );
}

const MARK: Record<DiffLine["op"], string> = {
  equal: " ",
  add: "+",
  remove: "-",
};

function LineRow({ line }: { line: DiffLine }) {
  const text = (
    <>
      <span className="cx-diff__no" aria-hidden="true">
        {line.before_line ?? ""}
      </span>
      <span className="cx-diff__no" aria-hidden="true">
        {line.after_line ?? ""}
      </span>
      <span aria-hidden="true">{MARK[line.op]} </span>
      {line.text}
    </>
  );
  if (line.op === "add")
    return (
      <ins className="cx-diff__line cx-diff__line--add">
        <span className="cx-visually-hidden">Added: </span>
        {text}
        {"\n"}
      </ins>
    );
  if (line.op === "remove")
    return (
      <del className="cx-diff__line cx-diff__line--remove">
        <span className="cx-visually-hidden">Removed: </span>
        {text}
        {"\n"}
      </del>
    );
  return (
    <span className="cx-diff__line">
      {text}
      {"\n"}
    </span>
  );
}

/**
 * Draws a diff the server produced (`lib/versions.ts`): structural changes for data, hunks for
 * text. It never compares anything itself. Every change says what happened in words (Added,
 * Removed, Changed, Moved) as well as by colour, and values are text nodes.
 */
export function DiffView({ diff, label }: { diff: Diff; label?: string }) {
  return (
    <div className="cx-diff" role="group" aria-label={label ?? "Differences"}>
      <p className="cx-diff__summary">{summary(diff)}</p>
      {diff.kind === "json" && diff.changes.length > 0 && (
        <ul className="cx-diff__changes">
          {diff.changes.map((change, index) => (
            <ChangeRow key={index} change={change} />
          ))}
        </ul>
      )}
      {diff.kind === "text" &&
        diff.hunks.map((hunk, index) => (
          <pre
            key={index}
            className="cx-diff__hunk cx-scroll-region"
            tabIndex={0}
            aria-label={`Lines ${hunk.lines[0]?.before_line ?? hunk.lines[0]?.after_line ?? ""} onward`}
          >
            {hunk.lines.map((line, at) => (
              <LineRow key={at} line={line} />
            ))}
          </pre>
        ))}
    </div>
  );
}
