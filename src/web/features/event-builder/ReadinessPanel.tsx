import { Badge } from "../../components/Badge";
import { VisuallyHidden } from "../../components/VisuallyHidden";
import { DestinationLink } from "../../components/WorkspaceNavigation";
import type { Loaded } from "../../hooks/useLoad";
import {
  unresolvedItems,
  type Readiness,
  type ReadinessItem,
} from "../../hooks/useReadiness";

const TONE = {
  ready: "success",
  warning: "warning",
  blocked: "danger",
} as const;
const STATUS_TEXT = {
  ready: "Ready to launch",
  warning: "Can launch, with warnings",
  blocked: "Not ready: blockers remain",
} as const;

function severityTone(item: ReadinessItem): "success" | "warning" | "danger" {
  if (item.passed) return "success";
  return item.severity === "blocker" ? "danger" : "warning";
}

/**
 * The one readiness surface (PD-F001-B01-T05): what is missing before launch, each item with the
 * place to fix it. Setup and the operations center both render this from the same server list.
 * Passed checks stay collapsed so the base view shows only what needs action.
 */
export function ReadinessPanel({ load }: { load: Loaded<Readiness> }) {
  const readiness = load.data;
  if (load.error)
    return (
      <p role="alert">
        Readiness could not load.{" "}
        <button type="button" onClick={() => void load.reload()}>
          Try again
        </button>
      </p>
    );
  if (!readiness) return <p className="cx-muted">Checking readiness…</p>;
  const open = unresolvedItems(readiness);
  const passed = readiness.items.filter((item) => item.passed);
  return (
    <section aria-label="Event readiness">
      <h3>
        Launch readiness{" "}
        <Badge tone={TONE[readiness.status]}>
          {STATUS_TEXT[readiness.status]}
        </Badge>
      </h3>
      {open.length === 0 ? (
        <p>Nothing is missing. Every check passes.</p>
      ) : (
        <ul>
          {open.map((item) => (
            <li key={item.id}>
              <Badge tone={severityTone(item)}>{item.severity}</Badge>{" "}
              {item.detail}{" "}
              <DestinationLink
                id={item.fix.destination}
                section={item.fix.section || undefined}
                className="cx-inline-link"
              >
                Fix
                <VisuallyHidden> {item.id.replace(/_/g, " ")}</VisuallyHidden>
              </DestinationLink>
            </li>
          ))}
        </ul>
      )}
      <button type="button" onClick={() => void load.reload()}>
        Check again
      </button>
      {passed.length > 0 && (
        <details>
          <summary>
            {passed.length} check{passed.length === 1 ? "" : "s"} passed
          </summary>
          <ul>
            {passed.map((item) => (
              <li key={item.id}>
                <Badge tone="success">OK</Badge> {item.detail}
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
