import { useEffect, useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";

type IdentityMode = "authenticated" | "email_link" | "token";
type Status = { identity_mode: IdentityMode; is_open: boolean } | null;
type Candidate = { project: string; name: string };
type Result = { project: string; name: string; votes: number };

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

async function request<T>(url: string, method = "GET", body?: object): Promise<T> {
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
      /* Retain status message. */
    }
    throw new Error(message(detail));
  }
  return response.status === 204 ? (undefined as T) : (response.json() as Promise<T>);
}

/** Public audience-choice voting (COM-*), embedded on the public event page.
 * Reachable without a workspace id -- see community.urls' public/ prefix. */
export function CommunityVoting({ eventId }: { eventId: string }) {
  const base = `/api/v1/public/events/${eventId}/voting`;
  const [status, setStatus] = useState<Status>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [results, setResults] = useState<Result[] | null>(null);
  const [voteToken, setVoteToken] = useState("");
  const [email, setEmail] = useState("");
  const [votedFor, setVotedFor] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    request<Status>(base + "/status/")
      .then(setStatus)
      .catch(() => undefined);
    request<Result[]>(base + "/results/")
      .then(setResults)
      .catch(() => undefined);
  }, [base]);

  useEffect(() => {
    if (!status) return;
    request<Candidate[]>(base + `/candidates/${voteToken ? `?token=${voteToken}` : ""}`)
      .then(setCandidates)
      .catch((cause: unknown) => setError(message(cause)));
  }, [base, status, voteToken]);

  async function requestEmailToken(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const response = await request<{ token: string }>(base + "/request-email-token/", "POST", {
        email,
      });
      setVoteToken(response.token);
      setNotice("A voting link would normally be emailed to you; using it here directly.");
    } catch (cause) {
      setError(message(cause));
    }
  }

  async function vote(project: string) {
    setError("");
    try {
      await request(base + "/votes/", "POST", {
        project,
        ...(voteToken ? { token: voteToken } : {}),
      });
      setVotedFor(project);
    } catch (cause) {
      setError(message(cause));
    }
  }

  if (!status) return null;

  return (
    <section aria-label="Community voting">
      <h2>Audience choice</h2>
      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}
      {!status.is_open && <p>Voting is not currently open.</p>}
      {status.is_open && status.identity_mode === "email_link" && !voteToken && (
        <form onSubmit={(event) => void requestEmailToken(event)}>
          <label>
            Email{" "}
            <input
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <Button>Request a voting link</Button>
        </form>
      )}
      {status.is_open && status.identity_mode === "token" && !voteToken && (
        <label>
          Voting token{" "}
          <input value={voteToken} onChange={(event) => setVoteToken(event.target.value)} />
        </label>
      )}
      {status.is_open && (voteToken || status.identity_mode !== "token") && (
        <ul>
          {candidates.map((candidate) => (
            <li key={candidate.project}>
              {candidate.name}{" "}
              {votedFor === candidate.project ? (
                <Badge tone="success">voted</Badge>
              ) : (
                <Button
                  variant="secondary"
                  disabled={!!votedFor}
                  onClick={() => void vote(candidate.project)}
                >
                  Vote
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}
      {results && (
        <>
          <h3>Results</h3>
          <ul>
            {results.map((result) => (
              <li key={result.project}>
                {result.name}: {result.votes}
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
