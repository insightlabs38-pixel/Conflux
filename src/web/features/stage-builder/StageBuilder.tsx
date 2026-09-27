import { useEffect, useState, type FormEvent } from "react";

type Stage = {
  public_id: string;
  name: string;
  position: number;
  is_initial: boolean;
  participation_mode: "individual" | "team_formation" | "team_locked";
};
type Transition = { public_id: string; from_stage: string; to_stage: string };
type GraphStatus =
  { valid: true; order: string[] } | { valid: false; errors: string[] };
type EvidenceRow = {
  created_at: string;
  actor: string | null;
  stage_public_id: string;
  metadata: {
    strategy: string;
    advanced: { subject_type: string; subject_id: string }[];
  };
};

function message(error: unknown): string {
  if (typeof error === "string") return error;
  if (error instanceof Error) return error.message;
  if (Array.isArray(error)) return error.map(message).join(" ");
  if (error && typeof error === "object") {
    return Object.entries(error)
      .map(([key, value]) => `${key}: ${message(value)}`)
      .join(" ");
  }
  return "Request failed.";
}

async function request<T>(
  path: string,
  method = "GET",
  body?: object,
): Promise<T> {
  const response = await fetch(path, {
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
      /* Retain status message. */
    }
    throw new Error(message(detail));
  }
  return response.status === 204
    ? (undefined as T)
    : (response.json() as Promise<T>);
}

function parseCandidates(text: string) {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [subject_id, score] = line.split(",").map((part) => part.trim());
      return {
        subject_type: "team",
        subject_id,
        ...(score ? { score: Number(score) } : {}),
      };
    });
}

export function StageBuilder({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/`;
  const [stages, setStages] = useState<Stage[]>([]);
  const [transitions, setTransitions] = useState<Transition[]>([]);
  const [graph, setGraph] = useState<GraphStatus | null>(null);
  const [strategies, setStrategies] = useState<string[]>([]);
  const [evidence, setEvidence] = useState<EvidenceRow[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const [stageName, setStageName] = useState("");
  const [stageInitial, setStageInitial] = useState(false);
  const [fromStage, setFromStage] = useState("");
  const [toStage, setToStage] = useState("");
  const [advanceFrom, setAdvanceFrom] = useState("");
  const [advanceTo, setAdvanceTo] = useState("");
  const [strategy, setStrategy] = useState("everyone");
  const [candidateText, setCandidateText] = useState("");

  async function refresh() {
    const [nextStages, nextTransitions, nextGraph, nextEvidence] =
      await Promise.all([
        request<Stage[]>(base + "stages/"),
        request<Transition[]>(base + "stage-transitions/"),
        request<GraphStatus>(base + "stage-graph/validate/"),
        request<EvidenceRow[]>(base + "stage-evidence/"),
      ]);
    setStages(nextStages);
    setTransitions(nextTransitions);
    setGraph(nextGraph);
    setEvidence(nextEvidence);
    if (nextStages[0] && !strategies.length) {
      const { strategies: available } = await request<{
        strategies: string[];
      }>(base + `stages/${nextStages[0].public_id}/advance/`);
      setStrategies(available);
    }
  }

  useEffect(() => {
    let active = true;
    refresh().catch((cause: unknown) => {
      if (active) setError(message(cause));
    });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [base]);

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

  function addStage(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (!stageName.trim()) throw new Error("Stage name is required.");
      await request<Stage>(base + "stages/", "POST", {
        name: stageName.trim(),
        is_initial: stageInitial,
      });
      setStageName("");
      setStageInitial(false);
      await refresh();
    });
  }

  function deleteStage(publicId: string) {
    void run(async () => {
      await request<void>(base + `stages/${publicId}/`, "DELETE");
      await refresh();
    });
  }

  function addTransition(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (!fromStage || !toStage)
        throw new Error("Choose both a from-stage and a to-stage.");
      await request<Transition>(base + "stage-transitions/", "POST", {
        from_stage: fromStage,
        to_stage: toStage,
      });
      await refresh();
    });
  }

  function deleteTransition(publicId: string) {
    void run(async () => {
      await request<void>(base + `stage-transitions/${publicId}/`, "DELETE");
      await refresh();
    });
  }

  function runAdvancement(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (!advanceFrom || !advanceTo)
        throw new Error("Choose both a from-stage and a to-stage.");
      await request<{ advanced: unknown[] }>(
        base + `stages/${advanceFrom}/advance/`,
        "POST",
        {
          to_stage: advanceTo,
          strategy,
          candidates: parseCandidates(candidateText),
        },
      );
      await refresh();
    });
  }

  const stageName_ = (id: string) =>
    stages.find((s) => s.public_id === id)?.name ?? id;

  return (
    <section aria-label="Stage builder">
      <h2>Stages</h2>
      {error && <p role="alert">{error}</p>}
      {graph && (
        <p>
          Graph: {graph.valid ? "Valid" : `Invalid — ${graph.errors.join(" ")}`}
        </p>
      )}
      <ol aria-label="Stage order">
        {stages.map((stage) => (
          <li key={stage.public_id}>
            {stage.name}
            {stage.is_initial ? " (initial)" : ""} — {stage.participation_mode}{" "}
            <button
              type="button"
              disabled={busy}
              onClick={() => deleteStage(stage.public_id)}
            >
              Delete
            </button>
          </li>
        ))}
      </ol>
      <form onSubmit={addStage}>
        <h3>Add stage</h3>
        <label>
          Name{" "}
          <input
            value={stageName}
            onChange={(e) => setStageName(e.target.value)}
            required
          />
        </label>
        <label>
          Initial{" "}
          <input
            type="checkbox"
            checked={stageInitial}
            onChange={(e) => setStageInitial(e.target.checked)}
          />
        </label>
        <button disabled={busy}>Add stage</button>
      </form>

      <h3>Transitions</h3>
      <ul aria-label="Stage transitions">
        {transitions.map((t) => (
          <li key={t.public_id}>
            {stageName_(t.from_stage)} → {stageName_(t.to_stage)}{" "}
            <button
              type="button"
              disabled={busy}
              onClick={() => deleteTransition(t.public_id)}
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
      <form onSubmit={addTransition}>
        <label>
          From{" "}
          <select
            value={fromStage}
            onChange={(e) => setFromStage(e.target.value)}
          >
            <option value="" />
            {stages.map((s) => (
              <option key={s.public_id} value={s.public_id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          To{" "}
          <select value={toStage} onChange={(e) => setToStage(e.target.value)}>
            <option value="" />
            {stages.map((s) => (
              <option key={s.public_id} value={s.public_id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <button disabled={busy}>Add transition</button>
      </form>

      <h3>Advance</h3>
      <form onSubmit={runAdvancement}>
        <label>
          From{" "}
          <select
            value={advanceFrom}
            onChange={(e) => setAdvanceFrom(e.target.value)}
          >
            <option value="" />
            {stages.map((s) => (
              <option key={s.public_id} value={s.public_id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          To{" "}
          <select
            value={advanceTo}
            onChange={(e) => setAdvanceTo(e.target.value)}
          >
            <option value="" />
            {stages.map((s) => (
              <option key={s.public_id} value={s.public_id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Strategy{" "}
          <select
            value={strategy}
            onChange={(e) => setStrategy(e.target.value)}
          >
            {strategies.map((slug) => (
              <option key={slug} value={slug}>
                {slug}
              </option>
            ))}
          </select>
        </label>
        <label>
          Candidates (one per line: subject_id,score)
          <textarea
            value={candidateText}
            onChange={(e) => setCandidateText(e.target.value)}
          />
        </label>
        <button disabled={busy}>Run advancement</button>
      </form>

      <h3>Evidence</h3>
      <ul aria-label="Advancement evidence">
        {evidence.map((row, i) => (
          <li key={i}>
            {row.created_at} · {row.actor ?? "unknown"} ·{" "}
            {row.metadata.strategy} · {row.metadata.advanced.length} advanced
          </li>
        ))}
      </ul>
    </section>
  );
}
