import { useEffect, useState, type FormEvent } from "react";

type PolicyRow = { public_id: string; name: string; ast: object };
type Binding = { public_id: string; action: string; policy: string };
type Gate = {
  public_id: string;
  name: string;
  opens_at: string | null;
  closes_at: string | null;
};
type Preset = { label: string; params: string[] };
type TraceNode = {
  path: number[];
  op: string | null;
  status: string;
  result?: boolean;
  fact?: string;
  expected?: unknown;
  actual?: unknown;
  error?: string;
  children?: TraceNode[];
};
type DebugResult = {
  allowed: boolean;
  policy_allowed: boolean | null;
  policy: { name: string } | null;
  reason: string;
  exception_grant_reason: string | null;
  error: string | null;
  trace: TraceNode | null;
};

const ACTIONS = ["submit", "join", "advance", "vote", "award"];

function Trace({ node }: { node: TraceNode }) {
  return (
    <li>
      <span>
        {node.op ?? "invalid node"}: {node.status}
        {node.result !== undefined
          ? ` (${node.result ? "true" : "false"})`
          : ""}
        {node.fact
          ? ` — ${node.fact} = ${JSON.stringify(node.actual)}; expected ${JSON.stringify(node.expected)}`
          : ""}
        {node.error ? ` — ${node.error}` : ""}
      </span>
      {node.children?.length ? (
        <ul>
          {node.children.map((child) => (
            <Trace key={child.path.join(".")} node={child} />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

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

export function PolicyBuilder({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/`;
  const [presets, setPresets] = useState<Record<string, Preset>>({});
  const [policies, setPolicies] = useState<PolicyRow[]>([]);
  const [bindings, setBindings] = useState<Binding[]>([]);
  const [gates, setGates] = useState<Gate[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const [policyName, setPolicyName] = useState("");
  const [presetSlug, setPresetSlug] = useState("everyone");
  const [gateNameParam, setGateNameParam] = useState("");
  const [bindPolicy, setBindPolicy] = useState("");
  const [bindAction, setBindAction] = useState(ACTIONS[0]);
  const [gateName, setGateName] = useState("");
  const [debugAction, setDebugAction] = useState(ACTIONS[0]);
  const [debugSubjectId, setDebugSubjectId] = useState("");
  const [debugResult, setDebugResult] = useState<DebugResult | null>(null);

  async function refresh() {
    const [nextPresets, nextPolicies, nextBindings, nextGates] =
      await Promise.all([
        request<Record<string, Preset>>(base + "policy-presets/"),
        request<PolicyRow[]>(base + "policies/"),
        request<Binding[]>(base + "policy-bindings/"),
        request<Gate[]>(base + "temporal-gates/"),
      ]);
    setPresets(nextPresets);
    setBindings(nextBindings);
    setPolicies(nextPolicies);
    setGates(nextGates);
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

  function addPolicy(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (!policyName.trim()) throw new Error("Policy name is required.");
      const params = presets[presetSlug]?.params.includes("gate_name")
        ? { gate_name: gateNameParam }
        : undefined;
      await request<PolicyRow>(base + "policies/", "POST", {
        name: policyName.trim(),
        preset: presetSlug,
        ...(params ? { preset_params: params } : {}),
      });
      setPolicyName("");
      await refresh();
    });
  }

  function addBinding(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (!bindPolicy) throw new Error("Choose a policy to bind.");
      await request<Binding>(base + "policy-bindings/", "POST", {
        action: bindAction,
        policy: bindPolicy,
      });
      await refresh();
    });
  }

  function addGate(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (!gateName.trim()) throw new Error("Gate name is required.");
      await request<Gate>(base + "temporal-gates/", "POST", {
        name: gateName.trim(),
      });
      setGateName("");
      await refresh();
    });
  }

  const policyName_ = (id: string) =>
    policies.find((p) => p.public_id === id)?.name ?? id;

  function debugPolicy(event: FormEvent) {
    event.preventDefault();
    setDebugResult(null);
    void run(async () => {
      const subject_type =
        debugAction === "submit"
          ? "project"
          : debugAction === "join"
            ? "team"
            : null;
      const body = {
        action: debugAction,
        ...(subject_type && debugSubjectId.trim()
          ? { subject_type, subject_id: debugSubjectId.trim() }
          : {}),
      };
      setDebugResult(
        await request<DebugResult>(base + "policy-debug/", "POST", body),
      );
    });
  }

  return (
    <section aria-label="Policy builder">
      <h2>Policies</h2>
      {error && <p role="alert">{error}</p>}

      <ul aria-label="Policy list">
        {policies.map((p) => (
          <li key={p.public_id}>
            {p.name}: {JSON.stringify(p.ast)}
          </li>
        ))}
      </ul>
      <form onSubmit={addPolicy}>
        <h3>Add policy</h3>
        <label>
          Name{" "}
          <input
            value={policyName}
            onChange={(e) => setPolicyName(e.target.value)}
            required
          />
        </label>
        <label>
          Rule{" "}
          <select
            value={presetSlug}
            onChange={(e) => setPresetSlug(e.target.value)}
          >
            {Object.entries(presets).map(([slug, preset]) => (
              <option key={slug} value={slug}>
                {preset.label}
              </option>
            ))}
          </select>
        </label>
        {presets[presetSlug]?.params.includes("gate_name") && (
          <label>
            Gate name{" "}
            <input
              value={gateNameParam}
              onChange={(e) => setGateNameParam(e.target.value)}
              required
            />
          </label>
        )}
        <button disabled={busy}>Add policy</button>
      </form>

      <h3>Action bindings</h3>
      <ul aria-label="Policy bindings">
        {bindings.map((b) => (
          <li key={b.public_id}>
            {b.action} → {policyName_(b.policy)}
          </li>
        ))}
      </ul>
      <form onSubmit={addBinding}>
        <label>
          Action{" "}
          <select
            value={bindAction}
            onChange={(e) => setBindAction(e.target.value)}
          >
            {ACTIONS.map((action) => (
              <option key={action} value={action}>
                {action}
              </option>
            ))}
          </select>
        </label>
        <label>
          Policy{" "}
          <select
            value={bindPolicy}
            onChange={(e) => setBindPolicy(e.target.value)}
          >
            <option value="" />
            {policies.map((p) => (
              <option key={p.public_id} value={p.public_id}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
        <button disabled={busy}>Bind policy to action</button>
      </form>

      <h3>Temporal gates</h3>
      <ul aria-label="Temporal gates">
        {gates.map((g) => (
          <li key={g.public_id}>
            {g.name}: {g.opens_at ?? "always open"} –{" "}
            {g.closes_at ?? "never closes"}
          </li>
        ))}
      </ul>
      <form onSubmit={addGate}>
        <label>
          Gate name{" "}
          <input
            value={gateName}
            onChange={(e) => setGateName(e.target.value)}
            required
          />
        </label>
        <button disabled={busy}>Add gate</button>
      </form>

      <h3>Policy debugger</h3>
      <p>
        Shows the policy decision at the current server time. Other action rules
        may still block the operation.
      </p>
      <form onSubmit={debugPolicy}>
        <label>
          Debug action{" "}
          <select
            value={debugAction}
            onChange={(e) => {
              setDebugAction(e.target.value);
              setDebugSubjectId("");
              setDebugResult(null);
            }}
          >
            {ACTIONS.map((action) => (
              <option key={action} value={action}>
                {action}
              </option>
            ))}
          </select>
        </label>
        {(debugAction === "submit" || debugAction === "join") && (
          <label>
            {debugAction === "submit" ? "Project ID" : "Team ID"} for grant
            check{" "}
            <input
              value={debugSubjectId}
              onChange={(e) => setDebugSubjectId(e.target.value)}
            />
          </label>
        )}
        <button disabled={busy}>Check policy</button>
      </form>
      {debugResult && (
        <div aria-label="Policy debug result">
          <p>
            {debugResult.allowed ? "Allowed by policy" : "Denied by policy"}:{" "}
            {debugResult.reason}
          </p>
          <p>Bound policy: {debugResult.policy?.name ?? "none"}</p>
          {debugResult.exception_grant_reason && (
            <p>Exception grant: {debugResult.exception_grant_reason}</p>
          )}
          {debugResult.error && <p>Evaluation error: {debugResult.error}</p>}
          {debugResult.trace && (
            <ul aria-label="Policy trace">
              <Trace node={debugResult.trace} />
            </ul>
          )}
        </div>
      )}
    </section>
  );
}
