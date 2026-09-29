import { useEffect, useRef, useState } from "react";
import { Button } from "../../components/Button";
import { Badge } from "../../components/Badge";
import { SubmissionReceipt } from "../pvs";

type Version = {
  public_id: string;
  number: number;
  digest: string;
  finalized_at: string;
};
type Submission = {
  status: "draft" | "finalized";
  draft_revision: number;
  draft_payload: { notes?: string; artifact_ids?: string[] };
  current_version: string | null;
  versions: Version[];
};
type Stage = { public_id: string; name: string; submission: Submission | null };
type Artifact = { public_id: string; title: string; status: string };

function message(value: unknown): string {
  if (value instanceof Error) return value.message;
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.map(message).join(" ");
  if (value && typeof value === "object")
    return Object.values(value).map(message).join(" ");
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
      // Keep the HTTP status.
    }
    throw new Error(message(detail));
  }
  return response.json() as Promise<T>;
}

export function SubmissionPanel({
  workspaceId,
  eventId,
  projectId,
}: {
  workspaceId: string;
  eventId: string;
  projectId: string;
}) {
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/projects/${projectId}/`;
  const [stages, setStages] = useState<Stage[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [stageId, setStageId] = useState("");
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [notes, setNotes] = useState("");
  const [artifactIds, setArtifactIds] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [finalizing, setFinalizing] = useState(false);
  const [dirty, setDirty] = useState(false);
  const revision = useRef(0);
  const pending = useRef<Promise<void>>(Promise.resolve());
  const latest = useRef({ notes: "", artifact_ids: [] as string[] });
  const saved = useRef(JSON.stringify(latest.current));

  useEffect(() => {
    let active = true;
    Promise.all([
      request<Stage[]>(base + "submissions/"),
      request<Artifact[]>(base + "artifacts/"),
    ])
      .then(([items, evidence]) => {
        if (active) {
          setStages(items);
          setArtifacts(evidence);
        }
      })
      .catch((cause: unknown) => {
        if (active) setError(message(cause));
      });
    return () => {
      active = false;
    };
  }, [base]);

  async function selectStage(id: string) {
    if (stageId && dirty) {
      try {
        await queueSave(stageId);
      } catch {
        return;
      }
    }
    setStageId(id);
    const current =
      stages.find((stage) => stage.public_id === id)?.submission ?? null;
    setSubmission(current);
    revision.current = current?.draft_revision ?? 0;
    latest.current = {
      notes: current?.draft_payload.notes ?? "",
      artifact_ids: current?.draft_payload.artifact_ids ?? [],
    };
    saved.current = JSON.stringify(latest.current);
    setNotes(latest.current.notes);
    setArtifactIds(latest.current.artifact_ids);
    setDirty(false);
    setError("");
  }

  function queueSave(id = stageId) {
    const work = pending.current
      .catch(() => undefined)
      .then(async () => {
        const payload = latest.current;
        const serialized = JSON.stringify(payload);
        if (
          !id ||
          serialized === saved.current ||
          submission?.status === "finalized"
        )
          return;
        setSaving(true);
        const next = await request<Submission>(
          base + `submissions/${id}/`,
          "PUT",
          {
            draft_payload: payload,
            draft_revision: revision.current,
          },
        );
        revision.current = next.draft_revision;
        saved.current = serialized;
        setSubmission(next);
        setDirty(JSON.stringify(latest.current) !== serialized);
        setSaving(false);
      });
    pending.current = work;
    return work.catch((cause: unknown) => {
      setSaving(false);
      setError(message(cause));
      throw cause;
    });
  }

  useEffect(() => {
    if (!dirty || !stageId) return;
    const timer = window.setTimeout(() => {
      void queueSave().catch(() => undefined);
    }, 700);
    return () => window.clearTimeout(timer);
  }, [notes, artifactIds, dirty, stageId]);

  async function finalize() {
    if (!stageId) return;
    setFinalizing(true);
    setError("");
    try {
      await queueSave();
      const result = await request<{ submission: Submission; receipt: string }>(
        base + `submissions/${stageId}/finalize/`,
        "POST",
        { draft_revision: revision.current },
      );
      setSubmission(result.submission);
      setStages((items) =>
        items.map((item) =>
          item.public_id === stageId
            ? { ...item, submission: result.submission }
            : item,
        ),
      );
      setDirty(false);
    } catch (cause) {
      setError(message(cause));
    } finally {
      setFinalizing(false);
    }
  }

  const finalized = submission?.status === "finalized";
  return (
    <section aria-label="Submission" className="cx-submission-workflow">
      <h3>Submission</h3>
      <p>
        Select the stage, choose ready artifacts and finalize the version. Your
        draft autosaves; finalization records immutable evidence.
      </p>
      <ol className="cx-submission-steps" aria-label="Submission progress">
        <li>
          <Badge tone={stageId ? "success" : "neutral"}>1</Badge> Choose a stage
        </li>
        <li>
          <Badge tone={stageId ? "info" : "neutral"}>2</Badge> Prepare notes &
          artifacts
        </li>
        <li>
          <Badge tone={finalized ? "success" : "neutral"}>3</Badge> Finalize &
          keep receipt
        </li>
      </ol>
      {error && <p role="alert">{error}</p>}
      {stages.length === 0 ? (
        <p>No submission stages yet.</p>
      ) : (
        <label>
          Stage{" "}
          <select
            value={stageId}
            onChange={(event) => void selectStage(event.target.value)}
          >
            <option value="">Choose a stage</option>
            {stages.map((stage) => (
              <option key={stage.public_id} value={stage.public_id}>
                {stage.name}
              </option>
            ))}
          </select>
        </label>
      )}
      {stageId && (
        <>
          <label>
            Submission notes{" "}
            <textarea
              value={notes}
              disabled={finalized}
              onChange={(event) => {
                const value = event.target.value;
                setNotes(value);
                latest.current = { ...latest.current, notes: value };
                setDirty(true);
              }}
            />
          </label>
          <Button
            variant="secondary"
            onClick={() =>
              void request<Artifact[]>(base + "artifacts/")
                .then(setArtifacts)
                .catch((cause: unknown) => setError(message(cause)))
            }
          >
            Refresh included artifacts
          </Button>
          <fieldset disabled={finalized} className="cx-artifact-picker">
            <legend>Include artifacts</legend>
            <p>
              Only ready evidence can be selected. The server validates the
              complete submission when finalizing.
            </p>
            {artifacts
              .filter((artifact) => artifact.status === "ready")
              .map((artifact) => (
                <label key={artifact.public_id}>
                  <input
                    type="checkbox"
                    checked={artifactIds.includes(artifact.public_id)}
                    onChange={(event) => {
                      const ids = event.target.checked
                        ? [...artifactIds, artifact.public_id]
                        : artifactIds.filter((id) => id !== artifact.public_id);
                      setArtifactIds(ids);
                      latest.current = { ...latest.current, artifact_ids: ids };
                      setDirty(true);
                    }}
                  />
                  {artifact.title}
                </label>
              ))}
          </fieldset>
          {!finalized && (
            <>
              <p role="status">
                {saving
                  ? "Saving draft…"
                  : dirty
                    ? "Unsaved changes"
                    : "Draft saved"}
              </p>
              <Button
                disabled={finalizing || saving}
                onClick={() => void finalize()}
              >
                {finalizing ? "Finalizing…" : "Finalize submission"}
              </Button>
            </>
          )}
          {finalized && (
            <p role="status">
              Submission finalized. Receipt: {submission.current_version}
            </p>
          )}
          {finalized && (
            <SubmissionReceipt
              key={submission?.current_version ?? "receipt"}
              projectBase={base}
              stageId={stageId}
              stageName={
                stages.find((stage) => stage.public_id === stageId)?.name
              }
            />
          )}
          <details>
            <summary>Version history and integrity references</summary>
            {submission?.versions.map((version) => (
              <div key={version.public_id}>
                <h4>Version {version.number}</h4>
                <p>
                  Finalized {new Date(version.finalized_at).toLocaleString()}
                </p>
                <p>Receipt: {version.public_id}</p>
                <p>SHA-256: {version.digest}</p>
              </div>
            ))}
          </details>
        </>
      )}
    </section>
  );
}
