import { useState, type FormEvent } from "react";
import { Button } from "../../components/Button";
import { Field } from "../../components/Foundation";
import { api, messageOf } from "../pvs/http";

type Project = {
  public_id: string;
  name: string;
  description?: string;
  team: string | null;
  track: string | null;
};
export function ProjectStoryEditor({
  project,
  base,
  onSaved,
}: {
  project: Project;
  base: string;
  onSaved: (project: Project) => void;
}) {
  const [name, setName] = useState(project.name);
  const [description, setDescription] = useState(project.description ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setStatus("");
    try {
      const next = await api<Project>(
        `${base}projects/${project.public_id}/`,
        "PATCH",
        { name: name.trim(), description },
      );
      onSaved(next);
      setStatus("Project story saved.");
    } catch (cause) {
      setError(messageOf(cause));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section aria-label="Project story editor">
      <h3>Project story</h3>
      <p>
        Explain the problem, what you built, and how it works. Markdown is
        supported. Updating the project story does not change evidence already
        frozen in a finalized version.
      </p>
      <form onSubmit={(event) => void save(event)}>
        <Field label="Project title">
          {(props) => (
            <input
              {...props}
              required
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          )}
        </Field>
        <Field
          label="Project description"
          hint="Use headings, paragraphs, links, and code to tell the project story."
        >
          {(props) => (
            <textarea
              {...props}
              rows={12}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          )}
        </Field>
        <Button type="submit" disabled={busy}>
          {busy ? "Saving story…" : "Save project story"}
        </Button>
        {error && <p role="alert">{error}</p>}
        {status && <p role="status">{status}</p>}
      </form>
    </section>
  );
}
