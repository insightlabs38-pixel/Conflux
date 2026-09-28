import { useEffect, useState, type FormEvent } from "react";

type Field = {
  id: string;
  label: string;
  type: string;
  required: boolean;
  options?: string[];
  visible_to: string[];
  visible_if?: { field: string; equals: string | boolean };
  required_if?: { field: string; equals: string | boolean };
};
type Form = {
  public_id: string;
  name: string;
  draft_schema: { fields: Field[] };
};
type Version = {
  public_id: string;
  number: number;
  schema: { fields: Field[] };
};

const TYPES = [
  "text",
  "rich_text",
  "number",
  "select",
  "multi_select",
  "boolean",
  "url",
  "date",
  "datetime",
  "artifact",
];
const SCOPES = ["public", "participant", "judge", "organizer"];

function message(value: unknown): string {
  if (typeof value === "string") return value;
  if (value instanceof Error) return value.message;
  if (Array.isArray(value)) return value.map(message).join(" ");
  if (value && typeof value === "object")
    return Object.entries(value)
      .map(([key, item]) => `${key}: ${message(item)}`)
      .join(" ");
  return "Request failed.";
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
    let detail: unknown = `Request failed (${response.status}).`;
    try {
      detail = await response.json();
    } catch {
      /* Retain status. */
    }
    throw new Error(message(detail));
  }
  return response.json() as Promise<T>;
}

export function FormBuilder({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/forms/`;
  const [forms, setForms] = useState<Form[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [fields, setFields] = useState<Field[]>([]);
  const [versions, setVersions] = useState<Version[]>([]);
  const [formName, setFormName] = useState("");
  const [fieldId, setFieldId] = useState("");
  const [label, setLabel] = useState("");
  const [kind, setKind] = useState("text");
  const [options, setOptions] = useState("");
  const [required, setRequired] = useState(false);
  const [scopes, setScopes] = useState(["participant", "judge", "organizer"]);
  const [visibleController, setVisibleController] = useState("");
  const [visibleValue, setVisibleValue] = useState("");
  const [requiredController, setRequiredController] = useState("");
  const [requiredValue, setRequiredValue] = useState("");
  const [previewScope, setPreviewScope] = useState("participant");
  const [previewAnswers, setPreviewAnswers] = useState<Record<string, string>>(
    {},
  );
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    request<Form[]>(base)
      .then((items) => {
        if (active) setForms(items);
      })
      .catch((cause: unknown) => {
        if (active) setError(message(cause));
      });
    return () => {
      active = false;
    };
  }, [base]);

  async function choose(id: string, list = forms) {
    setSelectedId(id);
    setPreviewAnswers({});
    setFields(
      list.find((form) => form.public_id === id)?.draft_schema.fields ?? [],
    );
    setVersions(id ? await request<Version[]>(base + `${id}/versions/`) : []);
  }

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
    } catch (cause) {
      setError(message(cause));
    } finally {
      setBusy(false);
    }
  }

  function create(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      const form = await request<Form>(base, "POST", { name: formName.trim() });
      const list = [...forms, form];
      setForms(list);
      setFormName("");
      await choose(form.public_id, list);
    });
  }

  const controllers = fields.filter(
    (field) => field.type === "select" || field.type === "boolean",
  );
  function choices(controllerId: string) {
    const controller = controllers.find((field) => field.id === controllerId);
    return controller?.type === "boolean"
      ? ["true", "false"]
      : (controller?.options ?? []);
  }
  function condition(controllerId: string, value: string) {
    const controller = controllers.find((field) => field.id === controllerId);
    return {
      field: controllerId,
      equals: controller?.type === "boolean" ? value === "true" : value,
    };
  }

  function addField(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (
      !/^[a-z][a-z0-9_]{0,63}$/.test(fieldId) ||
      fields.some((field) => field.id === fieldId)
    ) {
      setError("Field id must be a unique lowercase identifier.");
      return;
    }
    if (!label.trim() || scopes.length === 0) {
      setError("A label and visibility scope are required.");
      return;
    }
    const values = options
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
    if (
      ["select", "multi_select"].includes(kind) &&
      (values.length === 0 || values.length !== new Set(values).size)
    ) {
      setError("Choices must be unique and nonempty.");
      return;
    }
    if (
      (visibleController && !visibleValue) ||
      (requiredController && !requiredValue)
    ) {
      setError("Choose a condition value.");
      return;
    }
    const field: Field = {
      id: fieldId,
      label: label.trim(),
      type: kind,
      required,
      visible_to: scopes,
    };
    if (["select", "multi_select"].includes(kind)) field.options = values;
    if (visibleController)
      field.visible_if = condition(visibleController, visibleValue);
    if (requiredController)
      field.required_if = condition(requiredController, requiredValue);
    setFields([...fields, field]);
    setFieldId("");
    setLabel("");
    setOptions("");
    setRequired(false);
    setVisibleController("");
    setVisibleValue("");
    setRequiredController("");
    setRequiredValue("");
  }

  function restoreVersion(version: Version) {
    void run(async () => {
      const updated = await request<Form>(
        base + `${selectedId}/versions/${version.public_id}/restore/`,
        "POST",
      );
      setForms(
        forms.map((form) => (form.public_id === selectedId ? updated : form)),
      );
      setFields(updated.draft_schema.fields);
      setNotice(
        `Version ${version.number} restored to draft. Publish to make it live.`,
      );
    });
  }

  function save(publish: boolean) {
    void run(async () => {
      const updated = await request<Form>(base + `${selectedId}/`, "PUT", {
        schema: { fields },
      });
      setForms(
        forms.map((form) => (form.public_id === selectedId ? updated : form)),
      );
      if (publish) {
        const version = await request<Version>(
          base + `${selectedId}/publish/`,
          "POST",
        );
        setVersions([...versions, version]);
        setNotice(`Published version ${version.number}.`);
      } else setNotice("Draft saved.");
    });
  }

  function isVisible(field: Field) {
    if (
      !field.visible_to.includes(previewScope) &&
      !field.visible_to.includes("public")
    )
      return false;
    return (
      !field.visible_if ||
      previewAnswers[field.visible_if.field] === String(field.visible_if.equals)
    );
  }

  return (
    <section aria-label="Form builder">
      <h2>Forms</h2>
      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}
      <form onSubmit={create}>
        <label>
          New form name{" "}
          <input
            value={formName}
            onChange={(event) => setFormName(event.target.value)}
            required
          />
        </label>
        <button disabled={busy}>Create form</button>
      </form>
      {forms.length === 0 ? (
        <p>No forms yet.</p>
      ) : (
        <label>
          Edit form{" "}
          <select
            value={selectedId}
            onChange={(event) => {
              void choose(event.target.value).catch((cause: unknown) =>
                setError(message(cause)),
              );
            }}
          >
            <option value="">Choose a form</option>
            {forms.map((form) => (
              <option key={form.public_id} value={form.public_id}>
                {form.name}
              </option>
            ))}
          </select>
        </label>
      )}
      {selectedId && (
        <>
          <h3>Draft fields</h3>
          {fields.length === 0 && <p>No fields yet.</p>}
          <ol>
            {fields.map((field, index) => (
              <li key={field.id}>
                {field.label} ({field.id}, {field.type}){" "}
                <button
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    setFields(fields.filter((_, at) => at !== index))
                  }
                >
                  Remove
                </button>
              </li>
            ))}
          </ol>
          <form onSubmit={addField}>
            <h4>Add field</h4>
            <label>
              Field id{" "}
              <input
                value={fieldId}
                onChange={(event) => setFieldId(event.target.value)}
                required
              />
            </label>
            <label>
              Label{" "}
              <input
                value={label}
                onChange={(event) => setLabel(event.target.value)}
                required
              />
            </label>
            <label>
              Type{" "}
              <select
                value={kind}
                onChange={(event) => setKind(event.target.value)}
              >
                {TYPES.map((type) => (
                  <option key={type}>{type}</option>
                ))}
              </select>
            </label>
            {["select", "multi_select"].includes(kind) && (
              <label>
                Choices, comma separated{" "}
                <input
                  value={options}
                  onChange={(event) => setOptions(event.target.value)}
                />
              </label>
            )}
            <label>
              <input
                type="checkbox"
                checked={required}
                onChange={(event) => setRequired(event.target.checked)}
              />{" "}
              Required
            </label>
            <fieldset>
              <legend>Visible to</legend>
              {SCOPES.map((scope) => (
                <label key={scope}>
                  <input
                    type="checkbox"
                    checked={scopes.includes(scope)}
                    onChange={(event) =>
                      setScopes(
                        event.target.checked
                          ? [...scopes, scope]
                          : scopes.filter((item) => item !== scope),
                      )
                    }
                  />
                  {scope}
                </label>
              ))}
            </fieldset>
            {controllers.length > 0 && (
              <>
                <label>
                  Visible when{" "}
                  <select
                    value={visibleController}
                    onChange={(event) => {
                      setVisibleController(event.target.value);
                      setVisibleValue("");
                    }}
                  >
                    <option value="">Always</option>
                    {controllers.map((field) => (
                      <option key={field.id} value={field.id}>
                        {field.label}
                      </option>
                    ))}
                  </select>
                </label>
                {visibleController && (
                  <label>
                    Equals{" "}
                    <select
                      value={visibleValue}
                      onChange={(event) => setVisibleValue(event.target.value)}
                    >
                      <option value="">Choose value</option>
                      {choices(visibleController).map((value) => (
                        <option key={value}>{value}</option>
                      ))}
                    </select>
                  </label>
                )}
                <label>
                  Required when{" "}
                  <select
                    value={requiredController}
                    onChange={(event) => {
                      setRequiredController(event.target.value);
                      setRequiredValue("");
                    }}
                  >
                    <option value="">Never</option>
                    {controllers.map((field) => (
                      <option key={field.id} value={field.id}>
                        {field.label}
                      </option>
                    ))}
                  </select>
                </label>
                {requiredController && (
                  <label>
                    Equals{" "}
                    <select
                      value={requiredValue}
                      onChange={(event) => setRequiredValue(event.target.value)}
                    >
                      <option value="">Choose value</option>
                      {choices(requiredController).map((value) => (
                        <option key={value}>{value}</option>
                      ))}
                    </select>
                  </label>
                )}
              </>
            )}
            <button disabled={busy}>Add field</button>
          </form>
          <button type="button" disabled={busy} onClick={() => save(false)}>
            Save draft
          </button>
          <button type="button" disabled={busy} onClick={() => save(true)}>
            Publish version
          </button>
          <h3>Preview</h3>
          <label>
            View as{" "}
            <select
              value={previewScope}
              onChange={(event) => setPreviewScope(event.target.value)}
            >
              {SCOPES.map((scope) => (
                <option key={scope}>{scope}</option>
              ))}
            </select>
          </label>
          <div aria-label="Form preview">
            {fields.filter(isVisible).map((field) => (
              <label key={field.id}>
                {field.label}
                {field.required ||
                (field.required_if &&
                  previewAnswers[field.required_if.field] ===
                    String(field.required_if.equals))
                  ? " *"
                  : ""}
                {field.type === "select" ? (
                  <select
                    value={previewAnswers[field.id] ?? ""}
                    onChange={(event) =>
                      setPreviewAnswers({
                        ...previewAnswers,
                        [field.id]: event.target.value,
                      })
                    }
                  >
                    <option value="">Choose</option>
                    {field.options?.map((value) => (
                      <option key={value}>{value}</option>
                    ))}
                  </select>
                ) : field.type === "multi_select" ? (
                  <select
                    multiple
                    value={previewAnswers[field.id]?.split(",") ?? []}
                    onChange={(event) =>
                      setPreviewAnswers({
                        ...previewAnswers,
                        [field.id]: Array.from(event.target.selectedOptions)
                          .map((option) => option.value)
                          .join(","),
                      })
                    }
                  >
                    {field.options?.map((value) => (
                      <option key={value}>{value}</option>
                    ))}
                  </select>
                ) : field.type === "boolean" ? (
                  <input
                    type="checkbox"
                    checked={previewAnswers[field.id] === "true"}
                    onChange={(event) =>
                      setPreviewAnswers({
                        ...previewAnswers,
                        [field.id]: String(event.target.checked),
                      })
                    }
                  />
                ) : field.type === "rich_text" ? (
                  <textarea
                    value={previewAnswers[field.id] ?? ""}
                    onChange={(event) =>
                      setPreviewAnswers({
                        ...previewAnswers,
                        [field.id]: event.target.value,
                      })
                    }
                  />
                ) : (
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
                              : field.type === "artifact"
                                ? "file"
                                : "text"
                    }
                    value={
                      field.type === "artifact"
                        ? undefined
                        : (previewAnswers[field.id] ?? "")
                    }
                    onChange={(event) =>
                      setPreviewAnswers({
                        ...previewAnswers,
                        [field.id]: event.target.value,
                      })
                    }
                  />
                )}
              </label>
            ))}
          </div>
          <h3>Published versions</h3>
          {versions.length === 0 ? (
            <p>No published versions yet.</p>
          ) : (
            <ul>
              {versions.map((version) => (
                <li key={version.public_id}>
                  Version {version.number} ({version.schema.fields.length}{" "}
                  fields)
                  <button type="button" onClick={() => restoreVersion(version)}>
                    Restore to draft
                  </button>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  );
}
