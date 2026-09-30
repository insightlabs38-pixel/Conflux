import { useState } from "react";
import { Button } from "../../components/Button";
import { useWorkspaceNavigation } from "../../components/WorkspaceNavigation";

/** Optional modules of the selected event: what is on, what holds content, and the switches. */
export function FeaturesPanel({ eventId }: { eventId: string }) {
  const navigation = useWorkspaceNavigation();
  const modules = navigation?.modules;
  const [error, setError] = useState("");
  const [pending, setPending] = useState("");
  const list = modules?.modules;
  const settled = modules?.eventId === eventId;
  if (!modules || !list) return <p className="cx-muted">Loading features…</p>;

  async function change(key: string, enabled: boolean) {
    setPending(key);
    setError("");
    try {
      await modules!.setEnabled(eventId, key, enabled);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not change.");
    } finally {
      setPending("");
    }
  }

  return (
    <section aria-label="Features">
      <h3>Features</h3>
      <p>
        Events start with the essentials. Turn on only what this event needs; a
        feature that already has content stays on.
      </p>
      {error && <p role="alert">{error}</p>}
      <ul className="cx-feature-list">
        {list.map((module) => (
          <li key={module.key}>
            <strong>{module.label}</strong>
            {module.in_use && <span> · in use</span>}
            <p>{module.description}</p>
            {module.enabled ? (
              <Button
                type="button"
                variant="secondary"
                disabled={!module.can_disable || !settled || pending !== ""}
                aria-label={`Turn off ${module.label.toLowerCase()}`}
                title={module.reason || undefined}
                onClick={() => void change(module.key, false)}
              >
                Turn off
              </Button>
            ) : (
              <Button
                type="button"
                disabled={!settled || pending !== ""}
                aria-label={`Turn on ${module.label.toLowerCase()}`}
                onClick={() => void change(module.key, true)}
              >
                Turn on
              </Button>
            )}
            {module.reason && (
              <small className="cx-muted">{module.reason}</small>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
