import { useState, type FormEvent } from "react";
import { Button } from "../../components/Button";
import { apiJson, describeProblem } from "../../lib/api";
import { useLoad } from "../../hooks/useLoad";

export type LibraryTemplate = {
  slug: string;
  label: string;
  description: string;
  tracks: string[];
  stages: string[];
  version: number;
  duration_days: number;
  registration_mode: string;
  min_team_size: number;
  max_team_size: number;
  required_artifact_kinds: string[];
  criteria: string[];
};

const BLANK = "blank";
const REGISTRATION_LABELS: Record<string, string> = {
  open: "open",
  application: "application-based",
  invite_only: "invite-only",
};
const MODES = [
  ["open", "Open"],
  ["application", "Application review"],
  ["invite_only", "Invite only"],
] as const;

function message(error: unknown): string {
  if (typeof error === "string") return error;
  if (error instanceof Error) return error.message;
  if (Array.isArray(error)) return error.map(message).join(" ");
  if (error && typeof error === "object")
    return Object.entries(error)
      .map(([key, value]) => `${key}: ${message(value)}`)
      .join(" ");
  return "Request failed.";
}

function browserZone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

/**
 * Create an event: a name, a format, and only the decisions people commonly make on day one. The
 * format supplies a real value for everything else (end date, registration, stages, a published
 * rubric) and the address is derived from the name, so nothing here is a placeholder to clean up.
 * The server validates and audits; this form sends only what the organizer actually chose.
 */
export function CreateEvent({
  workspaceId,
  onCreated,
}: {
  workspaceId: string;
  onCreated: (eventId: string) => void;
}) {
  const base = `/api/v1/workspaces/${workspaceId}/`;
  const library = useLoad<LibraryTemplate[]>(
    `${base}event-templates/library/`,
    { describe: describeProblem },
  );
  const formats = library.data ?? [];
  const [name, setName] = useState("");
  const [chosen, setChosen] = useState<string | null>(null);
  const [startsAt, setStartsAt] = useState("");
  const [timezone, setTimezone] = useState(browserZone);
  const [mode, setMode] = useState("");
  const [minTeam, setMinTeam] = useState("");
  const [maxTeam, setMaxTeam] = useState("");
  const [isPublic, setIsPublic] = useState(false);
  const [slug, setSlug] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const formatKey = chosen ?? formats[0]?.slug ?? BLANK;
  const format = formats.find((item) => item.slug === formatKey) ?? null;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (!name.trim()) return setError("A name is required.");
    const min = minTeam === "" ? format?.min_team_size : Number(minTeam);
    const max = maxTeam === "" ? format?.max_team_size : Number(maxTeam);
    if (
      format &&
      (min === undefined ||
        max === undefined ||
        !(min >= 1 && max <= 100 && min <= max))
    )
      return setError("Team size must be between 1 and 100, smallest first.");
    setBusy(true);
    try {
      const created = format
        ? await apiJson<{ public_id: string }>(
            `${base}event-templates/library/${format.slug}/instantiate/`,
            "POST",
            {
              name: name.trim(),
              ...(slug.trim() && { slug: slug.trim() }),
              is_public: isPublic,
              timezone: timezone.trim() || "UTC",
              ...(startsAt && { starts_at: new Date(startsAt).toISOString() }),
              ...(mode && { registration_mode: mode }),
              ...(minTeam !== "" && { min_team_size: Number(minTeam) }),
              ...(maxTeam !== "" && { max_team_size: Number(maxTeam) }),
            },
          )
        : await apiJson<{ public_id: string }>(`${base}events/`, "POST", {
            name: name.trim(),
            ...(slug.trim() && { slug: slug.trim() }),
          });
      setName("");
      setSlug("");
      onCreated(created.public_id);
    } catch (cause) {
      setError(message(cause));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="cx-create-form">
      <h2>Create event</h2>
      <label>
        Name{" "}
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          autoComplete="off"
        />
      </label>
      {library.error && (
        <p role="alert">
          {library.error.message}{" "}
          <button type="button" onClick={() => void library.reload()}>
            Try again
          </button>
        </p>
      )}
      {!library.data && !library.error && (
        <p className="cx-muted">Loading formats…</p>
      )}
      <fieldset>
        <legend>Format</legend>
        {formats.map((item) => (
          <label key={item.slug} className="cx-format-choice">
            <input
              type="radio"
              name="format"
              checked={formatKey === item.slug}
              onChange={() => setChosen(item.slug)}
            />{" "}
            <strong>{item.label}</strong> — {item.description}
          </label>
        ))}
        <label className="cx-format-choice">
          <input
            type="radio"
            name="format"
            checked={formatKey === BLANK}
            onChange={() => setChosen(BLANK)}
          />{" "}
          <strong>No format</strong> — an empty draft; you set everything up
          yourself.
        </label>
      </fieldset>
      {format && (
        <>
          <p className="cx-muted" aria-live="polite">
            Stages: {format.stages.join(" → ")}.
            {format.tracks.length > 0 && (
              <> Tracks: {format.tracks.join(", ")}.</>
            )}{" "}
            Starts with: {format.duration_days}{" "}
            {format.duration_days === 1 ? "day" : "days"},{" "}
            {REGISTRATION_LABELS[format.registration_mode] ??
              format.registration_mode}{" "}
            registration, teams of {format.min_team_size}–{format.max_team_size}
            , required evidence:{" "}
            {format.required_artifact_kinds
              .map((kind) => kind.replace(/_/g, " "))
              .join(", ") || "none"}
            , published rubric: {format.criteria.join(", ")}. Still yours to
            add: judges, prize amounts
            {startsAt ? "" : " and the dates"}.
          </p>
          <div className="cx-create-form__grid">
            <label>
              Starts{" "}
              <input
                type="datetime-local"
                value={startsAt}
                onChange={(e) => setStartsAt(e.target.value)}
              />
            </label>
            <label>
              Time zone{" "}
              <input
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                autoComplete="off"
              />
            </label>
            <label>
              Registration{" "}
              <select value={mode} onChange={(e) => setMode(e.target.value)}>
                <option value="">
                  Format default (
                  {REGISTRATION_LABELS[format.registration_mode] ??
                    format.registration_mode}
                  )
                </option>
                {MODES.map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Smallest team{" "}
              <input
                type="number"
                min={1}
                max={100}
                placeholder={String(format.min_team_size)}
                value={minTeam}
                onChange={(e) => setMinTeam(e.target.value)}
              />
            </label>
            <label>
              Largest team{" "}
              <input
                type="number"
                min={1}
                max={100}
                placeholder={String(format.max_team_size)}
                value={maxTeam}
                onChange={(e) => setMaxTeam(e.target.value)}
              />
            </label>
            <label>
              <input
                type="checkbox"
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
              />{" "}
              Public event page
            </label>
          </div>
        </>
      )}
      <details>
        <summary>Web address</summary>
        <label>
          Slug{" "}
          <input
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            placeholder="Derived from the name"
            autoComplete="off"
          />
        </label>
      </details>
      {error && <p role="alert">{error}</p>}
      <Button type="submit" disabled={busy || !name.trim()}>
        {format ? `Create ${format.label.toLowerCase()} event` : "Create event"}
      </Button>
    </form>
  );
}
