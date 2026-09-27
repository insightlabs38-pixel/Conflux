import { useEffect, useState, type FormEvent } from "react";
import { Card } from "../../components/Card";

type Project = {
  public_id: string;
  name: string;
  track: string | null;
  has_finalized_submission: boolean;
};
type Track = { public_id: string; name: string };
type Fulfillment = {
  public_id: string;
  component_name: string;
  state: string;
  note: string;
};
type Winner = {
  public_id: string;
  project_name: string;
  override_reason: string;
  fulfillments: Fulfillment[];
};
type Component = {
  public_id: string;
  kind: string;
  name: string;
  amount: string | null;
  currency: string;
};
type Award = {
  public_id: string;
  name: string;
  selection_source: string;
  winner_count: number;
  eligibility_track: string | null;
  require_finalized_submission: boolean;
  published_at: string | null;
  winners: Winner[];
  components: Component[];
};
type Proposal = {
  search_limited: boolean;
  awards: {
    award: string;
    name: string;
    existing: string[];
    proposed: string[];
    unfilled: number;
    blocker: string | null;
  }[];
};

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
    const problem = await response.json().catch(() => ({}));
    throw new Error(JSON.stringify(problem));
  }
  return response.json() as Promise<T>;
}

export function AwardsPanel({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const eventBase = `/api/v1/workspaces/${workspaceId}/events/${eventId}/`;
  const base = eventBase + "awards/";
  const [awards, setAwards] = useState<Award[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [tracks, setTracks] = useState<Track[]>([]);
  const [name, setName] = useState("");
  const [source, setSource] = useState("manual");
  const [plan, setPlan] = useState("");
  const [count, setCount] = useState(1);
  const [track, setTrack] = useState("");
  const [requireFinal, setRequireFinal] = useState(true);
  const [allowStacking, setAllowStacking] = useState(true);
  const [conflictGroup, setConflictGroup] = useState("");
  const [selected, setSelected] = useState("");
  const [project, setProject] = useState("");
  const [reason, setReason] = useState("");
  const [fulfillmentNote, setFulfillmentNote] = useState("");
  const [componentName, setComponentName] = useState("");
  const [kind, setKind] = useState("cash");
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [error, setError] = useState("");
  const [proposals, setProposals] = useState<Proposal | null>(null);

  async function refresh() {
    setAwards(await request<Award[]>(base));
    setProposals(null);
  }
  useEffect(() => {
    let active = true;
    Promise.all([
      request<Award[]>(base),
      request<Project[]>(base + "candidates/"),
      request<Track[]>(eventBase + "tracks/"),
    ])
      .then(([nextAwards, nextProjects, nextTracks]) => {
        if (active) {
          setAwards(nextAwards);
          setProjects(nextProjects);
          setTracks(nextTracks);
        }
      })
      .catch((cause: Error) => {
        if (active) setError(cause.message);
      });
    return () => {
      active = false;
    };
  }, [base, eventBase]);

  async function create(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await request(base, "POST", {
        name,
        selection_source: source,
        evaluation_plan: source === "evaluation" ? plan : null,
        winner_count: count,
        eligibility_track: track || null,
        require_finalized_submission: requireFinal,
        allow_stacking: allowStacking,
        conflict_group: conflictGroup,
      });
      setName("");
      await refresh();
    } catch (cause) {
      setError((cause as Error).message);
    }
  }

  async function addWinner(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await request(`${base}${selected}/winners/`, "POST", {
        project,
        override_reason: reason,
      });
      setProject("");
      setReason("");
      await refresh();
    } catch (cause) {
      setError((cause as Error).message);
    }
  }

  async function addComponent(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await request(`${base}${selected}/components/`, "POST", {
        name: componentName,
        kind,
        quantity: 1,
        ...(kind === "cash" ? { amount, currency } : {}),
      });
      setComponentName("");
      setAmount("");
      await refresh();
    } catch (cause) {
      setError((cause as Error).message);
    }
  }

  async function publish() {
    setError("");
    try {
      await request(`${base}${selected}/publish/`, "POST");
      await refresh();
    } catch (cause) {
      setError((cause as Error).message);
    }
  }

  async function previewAllocations() {
    setError("");
    try {
      setProposals(await request<Proposal>(base + "proposals/"));
    } catch (cause) {
      setError((cause as Error).message);
    }
  }

  async function advance(fulfillment: Fulfillment, state: string) {
    setError("");
    try {
      await request(
        `${base}${selected}/fulfillments/${fulfillment.public_id}/`,
        "PATCH",
        {
          state,
          note: fulfillmentNote,
        },
      );
      setFulfillmentNote("");
      await refresh();
    } catch (cause) {
      setError((cause as Error).message);
    }
  }

  const current = awards.find((award) => award.public_id === selected);
  return (
    <Card title="Awards and prizes">
      {error && <p role="alert">{error}</p>}
      <form onSubmit={create}>
        <label>
          Award name{" "}
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            required
          />
        </label>
        <label>
          Selection source{" "}
          <select
            value={source}
            onChange={(event) => setSource(event.target.value)}
          >
            <option value="manual">Manual</option>
            <option value="evaluation">Evaluation results</option>
            <option value="community">Community vote</option>
          </select>
        </label>
        {source === "evaluation" && (
          <label>
            Evaluation plan ID{" "}
            <input
              value={plan}
              onChange={(event) => setPlan(event.target.value)}
              required
            />
          </label>
        )}
        <label>
          Winner positions{" "}
          <input
            type="number"
            min="1"
            max="100"
            value={count}
            onChange={(event) => setCount(Number(event.target.value))}
            required
          />
        </label>
        <label>
          Eligible track{" "}
          <select
            value={track}
            onChange={(event) => setTrack(event.target.value)}
          >
            <option value="">All tracks</option>
            {tracks.map((item) => (
              <option key={item.public_id} value={item.public_id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          <input
            type="checkbox"
            checked={requireFinal}
            onChange={(event) => setRequireFinal(event.target.checked)}
          />{" "}
          Require finalized submission
        </label>
        <label>
          <input
            type="checkbox"
            checked={allowStacking}
            onChange={(event) => setAllowStacking(event.target.checked)}
          />{" "}
          Allow stacking with other awards
        </label>
        <label>
          Conflict group{" "}
          <input
            value={conflictGroup}
            onChange={(event) => setConflictGroup(event.target.value)}
            placeholder="Optional shared group"
          />
        </label>
        <button type="submit">Create award</button>
      </form>
      <section aria-label="Award allocation preview">
        <h3>Allocation preview</h3>
        <p>
          Suggestions respect eligibility, existing winners, stacking, and
          conflict groups. Select each winner to save it.
        </p>
        <button type="button" onClick={() => void previewAllocations()}>
          Preview allocations
        </button>
        {proposals && (
          <>
            {proposals.search_limited && (
              <p>
                Search limit reached; these suggestions may leave fillable
                positions.
              </p>
            )}
            <ul>
              {proposals.awards.map((item) => (
                <li key={item.award}>
                  <strong>{item.name}</strong>
                  {item.blocker && <span> · {item.blocker}</span>}
                  {item.proposed.map((projectId) => (
                    <button
                      key={projectId}
                      type="button"
                      onClick={() => {
                        setSelected(item.award);
                        setProject(projectId);
                      }}
                    >
                      Use{" "}
                      {projects.find(
                        (candidate) => candidate.public_id === projectId,
                      )?.name ?? projectId}
                    </button>
                  ))}
                  {item.unfilled > 0 && (
                    <span> · {item.unfilled} unfilled</span>
                  )}
                </li>
              ))}
            </ul>
          </>
        )}
      </section>
      <label>
        Manage award{" "}
        <select
          value={selected}
          onChange={(event) => {
            setSelected(event.target.value);
            setProject("");
          }}
        >
          <option value="">Choose an award</option>
          {awards.map((award) => (
            <option key={award.public_id} value={award.public_id}>
              {award.name}
            </option>
          ))}
        </select>
      </label>
      {current && (
        <section aria-label="Award operations">
          <p>
            {current.selection_source} · {current.winners.length}/
            {current.winner_count} winners ·{" "}
            {current.published_at ? "Published" : "Draft"}
          </p>
          <ul>
            {current.winners.map((winner) => (
              <li key={winner.public_id}>
                <strong>{winner.project_name}</strong>
                <ul>
                  {winner.fulfillments.map((fulfillment) => (
                    <li key={fulfillment.public_id}>
                      {fulfillment.component_name} · {fulfillment.state}
                      {fulfillment.state === "pending" && (
                        <button
                          type="button"
                          onClick={() => advance(fulfillment, "contacted")}
                        >
                          Mark contacted
                        </button>
                      )}
                      {fulfillment.state === "contacted" && (
                        <button
                          type="button"
                          onClick={() => advance(fulfillment, "verified")}
                        >
                          Mark verified
                        </button>
                      )}
                      {fulfillment.state === "verified" && (
                        <button
                          type="button"
                          onClick={() => advance(fulfillment, "sent")}
                        >
                          Mark sent
                        </button>
                      )}
                      {fulfillment.state === "sent" && (
                        <>
                          <button
                            type="button"
                            onClick={() => advance(fulfillment, "claimed")}
                          >
                            Mark claimed
                          </button>
                          <button
                            type="button"
                            onClick={() => advance(fulfillment, "failed")}
                          >
                            Mark failed
                          </button>
                        </>
                      )}
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
          <label>
            Fulfillment note{" "}
            <input
              value={fulfillmentNote}
              onChange={(event) => setFulfillmentNote(event.target.value)}
              placeholder="Required when marking failed"
            />
          </label>
          <ul>
            {current.components.map((component) => (
              <li key={component.public_id}>
                {component.name} ({component.kind}){" "}
                {component.amount &&
                  `${component.amount} ${component.currency}`}
              </li>
            ))}
          </ul>
          {!current.published_at && (
            <>
              <form onSubmit={addWinner}>
                <label>
                  Winning project{" "}
                  <select
                    value={project}
                    onChange={(event) => setProject(event.target.value)}
                    required
                  >
                    <option value="">Choose project</option>
                    {projects
                      .filter(
                        (item) =>
                          !current.eligibility_track ||
                          item.track === current.eligibility_track,
                      )
                      .filter(
                        (item) =>
                          !current.require_finalized_submission ||
                          item.has_finalized_submission,
                      )
                      .map((item) => (
                        <option key={item.public_id} value={item.public_id}>
                          {item.name}
                        </option>
                      ))}
                  </select>
                </label>
                <label>
                  Override reason, if outside source ranking{" "}
                  <input
                    value={reason}
                    onChange={(event) => setReason(event.target.value)}
                  />
                </label>
                <button type="submit">Select winner</button>
              </form>
              <form onSubmit={addComponent}>
                <label>
                  Prize component{" "}
                  <input
                    value={componentName}
                    onChange={(event) => setComponentName(event.target.value)}
                    required
                  />
                </label>
                <label>
                  Type{" "}
                  <select
                    value={kind}
                    onChange={(event) => setKind(event.target.value)}
                  >
                    {[
                      "cash",
                      "credit",
                      "discount",
                      "subscription",
                      "hardware",
                      "travel",
                      "service",
                      "mentorship",
                      "swag",
                      "other",
                    ].map((value) => (
                      <option key={value} value={value}>
                        {value}
                      </option>
                    ))}
                  </select>
                </label>
                {kind === "cash" && (
                  <>
                    <label>
                      Amount{" "}
                      <input
                        type="number"
                        min="0.01"
                        step="0.01"
                        value={amount}
                        onChange={(event) => setAmount(event.target.value)}
                        required
                      />
                    </label>
                    <label>
                      Currency{" "}
                      <input
                        maxLength={3}
                        value={currency}
                        onChange={(event) => setCurrency(event.target.value)}
                        required
                      />
                    </label>
                  </>
                )}
                <button type="submit">Add component</button>
              </form>
              <button
                type="button"
                onClick={publish}
                disabled={current.winners.length !== current.winner_count}
              >
                Publish winners
              </button>
            </>
          )}
        </section>
      )}
    </Card>
  );
}
