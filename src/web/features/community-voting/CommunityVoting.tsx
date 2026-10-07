import { useState } from "react";
import { Status } from "../../components/Status";
import { Button } from "../../components/Button";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { apiJson } from "../../lib/api";
import { useLoad } from "../../hooks/useLoad";

type IdentityMode = "authenticated" | "email_link" | "token";
type Status = {
  identity_mode: IdentityMode;
  is_open: boolean;
  results_published?: boolean;
} | null;
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

/** Public audience-choice voting (COM-*), embedded on the public event page.
 * Reachable without a workspace id -- see community.urls' public/ prefix. */
export function CommunityVoting({ eventId }: { eventId: string }) {
  const base = `/api/v1/public/events/${eventId}/voting`;
  const [voteToken, setVoteToken] = useState("");
  const [email, setEmail] = useState("");
  const [votedFor, setVotedFor] = useState("");
  const [actionError, setActionError] = useState("");
  const [notice, setNotice] = useState("");
  const [voting, setVoting] = useState(false);

  const statusLoad = useLoad<Status>(base + "/status/", {
    absent: [404],
    describe: (code) => `Could not load voting (${code}).`,
  });
  const status = statusLoad.data ?? null;
  const statusState = statusLoad.error
    ? "error"
    : statusLoad.loading && statusLoad.data === null
      ? "loading"
      : status
        ? "ready"
        : "absent";
  // Unpublished results are a guaranteed 403 for the public; don't ask.
  const resultsLoad = useLoad<Result[]>(
    status && status.results_published !== false ? base + "/results/" : null,
    {
      absent: [403, 404],
      describe: (code) => `Could not load voting results (${code}).`,
    },
  );
  const results = resultsLoad.data;
  const resultsError = resultsLoad.error?.message ?? "";
  const candidatesLoad = useLoad<Candidate[]>(
    status
      ? base + `/candidates/${voteToken ? `?token=${voteToken}` : ""}`
      : null,
  );
  const candidates = candidatesLoad.data ?? [];
  const error =
    actionError ||
    statusLoad.error?.message ||
    candidatesLoad.error?.message ||
    "";
  const setError = setActionError;

  async function requestEmailToken(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const response = await apiJson<{ token: string }>(
        base + "/request-email-token/",
        "POST",
        {
          email,
        },
      );
      setVoteToken(response.token);
      setNotice(
        "A voting link would normally be emailed to you; using it here directly.",
      );
    } catch (cause) {
      setError(message(cause));
    }
  }

  async function vote(project: string) {
    if (voting || votedFor) return;
    setVoting(true);
    setError("");
    try {
      await apiJson(base + "/votes/", "POST", {
        project,
        ...(voteToken ? { token: voteToken } : {}),
      });
      setVotedFor(project);
    } catch (cause) {
      setError(message(cause));
    } finally {
      setVoting(false);
    }
  }

  if (statusState === "loading")
    return <LoadingState label="Loading voting…" />;
  if (statusState === "error")
    return <ErrorState message={error} onRetry={statusLoad.reload} />;
  if (!status) return null;

  return (
    <section aria-label="Community voting">
      <h2>Audience choice</h2>
      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}
      {resultsError && <p role="alert">{resultsError}</p>}
      {!status.is_open && <p>Voting is not currently open.</p>}
      {status.is_open &&
        status.identity_mode === "email_link" &&
        !voteToken && (
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
            <Button variant="primary" type="submit">
              Request a voting link
            </Button>
          </form>
        )}
      {status.is_open && status.identity_mode === "token" && !voteToken && (
        <label>
          Voting token{" "}
          <input
            value={voteToken}
            onChange={(event) => setVoteToken(event.target.value)}
          />
        </label>
      )}
      {status.is_open && (voteToken || status.identity_mode !== "token") && (
        <ul>
          {candidates.map((candidate) => (
            <li key={candidate.project}>
              {candidate.name}{" "}
              {votedFor === candidate.project ? (
                <Status tone="success">voted</Status>
              ) : (
                <Button
                  variant="secondary"
                  disabled={!!votedFor || voting}
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
