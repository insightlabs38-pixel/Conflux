import type { Explanation } from "../lib/explain";
import { ExplanationView } from "./ExplanationView";
import { Icon } from "./Icon";

/**
 * Access is the server's decision (S-DENY): this only states it. When the server explained the
 * decision (POLICY_EXPLAIN: `core/explain.py`) the reasons and where to resolve them are drawn
 * as it sent them; the browser never works out a reason of its own.
 */
export function DeniedState({
  message = "You do not have access to this page.",
  explanation,
}: {
  message?: string;
  explanation?: Explanation;
}) {
  return (
    <div className="cx-state cx-state--denied" role="alert">
      <p className="cx-state__title">
        <Icon name="lock" /> Access denied
      </p>
      <p>{message}</p>
      {explanation && (
        <ExplanationView
          explanation={explanation}
          label="Why access is denied"
        />
      )}
    </div>
  );
}
