import { useEffect, useState, type FormEvent } from "react";
import { ErrorState } from "../../components/ErrorState";

type Answer = string | number | boolean | string[];
type Field = {
  id: string;
  label: string;
  type: string;
  required?: boolean;
  options?: string[];
  visible_if?: { field: string; equals: string | boolean };
  required_if?: { field: string; equals: string | boolean };
};
type Form = {
  public_id: string;
  name: string;
  number: number;
  schema: { fields: Field[] };
};
type Artifact = { public_id: string; title: string; status: string };

function visible(field: Field, answers: Record<string, Answer>) {
  return (
    !field.visible_if ||
    answers[field.visible_if.field] === field.visible_if.equals
  );
}

function errorMessage(cause: unknown) {
  return cause instanceof Error
    ? cause.message
    : "Could not save form response.";
}

function localDateTime(value: string) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value.slice(0, 16);
  return new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
    .toISOString()
    .slice(0, 16);
}

async function request<T>(
  url: string,
  method = "GET",
  body?: object,
): Promise<T> {
  const response = await fetch(url, {
    method,
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    let detail = `Request failed (${response.status}).`;
    try {
      const data = await response.json();
      detail = typeof data === "string" ? data : JSON.stringify(data);
    } catch {
      // Keep the HTTP status.
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export function ProjectForms({
  workspaceId,
  eventId,
  projectId,
}: {
  workspaceId: string;
  eventId: string;
  projectId: string;
}) {
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/projects/${projectId}/`;
  const [forms, setForms] = useState<Form[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([
      request<Form[]>(base + "forms/"),
      request<Artifact[]>(base + "artifacts/"),
    ])
      .then(([items, evidence]) => {
        if (active) {
          setForms(items);
          setArtifacts(evidence.filter((item) => item.status === "ready"));
        }
      })
      .catch((cause: unknown) => {
        if (active) setError(errorMessage(cause));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [base]);

  return (
    <section aria-label="Project forms">
      <h3>Project forms</h3>
      {loading ? (
        <p role="status">Loading forms…</p>
      ) : error ? (
        <p role="alert">{error}</p>
      ) : forms.length === 0 ? (
        <p>No published forms for this project.</p>
      ) : (
        forms.map((form) => (
          <ProjectForm
            key={form.public_id}
            form={form}
            artifacts={artifacts}
            url={`${base}forms/${form.public_id}/response/`}
          />
        ))
      )}
    </section>
  );
}

function ProjectForm({
  form,
  artifacts,
  url,
}: {
  form: Form;
  artifacts: Artifact[];
  url: string;
}) {
  const [answers, setAnswers] = useState<Record<string, Answer>>({});
  const [loading, setLoading] = useState(true);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    request<{ answers: Record<string, Answer> }>(url)
      .then((response) => {
        if (active) {
          setAnswers(response.answers);
          setLoaded(true);
        }
      })
      .catch((cause: unknown) => {
        if (active) {
          setLoaded(false);
          setError(errorMessage(cause));
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [url, retry]);

  function update(id: string, value: Answer | null) {
    setAnswers((current) => {
      if (value !== null) return { ...current, [id]: value };
      const next = { ...current };
      delete next[id];
      return next;
    });
    setDirty(true);
    setSaved(false);
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!loaded) return;
    setError("");
    const missingChoice = form.schema.fields.find(
      (field) =>
        field.type === "multi_select" &&
        visible(field, answers) &&
        (field.required ||
          (field.required_if &&
            answers[field.required_if.field] === field.required_if.equals)) &&
        (!Array.isArray(answers[field.id]) ||
          (answers[field.id] as string[]).length === 0),
    );
    if (missingChoice) {
      setError(`Select at least one option for ${missingChoice.label}.`);
      return;
    }
    setBusy(true);
    const included = Object.fromEntries(
      form.schema.fields
        .filter((field) => visible(field, answers) && field.id in answers)
        .map((field) => [field.id, answers[field.id]]),
    );
    try {
      const response = await request<{ answers: Record<string, Answer> }>(
        url,
        "PUT",
        { answers: included },
      );
      setAnswers(response.answers);
      setDirty(false);
      setSaved(true);
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={(event) => void save(event)}>
      <h4>
        {form.name} (version {form.number})
      </h4>
      {loading ? (
        <p role="status">Loading answers…</p>
      ) : !loaded ? (
        <ErrorState
          message={error}
          onRetry={() => setRetry((count) => count + 1)}
        />
      ) : (
        <>
          {error && <p role="alert">{error}</p>}
          {form.schema.fields
            .filter((field) => visible(field, answers))
            .map((field) => {
              const value = answers[field.id];
              const required =
                field.required ||
                (field.required_if &&
                  answers[field.required_if.field] ===
                    field.required_if.equals);
              if (field.type === "boolean")
                return (
                  <label key={field.id}>
                    {field.label}{" "}
                    <select
                      value={
                        value === true ? "true" : value === false ? "false" : ""
                      }
                      required={required}
                      onChange={(event) =>
                        update(
                          field.id,
                          event.target.value === ""
                            ? null
                            : event.target.value === "true",
                        )
                      }
                    >
                      <option value="">Choose an answer</option>
                      <option value="true">Yes</option>
                      <option value="false">No</option>
                    </select>
                  </label>
                );
              if (field.type === "multi_select")
                return (
                  <fieldset key={field.id} aria-required={required}>
                    <legend>
                      {field.label}
                      {required ? " *" : ""}
                    </legend>
                    {field.options?.map((option) => (
                      <label key={option}>
                        <input
                          type="checkbox"
                          checked={
                            Array.isArray(value) && value.includes(option)
                          }
                          onChange={(event) => {
                            const values = Array.isArray(value) ? value : [];
                            update(
                              field.id,
                              event.target.checked
                                ? [...values, option]
                                : values.filter((item) => item !== option),
                            );
                          }}
                        />
                        {option}
                      </label>
                    ))}
                  </fieldset>
                );
              if (field.type === "select" || field.type === "artifact")
                return (
                  <label key={field.id}>
                    {field.label}{" "}
                    <select
                      value={typeof value === "string" ? value : ""}
                      required={required}
                      onChange={(event) => update(field.id, event.target.value)}
                    >
                      <option value="">Choose an option</option>
                      {(field.type === "artifact"
                        ? artifacts.map((item) => ({
                            value: item.public_id,
                            label: item.title,
                          }))
                        : (field.options ?? []).map((option) => ({
                            value: option,
                            label: option,
                          }))
                      ).map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>
                );
              if (field.type === "rich_text")
                return (
                  <label key={field.id}>
                    {field.label}{" "}
                    <textarea
                      value={typeof value === "string" ? value : ""}
                      required={required}
                      onChange={(event) => update(field.id, event.target.value)}
                    />
                  </label>
                );
              const displayValue =
                typeof value === "string" || typeof value === "number"
                  ? value
                  : "";
              return (
                <label key={field.id}>
                  {field.label}{" "}
                  <input
                    type={
                      field.type === "number"
                        ? "number"
                        : field.type === "url"
                          ? "url"
                          : field.type === "date"
                            ? "date"
                            : field.type === "datetime"
                              ? "datetime-local"
                              : "text"
                    }
                    value={
                      field.type === "datetime" &&
                      typeof displayValue === "string"
                        ? localDateTime(displayValue)
                        : displayValue
                    }
                    required={required}
                    onChange={(event) =>
                      update(
                        field.id,
                        field.type === "datetime" && event.target.value
                          ? new Date(event.target.value).toISOString()
                          : event.target.value,
                      )
                    }
                  />
                </label>
              );
            })}
          <button disabled={busy}>{busy ? "Saving…" : "Save answers"}</button>
          {dirty && <p role="status">Unsaved answers</p>}
          {saved && <p role="status">Answers saved.</p>}
        </>
      )}
    </form>
  );
}
