import { useState } from "react";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { useLoad } from "../../hooks/useLoad";
import { describeProblem } from "../../lib/api";
import {
  lockedReason,
  preferencesUrl,
  setPreference,
  type NotificationPreferences as Preferences,
} from "../../lib/notifications";

/**
 * A person's own choices about which notifications reach them by email, for one workspace. The
 * in-app inbox copy and essential notices are shown as fixed: nothing is ever lost by choosing.
 * Each change is saved at once and the list is replaced by the server's answer.
 */
export function NotificationPreferences({
  workspaceId,
}: {
  workspaceId: string;
}) {
  const load = useLoad<Preferences>(preferencesUrl(workspaceId), {
    describe: describeProblem,
  });
  const [busy, setBusy] = useState("");
  const [problem, setProblem] = useState("");
  const [saved, setSaved] = useState("");

  async function choose(
    category: string,
    channel: string,
    label: string,
    enabled: boolean,
  ) {
    setBusy(`${category}:${channel}`);
    setProblem("");
    setSaved("");
    try {
      const next = await setPreference(workspaceId, category, channel, enabled);
      load.update(() => next);
      setSaved(`${label} ${enabled ? "on" : "off"}.`);
    } catch (error) {
      setProblem(error instanceof Error ? error.message : "That did not save.");
    } finally {
      setBusy("");
    }
  }

  if (load.error)
    return <ErrorState message={load.error.message} onRetry={load.reload} />;
  if (!load.data) return <LoadingState label="Loading notification choices…" />;
  return (
    <section aria-label="Notification preferences" className="cx-notifications">
      <p className="cx-field__hint">
        Choose what is also sent to your email. Everything stays in your inbox
        here whatever you choose.
      </p>
      {load.data.categories.map((category) => (
        <fieldset key={category.category}>
          <legend>{category.label}</legend>
          <p className="cx-field__hint">{category.description}</p>
          {category.channels.map((channel) => (
            <label key={channel.channel} className="cx-notifications__choice">
              <input
                type="checkbox"
                checked={channel.enabled}
                disabled={
                  channel.locked ||
                  busy === `${category.category}:${channel.channel}`
                }
                onChange={(event) =>
                  void choose(
                    category.category,
                    channel.channel,
                    `${category.label}: ${channel.label}`,
                    event.target.checked,
                  )
                }
              />{" "}
              {channel.label}
              {channel.locked ? (
                <span className="cx-muted">
                  {" "}
                  · {lockedReason(category, channel)}
                </span>
              ) : (
                !channel.chosen && <span className="cx-muted"> · default</span>
              )}
            </label>
          ))}
        </fieldset>
      ))}
      {problem && <p role="alert">{problem}</p>}
      {saved && <p role="status">{saved}</p>}
    </section>
  );
}
