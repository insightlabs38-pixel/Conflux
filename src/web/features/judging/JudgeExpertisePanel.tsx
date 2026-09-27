import { useEffect, useState } from "react";
import { Button } from "../../components/Button";

type Profile = { judge: string; tags: string[]; updated_at: string | null };

export function JudgeExpertisePanel({ workspaceId }: { workspaceId: string }) {
  const [tags, setTags] = useState("");
  const [savedTags, setSavedTags] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const url = `/api/v1/workspaces/${workspaceId}/my-judge-expertise/`;

  useEffect(() => {
    let active = true;
    fetch(url, { credentials: "include" })
      .then((response) => {
        if (!response.ok) throw new Error("Could not load expertise profile.");
        return response.json() as Promise<Profile>;
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
      const response = await fetch(url, {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tags: tags
            .split(",")
            .map((tag) => tag.trim())
            .filter(Boolean),
        }),
      });
      if (!response.ok) {
        const detail = (await response.json()) as { tags?: string[] };
        throw new Error(
          detail.tags?.join(" ") || "Could not save expertise profile.",
        );
      }
      const profile = (await response.json()) as Profile;
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
      <Button disabled={saving} onClick={() => void save()}>
        Save expertise
      </Button>
      {savedTags.length > 0 && <p>Saved: {savedTags.join(", ")}</p>}
    </section>
  );
}
