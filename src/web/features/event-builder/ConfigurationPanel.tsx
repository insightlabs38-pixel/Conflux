import { useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { SchemaForm } from "../../components/SchemaForm";
import { apiJson, describeProblem } from "../../lib/api";
import { useLoad } from "../../hooks/useLoad";
import { validate, type Schema } from "../../lib/schema";
import { GeneratedConfiguration } from "./GeneratedConfiguration";

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
  schema: Schema;
  editable: boolean;
  lock: { code: string; message: string } | null;
  constraint: string | null;
  write: {
    method: "PATCH" | "PUT" | "POST";
    path: string;
    field: string;
    body: "partial" | "whole";
  } | null;
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
 * Send a new value through the endpoint the configuration answer names for that setting: the
 * domain endpoint validates, audits and versions it exactly as before. An endpoint that replaces
 * every input (`body: "whole"`) is read first and sent back with the one field changed.
 */
async function writeSetting(
  workspaceId: string,
  eventId: string,
  entry: Entry,
  next: unknown,
) {
  const write = entry.write!;
  const url = `/api/v1/${write.path
    .replace("{workspace}", workspaceId)
    .replace("{event}", eventId)}`;
  if (write.body === "whole") {
    const current = await apiJson<Record<string, unknown>>(url);
    delete current.updated_at;
    return apiJson(url, write.method, { ...current, [write.field]: next });
  }
  return apiJson(url, write.method, { [write.field]: next });
}

/** One setting's schema as a one-field form, so the shared form and validator apply. */
const single = (entry: Entry): Schema => ({
  type: "object",
  properties: { value: { ...entry.schema, title: entry.label } },
});

function SettingEditor({
  entry,
  timeZone,
  workspaceId,
  eventId,
  onDone,
}: {
  entry: Entry;
  timeZone: string;
  workspaceId: string;
  eventId: string;
  onDone: (saved: boolean) => void;
}) {
  const [draft, setDraft] = useState<Record<string, unknown>>({
    value: entry.value,
  });
  const [problem, setProblem] = useState("");
  const [busy, setBusy] = useState(false);
  const problems = validate(single(entry), draft);

  async function save() {
    setProblem("");
    if (problems.length > 0) return;
    setBusy(true);
    try {
      await writeSetting(workspaceId, eventId, entry, draft.value);
      onDone(true);
    } catch (error) {
      setProblem(error instanceof Error ? error.message : "That did not work.");
      setBusy(false);
    }
  }

  return (
    <form
      aria-label={`Change ${entry.label}`}
      onSubmit={(event) => {
        event.preventDefault();
        void save();
      }}
    >
      <SchemaForm
        schema={single(entry)}
        value={draft}
        onChange={setDraft}
        problems={problems}
        disabled={busy}
        timeZone={timeZone}
      />
      <Button type="submit" disabled={busy || problems.length > 0}>
        Save
      </Button>{" "}
      <Button variant="secondary" disabled={busy} onClick={() => onDone(false)}>
        Cancel
      </Button>
      {problem && <p role="alert">{problem}</p>}
    </form>
  );
}

/**
 * Every setting of the event with its value, where that value comes from and whether it can be
 * changed now: the same answer automation gets from `GET …/configuration/`. A setting that can be
 * changed has a Change control: the shared schema form over the setting's schema, saved through the
 * endpoint the answer names (so validation, audit and locks stay the domain's).
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
  const [editing, setEditing] = useState<string | null>(null);
  const timeZone =
    (data?.settings.find((e) => e.key === "event.timezone")?.value as
      string | undefined) ?? "UTC";
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
              {entry.editable &&
                entry.module_enabled &&
                editing !== entry.key && (
                  <>
                    {" "}
                    <Button
                      variant="secondary"
                      aria-label={`Change ${entry.label}`}
                      onClick={() => setEditing(entry.key)}
                    >
                      Change
                    </Button>
                  </>
                )}
              {editing === entry.key && (
                <SettingEditor
                  entry={entry}
                  timeZone={timeZone}
                  workspaceId={workspaceId}
                  eventId={eventId}
                  onDone={(saved) => {
                    setEditing(null);
                    if (saved) void load.reload();
                  }}
                />
              )}
            </li>
          ))}
        </ul>
      )}
      <GeneratedConfiguration workspaceId={workspaceId} eventId={eventId} />
    </section>
  );
}
