/**
 * The client half of explanations (PD-F002-B02-T06). The server explains a decision the domain
 * already made (a policy check, event readiness, what a delete would do) in one shape
 * (`core/explain.py`); the browser only draws it. It never works out a reason itself.
 */
export type Outcome = "allowed" | "blocked" | "needs_action" | "unknown";
export type Severity = "info" | "warning" | "blocker";

export type Reason = {
  code: string;
  severity: Severity;
  message: string;
  /** Short scalar values behind the message, for tools; the message already states them. */
  facts?: Record<string, string | number | boolean | null>;
  /** Where it is resolved. */
  fix?: { destination: string; section: string | null };
};

export type Explanation = {
  outcome: Outcome;
  summary: string;
  reasons: Reason[];
  total: number;
  truncated: boolean;
};

export const OUTCOME_LABEL: Record<Outcome, string> = {
  allowed: "Allowed",
  blocked: "Blocked",
  needs_action: "Needs attention",
  unknown: "Not decided",
};

export const SEVERITY_LABEL: Record<Severity, string> = {
  info: "Note",
  warning: "Warning",
  blocker: "Blocker",
};

/** "setup › Public page" for a fix, or just the destination. */
export const fixLabel = (fix: NonNullable<Reason["fix"]>): string =>
  fix.section ? `${fix.destination} › ${fix.section}` : fix.destination;
