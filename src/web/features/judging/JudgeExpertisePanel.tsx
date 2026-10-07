import { useEffect, useState } from "react";
import { Button } from "../../components/Button";
import { apiRequest } from "../../lib/api";

type Profile = { judge: string; tags: string[]; updated_at: string | null };

export function JudgeExpertisePanel({ workspaceId }: { workspaceId: string }) {
  const [tags, setTags] = useState("");
  const [savedTags, setSavedTags] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const url = `/api/v1/workspaces/${workspaceId}/my-judge-expertise/`;

  useEffect(() => {
    let active = true;
    apiRequest<Profile>(url, {
      describe: () => "Could not load expertise profile.",
    })
      .then((profile) => {
        if (!Array.isArray(profile.tags))
          throw new Error("Invalid expertise profile response.");
        if (active) {
          setSavedTags(profile.tags);
          setTags(profile.tags.join(", "));
        }
      })
      .catch((cause: unknown) => {
        if (active) setError(String(cause));
      });
    return () => {
      active = false;
    };
  }, [url]);

  async function save() {
    setError("");
    setSaving(true);
    try {
      const profile = await apiRequest<Profile>(url, {
        method: "PUT",
        body: {
          tags: tags
            .split(",")
            .map((tag) => tag.trim())
            .filter(Boolean),
        },
        describe: (_status, detail) =>
          (detail as { tags?: string[] } | undefined)?.tags?.join(" ") ||
          "Could not save expertise profile.",
      });
      setSavedTags(profile.tags);
      setTags(profile.tags.join(", "));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section aria-label="Judge expertise">
      <h3>Expertise</h3>
      <p>Tags matching event track names help organizers assign reviews.</p>
      {error && <p role="alert">{error}</p>}
      <label>
        Track expertise tags, separated by commas{" "}
        <input value={tags} onChange={(event) => setTags(event.target.value)} />
      </label>
      <Button variant="primary" disabled={saving} onClick={() => void save()}>
        Save expertise
      </Button>
      {savedTags.length > 0 && <p>Saved: {savedTags.join(", ")}</p>}
    </section>
  );
}
