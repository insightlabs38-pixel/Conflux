/**
 * The client half of the completeness contract (PD-F003-B01-T01, spec 003). The server states which
 * feature provides which of the 21 properties and checks each claim against the live system
 * (`core/features.py`); the browser only lists it. There is nothing to edit.
 */
export type ClaimState = "provided" | "not_applicable" | "planned";

export type Claim = {
  state: ClaimState;
  refs: string[];
  reason: string;
  owner: string;
};

export type CompletenessProperty = {
  key: string;
  label: string;
  /** The batch whose verifier makes it checkable. */
  batch: string;
  landed: boolean;
};

export type CompletenessProblem = {
  code: string;
  feature: string | null;
  property: string | null;
  message: string;
};

export type Lifecycle = {
  kind: "choice" | "timestamp" | "flag" | "none";
  field: string;
  initial: string[];
  terminal: string[];
  via: string[];
  note: string;
  transitions: Record<string, string[]>;
};

export type CompletenessFeature = {
  key: string;
  label: string;
  model: string;
  id_field: string;
  id_type: string | null;
  states: { value: string; label: string }[];
  lifecycle: Lifecycle | null;
  claims: Record<string, Claim>;
  /** What the system itself says per property (derived, never declared). */
  facts?: Record<string, Record<string, unknown>>;
  problems: CompletenessProblem[];
};

export type Completeness = {
  properties: CompletenessProperty[];
  features: CompletenessFeature[];
  totals: Record<string, Record<string, number>>;
  problems: CompletenessProblem[];
  ok: boolean;
};

export const completenessUrl = (workspaceId: string) =>
  `/api/v1/workspaces/${workspaceId}/completeness/`;

export const CLAIM_TEXT: Record<ClaimState | "unclaimed", string> = {
  provided: "Provided",
  not_applicable: "Not applicable",
  planned: "Planned",
  unclaimed: "Not claimed",
};

/** "Draft, Open, Closed, Archived" in the order the model lists its states. */
export const stateList = (feature: CompletenessFeature): string =>
  feature.states.map((s) => s.label).join(", ");

/** The label a state is shown with, falling back to its value. */
export function stateLabel(feature: CompletenessFeature, value: string) {
  return feature.states.find((s) => s.value === value)?.label ?? value;
}

/** "Draft → Open" lines for the transitions the code allows, in declaration order. */
export function transitionLines(feature: CompletenessFeature): string[] {
  const graph = feature.lifecycle?.transitions ?? {};
  return Object.entries(graph).flatMap(([from, targets]) =>
    targets.map(
      (to) => `${stateLabel(feature, from)} → ${stateLabel(feature, to)}`,
    ),
  );
}

const FACT_LABEL: Record<string, string> = {
  blank_refused: "A blank record is refused for",
  constraints: "Constraints",
  own_clean: "Model checks its own rules",
  readers: "Who can read",
  writers: "Who can change",
  scope_path: "Scoped through",
};

/** One derived fact as a sentence fragment: lists joined, booleans as yes or no. */
export function factText(key: string, value: unknown): string {
  const label = FACT_LABEL[key] ?? key.replace(/_/g, " ");
  if (key === "scope_path" && Array.isArray(value))
    return `${label}: ${value.length ? value.join(" → ") : "no chain"}`;
  if (Array.isArray(value))
    return `${label}: ${value.length ? value.join(", ") : "none"}`;
  if (value && typeof value === "object" && "summary" in value)
    return String((value as { summary: unknown }).summary);
  if (typeof value === "boolean") return `${label}: ${value ? "yes" : "no"}`;
  return `${label}: ${String(value)}`;
}
