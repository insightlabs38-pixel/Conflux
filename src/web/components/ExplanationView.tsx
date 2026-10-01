import {
  OUTCOME_LABEL,
  SEVERITY_LABEL,
  fixLabel,
  type Explanation,
  type Outcome,
  type Severity,
} from "../lib/explain";
import { Badge } from "./Badge";

const OUTCOME_TONE: Record<
  Outcome,
  "success" | "danger" | "warning" | "neutral"
> = {
  allowed: "success",
  blocked: "danger",
  needs_action: "warning",
  unknown: "neutral",
};
const SEVERITY_TONE: Record<Severity, "danger" | "warning" | "neutral"> = {
  blocker: "danger",
  warning: "warning",
  info: "neutral",
};

/**
 * Draws an explanation the server produced: the outcome in words (never colour alone), one
 * sentence, then each reason with its severity and, when the domain says where to resolve it,
 * where. `alert` announces a blocked outcome to assistive technology as it appears.
 */
export function ExplanationView({
  explanation,
  label,
  alert = false,
}: {
  explanation: Explanation;
  label?: string;
  alert?: boolean;
}) {
  const announce = alert && explanation.outcome === "blocked";
  return (
    <section className="cx-explain" aria-label={label ?? "Explanation"}>
      <p className="cx-explain__summary" role={announce ? "alert" : undefined}>
        <Badge tone={OUTCOME_TONE[explanation.outcome]}>
          {OUTCOME_LABEL[explanation.outcome]}
        </Badge>{" "}
        {explanation.summary}
      </p>
      {explanation.reasons.length > 0 && (
        <ul className="cx-explain__reasons">
          {explanation.reasons.map((reason, index) => (
            <li key={`${reason.code}-${index}`}>
              <Badge tone={SEVERITY_TONE[reason.severity]}>
                {SEVERITY_LABEL[reason.severity]}
              </Badge>{" "}
              {reason.message}
              {reason.fix && (
                <span className="cx-muted">
                  {" "}
                  · Resolve in {fixLabel(reason.fix)}
                </span>
              )}
            </li>
          ))}
          {explanation.truncated && (
            <li className="cx-muted">
              Showing {explanation.reasons.length} of {explanation.total}{" "}
              reasons.
            </li>
          )}
        </ul>
      )}
    </section>
  );
}
