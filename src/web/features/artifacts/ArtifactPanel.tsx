import { useState, type FormEvent } from "react";
import { apiJson, describeProblem } from "../../lib/api";
import { useLoad } from "../../hooks/useLoad";
import { OperationStatus } from "../../components/OperationStatus";
import { useOperation } from "../../hooks/useOperation";

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
  const artifactsLoad = useLoad<Artifact[]>(base, {
    describe: describeProblem,
  });
  const preflightLoad = useLoad<Preflight>(base + "preflight/", {
    describe: describeProblem,
  });
  const artifacts = artifactsLoad.data ?? [];
  const preflight = preflightLoad.data;
  const [title, setTitle] = useState("");
  const [kind, setKind] = useState("file");
  const [visibility, setVisibility] = useState("participant");
  const [file, setFile] = useState<File | null>(null);
  const [linkTitle, setLinkTitle] = useState("");
  const [linkKind, setLinkKind] = useState("repository");
  const [linkUrl, setLinkUrl] = useState("");
  const [actionError, setError] = useState("");
  const error =
    actionError ||
    artifactsLoad.error?.message ||
    preflightLoad.error?.message ||
    "";
  const [refreshing, setRefreshing] = useState(false);

  async function refresh() {
    await Promise.all([artifactsLoad.reload(), preflightLoad.reload()]);
  }

  // Long-running actions follow the async-operation contract (hooks/useOperation.ts).
  const addLink = useOperation(
    async (
      input: { kind: string; title: string; url: string },
      { signal, report },
    ) => {
      const artifact = await apiJson<Artifact>(
        base,
        "POST",
        {
          kind: input.kind,
          visibility: "public",
          title: input.title,
          external_url: input.url,
        },
        signal,
      );
      report({ label: "Checking link…" });
      await apiJson(
        base + `${artifact.public_id}/validate/`,
        "POST",
        undefined,
        signal,
      );
      setLinkTitle("");
      setLinkUrl("");
      await refresh();
      return "Link added and checked.";
    },
  );

  const upload = useOperation(
    async (
      input: {
        file: File;
        kind: string;
        visibility: string;
        title: string;
      },
      { signal, report, commit },
    ) => {
      const { file } = input;
      report({ label: "Preparing upload…" });
      const issued = await apiJson<Upload>(
        base + "upload-intents/",
        "POST",
        {
          kind: input.kind,
          visibility: input.visibility,
          title: input.title,
          byte_size: file.size,
          content_type: file.type || "application/octet-stream",
        },
        signal,
      );
      let parts: { PartNumber: number; ETag: string }[] | undefined;
      if (issued.upload.mode === "single") {
        report({ label: "Uploading file…" });
        const response = await fetch(issued.upload.url, {
          method: "PUT",
          credentials: "omit",
          headers: issued.upload.headers,
          body: file,
          signal,
        });
        if (!response.ok)
          throw new Error(`Upload failed (${response.status}).`);
      } else {
        parts = [];
        const total = issued.upload.urls.length;
        for (const [index, url] of issued.upload.urls.entries()) {
          report({
            label: `Uploading part ${index + 1} of ${total}…`,
            done: index,
            total,
          });
          const chunk = file.slice(
            index * issued.upload.part_size,
            (index + 1) * issued.upload.part_size,
          );
          const response = await fetch(url, {
            method: "PUT",
            credentials: "omit",
            body: chunk,
            signal,
          });
          if (!response.ok)
            throw new Error(`Part ${index + 1} failed (${response.status}).`);
          const etag = response.headers.get("ETag");
          if (!etag)
            throw new Error(`Part ${index + 1} did not return an ETag.`);
          parts.push({ PartNumber: index + 1, ETag: etag });
        }
      }
      // Everything is stored: finishing is safer than stopping half-registered.
      commit();
      report({ label: "Verifying upload…" });
      await apiJson(
        base +
          `${issued.artifact.public_id}/upload-intents/${issued.intent}/complete/`,
        "POST",
        parts ? { parts } : {},
      );
      const validated = await apiJson<Artifact>(
        base + `${issued.artifact.public_id}/validate/`,
        "POST",
      );
      if (validated.status !== "ready")
        throw new Error(
          validated.validation?.detail ?? "Artifact is not ready yet.",
        );
      setTitle("");
      setFile(null);
      await refresh();
      return input.visibility === "participant" || input.visibility === "public"
        ? "Evidence uploaded and ready."
        : "Private evidence uploaded and ready.";
    },
  );
  const busy = upload.busy || addLink.busy || refreshing;

  function addExternal(event: FormEvent) {
    event.preventDefault();
    void addLink.start({
      kind: linkKind,
      title: linkTitle.trim(),
      url: linkUrl.trim(),
    });
  }

  function startUpload(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      // Rejected before anything starts, same voice as a failed operation.
      setError("Choose a file first.");
      return;
    }
    setError("");
    void upload.start({ file, kind, visibility, title: title.trim() });
  }

  function refreshChecks() {
    setRefreshing(true);
    setError("");
    refresh()
      .catch((cause: unknown) => setError(message(cause)))
      .finally(() => setRefreshing(false));
  }

  return (
    <section aria-label="Project artifacts">
      <h3>Evidence and submission checks</h3>
      {error && <p role="alert">{error}</p>}
      <div className="cx-evidence-entry">
        <form onSubmit={startUpload}>
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
          <OperationStatus
            state={upload.state}
            successMessage={(text) => text}
            onCancel={upload.cancel}
            onRetry={upload.retry}
            onDismiss={upload.reset}
          />
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
          <OperationStatus
            state={addLink.state}
            successMessage={(text) => text}
            onCancel={addLink.cancel}
            onRetry={addLink.retry}
            onDismiss={addLink.reset}
          />
        </form>
      </div>
      {artifacts.length === 0 ? (
        <p>No evidence yet.</p>
      ) : (
        <ul className="cx-evidence-list">
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
      <button type="button" disabled={busy} onClick={refreshChecks}>
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
