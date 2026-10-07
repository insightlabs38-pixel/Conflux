import { useEffect, useState, type FormEvent } from "react";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { apiJson } from "../../lib/api";

type EventSummary = { public_id: string; name: string };
type Template = {
  public_id: string;
  name: string;
  source_event_name: string;
  sections: string[];
  created_at: string;
};
type Preview = Record<string, unknown[] | undefined>;

const SECTION_KEYS = [
  "tracks",
  "base_prizes",
  "stages",
  "stage_transitions",
  "forms",
  "policies",
  "temporal_gates",
  "policy_bindings",
  "awards",
  "evaluation_plans",
  "pages",
] as const;

function message(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (typeof error === "string") return error;
  if (error && typeof error === "object") {
    return Object.entries(error)
      .map(([key, value]) => `${key}: ${message(value)}`)
      .join(" ");
  }
  return "Request failed.";
}

export function EventTemplatesPanel({
  workspaceId,
  onCreated,
}: {
  workspaceId: string;
  onCreated?: (eventId: string) => void;
}) {
  const base = `/api/v1/workspaces/${workspaceId}/`;
  const [events, setEvents] = useState<EventSummary[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [sourceEvent, setSourceEvent] = useState("");
  const [sections, setSections] = useState<string[]>([...SECTION_KEYS]);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [templateName, setTemplateName] = useState("");
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [created, setCreated] = useState<{
    public_id: string;
    name: string;
    slug: string;
  } | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function loadLists() {
    void Promise.all([
      apiJson<EventSummary[]>(base + "events/"),
      apiJson<Template[]>(base + "event-templates/"),
    ])
      .then(([nextEvents, nextTemplates]) => {
        setEvents(nextEvents);
        setTemplates(nextTemplates);
      })
      .catch((cause: unknown) => setError(message(cause)));
  }
  useEffect(loadLists, [base]);

  function toggleSection(key: string) {
    setSections((current) =>
      current.includes(key)
        ? current.filter((item) => item !== key)
        : [...current, key],
    );
  }

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (cause) {
      setError(message(cause));
    } finally {
      setBusy(false);
    }
  }

  function previewSource() {
    void run(async () => {
      if (!sourceEvent) throw new Error("Choose a source event first.");
      const archive = await apiJson<Preview>(
        base + `events/${sourceEvent}/archive/?mode=config`,
      );
      setPreview(archive);
    });
  }

  function saveTemplate(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (!sourceEvent) throw new Error("Choose a source event first.");
      if (!templateName.trim()) throw new Error("Template name is required.");
      const saved = await apiJson<Template>(base + "event-templates/", "POST", {
        event: sourceEvent,
        name: templateName.trim(),
        sections,
      });
      setTemplateName("");
      setTemplates((current) => [...current, saved]);
    });
  }

  function cloneDirectly(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (!sourceEvent) throw new Error("Choose a source event first.");
      if (!name.trim() || !slug.trim())
        throw new Error("Name and slug are required.");
      const result = await apiJson<{
        public_id: string;
        name: string;
        slug: string;
      }>(base + `events/${sourceEvent}/clone/`, "POST", {
        name: name.trim(),
        slug: slug.trim(),
        sections,
      });
      setCreated(result);
      onCreated?.(result.public_id);
      setName("");
      setSlug("");
    });
  }

  async function instantiate(
    template: Template,
    instantiateName: string,
    instantiateSlug: string,
  ) {
    await run(async () => {
      if (!instantiateName.trim() || !instantiateSlug.trim())
        throw new Error("Name and slug are required.");
      const result = await apiJson<{
        public_id: string;
        name: string;
        slug: string;
      }>(base + `event-templates/${template.public_id}/instantiate/`, "POST", {
        name: instantiateName.trim(),
        slug: instantiateSlug.trim(),
      });
      setCreated(result);
      onCreated?.(result.public_id);
    });
  }

  async function removeTemplate(template: Template) {
    await run(async () => {
      await apiJson(base + `event-templates/${template.public_id}/`, "DELETE");
      setTemplates((current) =>
        current.filter((item) => item.public_id !== template.public_id),
      );
    });
  }

  return (
    <Card title="Event templates &amp; cloning">
      {error && <p role="alert">{error}</p>}
      {created && (
        <p role="status">
          Created event "{created.name}" ({created.slug}).
        </p>
      )}
      <label htmlFor="tpl-source">Source event</label>
      <select
        id="tpl-source"
        value={sourceEvent}
        onChange={(e) => setSourceEvent(e.target.value)}
      >
        <option value="">Choose an event</option>
        {events.map((item) => (
          <option key={item.public_id} value={item.public_id}>
            {item.name}
          </option>
        ))}
      </select>
      <Button type="button" variant="secondary" onClick={previewSource}>
        Preview
      </Button>
      {preview && (
        <ul>
          {SECTION_KEYS.filter((key) => key in preview).map((key) => (
            <li key={key}>
              {key}: {(preview[key] ?? []).length}
            </li>
          ))}
        </ul>
      )}
      <fieldset>
        <legend>Components to include</legend>
        {SECTION_KEYS.map((key) => (
          <label key={key}>
            <input
              type="checkbox"
              checked={sections.includes(key)}
              onChange={() => toggleSection(key)}
            />{" "}
            {key}
          </label>
        ))}
      </fieldset>
      <form onSubmit={saveTemplate}>
        <label htmlFor="tpl-name">Template name</label>
        <input
          id="tpl-name"
          value={templateName}
          onChange={(e) => setTemplateName(e.target.value)}
          required
        />
        <Button variant="primary" type="submit" disabled={busy}>
          Save as template
        </Button>
      </form>
      <form onSubmit={cloneDirectly}>
        <label htmlFor="clone-name">New event name</label>
        <input
          id="clone-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <label htmlFor="clone-slug">New event slug</label>
        <input
          id="clone-slug"
          value={slug}
          onChange={(e) => setSlug(e.target.value)}
          required
        />
        <Button variant="primary" type="submit" disabled={busy}>
          Clone directly to a new event now
        </Button>
      </form>
      <h4>Saved templates</h4>
      {templates.length === 0 ? (
        <p>No templates saved yet.</p>
      ) : (
        <ul>
          {templates.map((template) => (
            <TemplateRow
              key={template.public_id}
              template={template}
              onInstantiate={instantiate}
              onDelete={removeTemplate}
            />
          ))}
        </ul>
      )}
    </Card>
  );
}

function TemplateRow({
  template,
  onInstantiate,
  onDelete,
}: {
  template: Template;
  onInstantiate: (
    template: Template,
    name: string,
    slug: string,
  ) => Promise<void>;
  onDelete: (template: Template) => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [removing, setRemoving] = useState(false);
  return (
    <li>
      <strong>{template.name}</strong> (from {template.source_event_name}) —{" "}
      {template.sections.join(", ")}
      <div>
        <label htmlFor={`inst-name-${template.public_id}`}>Name</label>
        <input
          id={`inst-name-${template.public_id}`}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <label htmlFor={`inst-slug-${template.public_id}`}>Slug</label>
        <input
          id={`inst-slug-${template.public_id}`}
          value={slug}
          onChange={(e) => setSlug(e.target.value)}
        />
        <Button
          variant="primary"
          type="button"
          onClick={() => void onInstantiate(template, name, slug)}
        >
          Create event from template
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() => setRemoving(true)}
        >
          Delete template
        </Button>
      </div>
      {removing && (
        <p role="group" aria-label="Confirm template deletion">
          Delete “{template.name}”? The template is removed and cannot be
          restored; events already created from it are not changed.{" "}
          <Button
            type="button"
            variant="danger"
            onClick={() => void onDelete(template)}
          >
            Delete template
          </Button>{" "}
          <Button
            type="button"
            variant="secondary"
            onClick={() => setRemoving(false)}
          >
            Keep template
          </Button>
        </p>
      )}
    </li>
  );
}
