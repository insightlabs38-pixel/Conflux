import { useEffect, useState, type FormEvent } from "react";

type Artifact = {
  public_id: string;
  kind: string;
  title: string;
  visibility: string;
  status: string;
  validation: { outcome: string; detail: string } | null;
  external_url: string;
};
type Preflight = {
  status: "READY" | "WARNING" | "BLOCKED";
  checks: { code: string; severity: string; detail: string }[];
};
type Upload = {
  artifact: Artifact;
  intent: string;
  upload:
    | { mode: "single"; url: string; headers: Record<string, string> }
    | { mode: "multipart"; part_size: number; urls: string[] };
};

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

export function ArtifactPanel({
  workspaceId,
  eventId,
  projectId,
}: {
  workspaceId: string;
  eventId: string;
  projectId: string;
}) {
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/projects/${projectId}/artifacts/`;
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [preflight, setPreflight] = useState<Preflight | null>(null);
  const [title, setTitle] = useState("");
  const [kind, setKind] = useState("file");
  const [visibility, setVisibility] = useState("participant");
  const [file, setFile] = useState<File | null>(null);
  const [linkTitle, setLinkTitle] = useState("");
  const [linkKind, setLinkKind] = useState("repository");
  const [linkUrl, setLinkUrl] = useState("");
  const [error, setError] = useState("");
  const [progress, setProgress] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  async function refresh() {
    const [items, checks] = await Promise.all([
      request<Artifact[]>(base),
      request<Preflight>(base + "preflight/"),
    ]);
    setArtifacts(items);
    setPreflight(checks);
  }
  useEffect(() => {
    let active = true;
    Promise.all([
      request<Artifact[]>(base),
      request<Preflight>(base + "preflight/"),
    ])
      .then(([items, checks]) => {
        if (active) {
          setArtifacts(items);
          setPreflight(checks);
        }
      })
      .catch((cause: unknown) => {
        if (active) setError(message(cause));
      });
    return () => {
      active = false;
    };
  }, [base]);

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
      setProgress("");
    }
  }

  function addExternal(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      const artifact = await request<Artifact>(base, "POST", {
        kind: linkKind,
        visibility: "public",
        title: linkTitle.trim(),
        external_url: linkUrl.trim(),
      });
      setProgress("Checking link…");
      await request(base + `${artifact.public_id}/validate/`, "POST");
      setNotice("Link added and checked.");
      setLinkTitle("");
      setLinkUrl("");
      await refresh();
    });
  }

  function upload(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (!file) throw new Error("Choose a file first.");
      setProgress("Preparing upload…");
      const issued = await request<Upload>(base + "upload-intents/", "POST", {
        kind,
        visibility,
        title: title.trim(),
        byte_size: file.size,
        content_type: file.type || "application/octet-stream",
      });
      let parts: { PartNumber: number; ETag: string }[] | undefined;
      if (issued.upload.mode === "single") {
        setProgress("Uploading file…");
        const response = await fetch(issued.upload.url, {
          method: "PUT",
          credentials: "omit",
          headers: issued.upload.headers,
          body: file,
        });
        if (!response.ok)
          throw new Error(`Upload failed (${response.status}).`);
      } else {
        parts = [];
        for (const [index, url] of issued.upload.urls.entries()) {
          setProgress(
            `Uploading part ${index + 1} of ${issued.upload.urls.length}…`,
          );
          const chunk = file.slice(
            index * issued.upload.part_size,
            (index + 1) * issued.upload.part_size,
          );
          const response = await fetch(url, {
            method: "PUT",
            credentials: "omit",
            body: chunk,
          });
          if (!response.ok)
            throw new Error(`Part ${index + 1} failed (${response.status}).`);
          const etag = response.headers.get("ETag");
          if (!etag)
            throw new Error(`Part ${index + 1} did not return an ETag.`);
          parts.push({ PartNumber: index + 1, ETag: etag });
        }
      }
      setProgress("Verifying upload…");
      await request(
        base +
          `${issued.artifact.public_id}/upload-intents/${issued.intent}/complete/`,
        "POST",
        parts ? { parts } : {},
      );
      const validated = await request<Artifact>(
        base + `${issued.artifact.public_id}/validate/`,
        "POST",
      );
      if (validated.status !== "ready")
        throw new Error(
          validated.validation?.detail ?? "Artifact is not ready yet.",
        );
      setNotice(
        visibility === "participant" || visibility === "public"
          ? "Evidence uploaded and ready."
          : "Private evidence uploaded and ready.",
      );
      setTitle("");
      setFile(null);
      await refresh();
    });
  }

  return (
    <section aria-label="Project artifacts">
      <h3>Evidence and submission checks</h3>
      {error && <p role="alert">{error}</p>}
      {progress && <p role="status">{progress}</p>}
      {notice && <p role="status">{notice}</p>}
      <form onSubmit={upload}>
        <h4>Upload evidence</h4>
        <label>
          Title{" "}
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            required
          />
        </label>
        <label>
          Kind{" "}
          <select
            value={kind}
            onChange={(event) => {
              setKind(event.target.value);
              if (event.target.value === "secret") setVisibility("judge");
            }}
          >
            {["file", "image", "video", "document", "dataset", "secret"].map(
              (value) => (
                <option key={value}>{value}</option>
              ),
            )}
          </select>
        </label>
        <label>
          Visibility{" "}
          <select
            value={visibility}
            onChange={(event) => setVisibility(event.target.value)}
          >
            {(kind === "secret"
              ? ["judge", "organizer"]
              : ["participant", "public", "judge", "organizer"]
            ).map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        <label>
          File{" "}
          <input
            type="file"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            required
          />
        </label>
        <button disabled={busy}>Upload</button>
      </form>
      <form onSubmit={addExternal}>
        <h4>Add link</h4>
        <label>
          Title{" "}
          <input
            value={linkTitle}
            onChange={(event) => setLinkTitle(event.target.value)}
            required
          />
        </label>
        <label>
          Kind{" "}
          <select
            value={linkKind}
            onChange={(event) => setLinkKind(event.target.value)}
          >
            {["repository", "live_url", "external_video"].map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        <label>
          URL{" "}
          <input
            type="url"
            value={linkUrl}
            onChange={(event) => setLinkUrl(event.target.value)}
            required
          />
        </label>
        <button disabled={busy}>Add link</button>
      </form>
      {artifacts.length === 0 ? (
        <p>No evidence yet.</p>
      ) : (
        <ul>
          {artifacts.map((artifact) => (
            <li key={artifact.public_id}>
              {artifact.title} ({artifact.kind}, {artifact.status})
              {artifact.validation && (
                <span> — {artifact.validation.detail}</span>
              )}
            </li>
          ))}
        </ul>
      )}
      <button
        type="button"
        disabled={busy}
        onClick={() => {
          void run(refresh);
        }}
      >
        Refresh checks
      </button>
      {preflight && (
        <section aria-label="Submission preflight">
          <h4>Submission readiness: {preflight.status}</h4>
          {preflight.checks.length === 0 ? (
            <p>All checks passed.</p>
          ) : (
            <ul>
              {preflight.checks.map((check, index) => (
                <li key={`${check.code}-${index}`}>
                  {check.severity}: {check.detail}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </section>
  );
}
