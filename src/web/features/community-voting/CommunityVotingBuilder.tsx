import { useEffect, useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { FraudReview } from "./FraudReview";

type IdentityMode = "authenticated" | "email_link" | "token";
type CommentVisibility = "organizer" | "organizer_judge" | "everyone";
type Plan = {
  public_id: string;
  identity_mode: IdentityMode;
  opens_at: string;
  closes_at: string;
  allow_comments: boolean;
  comment_visibility: CommentVisibility;
  results_published_at: string | null;
};
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

function toLocalInput(value: string): string {
  const date = new Date(value);
  return new Date(date.getTime() - date.getTimezoneOffset() * 60_000).toISOString().slice(0, 16);
}

export function CommunityVotingBuilder({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/voting-plan/`;
  const [plan, setPlan] = useState<Plan | null>(null);
  const [tokenCount, setTokenCount] = useState(20);
  const [issuedTokens, setIssuedTokens] = useState<string[]>([]);
  const [results, setResults] = useState<Result[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    request<Plan>(base)
      .then(setPlan)
      .catch((cause: unknown) => setError(message(cause)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [base]);

  async function patch(fields: Partial<Plan>) {
    setError("");
    try {
      setPlan(await request<Plan>(base, "PATCH", fields));
    } catch (cause) {
      setError(message(cause));
    }
  }

  async function issueTokens() {
    setError("");
    try {
      const tokens = await request<{ token: string }[]>(base + "tokens/", "POST", {
        count: tokenCount,
      });
      setIssuedTokens(tokens.map((t) => t.token));
    } catch (cause) {
      setError(message(cause));
    }
  }

  async function publishResults() {
    setError("");
    try {
      setPlan(await request<Plan>(base + "publish-results/", "POST"));
      setResults(
        await request<Result[]>(
          `/api/v1/workspaces/${workspaceId}/events/${eventId}/voting/results/`,
        ),
      );
    } catch (cause) {
      setError(message(cause));
    }
  }

  if (!plan) return null;

  return (
    <>
    <Card title="Community voting">
      {error && <p role="alert">{error}</p>}
      <label>
        Identity mode{" "}
        <select
          value={plan.identity_mode}
          onChange={(e) => void patch({ identity_mode: e.target.value as IdentityMode })}
        >
          <option value="authenticated">Authenticated workspace member</option>
          <option value="email_link">Email magic link</option>
          <option value="token">Pre-issued token</option>
        </select>
      </label>
      <label>
        Opens{" "}
        <input
          type="datetime-local"
          value={toLocalInput(plan.opens_at)}
          onChange={(e) => void patch({ opens_at: new Date(e.target.value).toISOString() })}
        />
      </label>
      <label>
        Closes{" "}
        <input
          type="datetime-local"
          value={toLocalInput(plan.closes_at)}
          onChange={(e) => void patch({ closes_at: new Date(e.target.value).toISOString() })}
        />
      </label>
      <label>
        <input
          type="checkbox"
          checked={plan.allow_comments}
          onChange={(e) => void patch({ allow_comments: e.target.checked })}
        />{" "}
        Allow comments
      </label>
      <label>
        Comment visibility{" "}
        <select
          value={plan.comment_visibility}
          onChange={(e) => void patch({ comment_visibility: e.target.value as CommentVisibility })}
        >
          <option value="everyone">Any workspace member</option>
          <option value="organizer_judge">Organizers and judges</option>
          <option value="organizer">Organizer only</option>
        </select>
      </label>

      {plan.identity_mode === "token" && (
        <div>
          <label>
            Tokens to issue{" "}
            <input
              type="number"
              min={1}
              max={500}
              value={tokenCount}
              onChange={(e) => setTokenCount(Number(e.target.value))}
            />
          </label>
          <Button variant="secondary" onClick={() => void issueTokens()}>
            Issue tokens
          </Button>
          {issuedTokens.length > 0 && (
            <p>
              Issued {issuedTokens.length} tokens: {issuedTokens.join(", ")}
            </p>
          )}
        </div>
      )}

      <p>
        Results:{" "}
        <Badge tone={plan.results_published_at ? "success" : "neutral"}>
          {plan.results_published_at ? "published" : "not published"}
        </Badge>
      </p>
      <Button onClick={() => void publishResults()}>Publish results</Button>
      {results && (
        <ul>
          {results.map((result) => (
            <li key={result.project}>
              {result.name}: {result.votes}
            </li>
          ))}
        </ul>
      )}
    </Card>
    <FraudReview workspaceId={workspaceId} eventId={eventId} />
    </>
  );
}
