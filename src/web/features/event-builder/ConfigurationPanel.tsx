import { useState } from "react";
import { Badge } from "../../components/Badge";
import { describeProblem } from "../../lib/api";
import { useLoad } from "../../hooks/useLoad";

type Entry = {
  key: string;
  module: string;
  tier: "base" | "advanced" | "expert";
  label: string;
  help: string;
  value: unknown;
  default: unknown;
  baseline: unknown;
  source: "default" | "preset" | "overridden" | "set" | "unset" | "derived";
  editable: boolean;
  lock: { code: string; message: string } | null;
  constraint: string | null;
  module_enabled: boolean;
};
type Configuration = {
  event: string;
  preset: { key: string; version: number; label: string } | null;
  settings: Entry[];
};

const SOURCE: Record<
  Entry["source"],
  { label: string; tone: "neutral" | "success" | "warning" }
> = {
  default: { label: "Default", tone: "neutral" },
  preset: { label: "From the format", tone: "success" },
  overridden: { label: "Changed", tone: "warning" },
  set: { label: "Set", tone: "success" },
  unset: { label: "Not set", tone: "neutral" },
  derived: { label: "Derived", tone: "neutral" },
};

function show(value: unknown): string {
  if (value === null || value === undefined || value === "") return "Not set";
  if (typeof value === "boolean") return value ? "On" : "Off";
  if (Array.isArray(value))
    return value.length
      ? value.map((item) => String(item).replace(/_/g, " ")).join(", ")
      : "None";
  if (typeof value === "string" && /^\d{4}-\d\d-\d\dT/.test(value))
    return (
      new Date(value).toLocaleString("en-US", {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: "UTC",
      }) + " UTC"
    );
  return String(value).replace(/_/g, " ");
}

/**
 * Every setting of the event with its value, where that value comes from and whether it can be
 * changed now: the same answer automation gets from `GET …/configuration/`. Read-only; a value is
 * changed in the panel that owns it, through the endpoint the answer names.
 */
export function ConfigurationPanel({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const [source, setSource] = useState("");
  const query = source ? `?source=${source}` : "";
  const load = useLoad<Configuration>(
    `/api/v1/workspaces/${workspaceId}/events/${eventId}/configuration/${query}`,
    { describe: describeProblem },
  );
  const data = load.data;
  return (
    <section aria-label="Defaults and overrides">
      <h3>Defaults &amp; overrides</h3>
      <p>
        What each setting is, where its value comes from
        {data?.preset
          ? ` (this event started from the ${data.preset.label} format)`
          : ""}
        , and whether it can be changed now. Automation reads the same list from
        the configuration endpoint.
      </p>
      <label>
        Show{" "}
        <select value={source} onChange={(e) => setSource(e.target.value)}>
          <option value="">All settings</option>
          <option value="overridden">Only what was changed</option>
          <option value="preset">Only values from the format</option>
          <option value="derived">Only derived values</option>
        </select>
      </label>
      {load.error && (
        <p role="alert">
          {load.error.message}{" "}
          <button type="button" onClick={() => void load.reload()}>
            Try again
          </button>
        </p>
      )}
      {!data && !load.error && <p className="cx-muted">Loading settings…</p>}
      {data && data.settings.length === 0 && <p>No settings match.</p>}
      {data && data.settings.length > 0 && (
        <ul className="cx-config-list">
          {data.settings.map((entry) => (
            <li key={entry.key}>
              <strong>{entry.label}</strong>: {show(entry.value)}{" "}
              <Badge tone={SOURCE[entry.source].tone}>
                {SOURCE[entry.source].label}
              </Badge>
              <br />
              <small className="cx-muted">
                {entry.help}
                {entry.source === "overridden" &&
                  ` Started as ${show(entry.baseline ?? entry.default)}.`}
                {!entry.module_enabled &&
                  ` Belongs to ${entry.module.replace(/_/g, " ")}, which is off.`}
                {entry.lock
                  ? ` Locked: ${entry.lock.message}`
                  : entry.constraint && ` Rule: ${entry.constraint}`}
              </small>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
