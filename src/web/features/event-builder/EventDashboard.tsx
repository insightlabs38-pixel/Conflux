import { useEffect, useRef, useState, type FormEvent } from "react";
import { PolicyBuilder } from "../policy-builder/PolicyBuilder";
import { StageBuilder } from "../stage-builder/StageBuilder";
import { TeamPanel } from "../teams/TeamPanel";
import { FormBuilder } from "../form-builder/FormBuilder";
import { PageBuilder } from "../page-builder/PageBuilder";
import { EvaluationBuilder } from "../judging/EvaluationBuilder";
import { CommunityVotingBuilder } from "../community-voting/CommunityVotingBuilder";
import { WebhooksPanel } from "../integrations/WebhooksPanel";
import { AwardsPanel } from "../awards/AwardsPanel";
import { OperationsCenter } from "../operations/OperationsCenter";
import { CommunicationsPanel } from "../communications/CommunicationsPanel";
import { ConfigHistoryPanel } from "../audit/ConfigHistoryPanel";
import { EventTemplatesPanel } from "./EventTemplatesPanel";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";

type Event = {
  public_id: string;
  name: string;
  slug: string;
  description: string;
  timezone: string;
  starts_at: string | null;
  ends_at: string | null;
  status: "draft" | "open" | "closed" | "archived";
  is_public: boolean;
  updated_at: string;
};
type Track = { public_id: string; name: string; description: string };
type Prize = {
  public_id: string;
  name: string;
  kind: string;
  track: string | null;
};
type Dashboard = {
  event: Event;
  track_count: number;
  base_prize_count: number;
  configuration_checks: string[];
};

function localDateTime(value: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
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

export function EventDashboard({ workspaceId }: { workspaceId: string }) {
  const base = `/api/v1/workspaces/${workspaceId}/events/`;
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const selectedRef = useRef("");
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [tracks, setTracks] = useState<Track[]>([]);
  const [prizes, setPrizes] = useState<Prize[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loadingEvents, setLoadingEvents] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [retry, setRetry] = useState(0);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [trackName, setTrackName] = useState("");
  const [prizeName, setPrizeName] = useState("");
  const [prizeKind, setPrizeKind] = useState("other");
  const [prizeAmount, setPrizeAmount] = useState("");
  const [prizeCurrency, setPrizeCurrency] = useState("");
  const [prizeTrack, setPrizeTrack] = useState("");

  const eventBase = `${base}${selectedId}/`;
  async function refresh(id = selectedId) {
    const list = await request<Event[]>(base);
    setEvents(list);
    setLoadError("");
    if (!id) return;
    const detailBase = `${base}${id}/`;
    const [health, nextTracks, nextPrizes] = await Promise.all([
      request<Dashboard>(detailBase + "dashboard/"),
      request<Track[]>(detailBase + "tracks/"),
      request<Prize[]>(detailBase + "base-prizes/"),
    ]);
    if (selectedRef.current !== id) return;
    setDashboard(health);
    setTracks(nextTracks);
    setPrizes(nextPrizes);
  }
  useEffect(() => {
    let active = true;
    setLoadingEvents(true);
    setLoadError("");
    request<Event[]>(base)
      .then((list) => {
        if (active) setEvents(list);
      })
      .catch((cause: unknown) => {
        if (active) setLoadError(message(cause));
      })
      .finally(() => {
        if (active) setLoadingEvents(false);
      });
    return () => {
      active = false;
    };
  }, [base, retry]);

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
  function choose(id: string) {
    selectedRef.current = id;
    setSelectedId(id);
    setDashboard(null);
    void run(() => refresh(id));
  }
  function createEvent(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (!name.trim() || !slug.trim())
        throw new Error("Name and slug are required.");
      const created = await request<Event>(base, "POST", {
        name: name.trim(),
        slug: slug.trim(),
      });
      setName("");
      setSlug("");
      selectedRef.current = created.public_id;
      setSelectedId(created.public_id);
      await refresh(created.public_id);
    });
  }
  function saveSettings(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const start = String(data.get("starts_at") || "");
    const end = String(data.get("ends_at") || "");
    void run(async () => {
      if (start && end && start >= end)
        throw new Error("End must be after start.");
      await request<Event>(eventBase, "PATCH", {
        name: String(data.get("name") || "").trim(),
        timezone: String(data.get("timezone") || "").trim(),
        starts_at: start ? new Date(start).toISOString() : null,
        ends_at: end ? new Date(end).toISOString() : null,
        is_public: data.get("is_public") === "on",
      });
      await refresh();
    });
  }
  function addTrack(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (!trackName.trim()) throw new Error("Track name is required.");
      await request<Track>(eventBase + "tracks/", "POST", {
        name: trackName.trim(),
      });
      setTrackName("");
      await refresh();
    });
  }
  function addPrize(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (!prizeName.trim()) throw new Error("Prize name is required.");
      if (
        prizeKind === "cash" &&
        (!prizeAmount || !/^[A-Za-z]{3}$/.test(prizeCurrency))
      ) {
        throw new Error(
          "Cash prizes require an amount and three-letter currency.",
        );
      }
      await request<Prize>(eventBase + "base-prizes/", "POST", {
        name: prizeName.trim(),
        kind: prizeKind,
        track: prizeTrack || null,
        ...(prizeKind === "cash"
          ? { amount: prizeAmount, currency: prizeCurrency.toUpperCase() }
          : {}),
      });
      setPrizeName("");
      setPrizeAmount("");
      setPrizeCurrency("");
      await refresh();
    });
  }
  function transition(status: Event["status"]) {
    void run(async () => {
      await request<Event>(eventBase + "status/", "POST", { status });
      await refresh();
    });
  }
  const selected = dashboard?.event;
  const nextStatus =
    selected?.status === "draft"
      ? "open"
      : selected?.status === "open"
        ? "closed"
        : selected?.status === "closed"
          ? "archived"
          : null;

  return (
    <section aria-label="Event dashboard">
      <h1>Events</h1>
      {error && <p role="alert">{error}</p>}
      {loadingEvents && <LoadingState label="Loading events…" />}
      {loadError && (
        <ErrorState
          message={loadError}
          onRetry={() => setRetry((count) => count + 1)}
        />
      )}
      <form onSubmit={createEvent}>
        <h2>Create event</h2>
        <label>
          Name{" "}
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </label>
        <label>
          Slug{" "}
          <input
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            required
          />
        </label>
        <button disabled={busy}>Create event</button>
      </form>
      <nav aria-label="Workspace events">
        {events.map((item) => (
          <button
            key={item.public_id}
            type="button"
            aria-current={selectedId === item.public_id ? "page" : undefined}
            onClick={() => choose(item.public_id)}
          >
            {item.name} ({item.status})
          </button>
        ))}
      </nav>
      {!loadingEvents && !loadError && events.length === 0 && (
        <p>No events yet. Create one to get started.</p>
      )}
      <EventTemplatesPanel workspaceId={workspaceId} onCreated={choose} />
      {selected && (
        <article>
          <h2>{selected.name}</h2>
          <p>
            Status: {selected.status} ·{" "}
            {selected.is_public ? "Public" : "Private"}
          </p>
          {dashboard.configuration_checks.length > 0 && (
            <section aria-label="Configuration checks">
              <h3>Configuration checks</h3>
              <ul>
                {dashboard.configuration_checks.map((check) => (
                  <li key={check}>{check}</li>
                ))}
              </ul>
            </section>
          )}
          <form
            onSubmit={saveSettings}
            key={selected.public_id + selected.updated_at}
          >
            <h3>Settings</h3>
            <label>
              Name <input name="name" defaultValue={selected.name} required />
            </label>
            <label>
              Timezone{" "}
              <input
                name="timezone"
                defaultValue={selected.timezone}
                required
              />
            </label>
            <label>
              Start{" "}
              <input
                name="starts_at"
                type="datetime-local"
                defaultValue={localDateTime(selected.starts_at)}
              />
            </label>
            <label>
              End{" "}
              <input
                name="ends_at"
                type="datetime-local"
                defaultValue={localDateTime(selected.ends_at)}
              />
            </label>
            <label>
              Public{" "}
              <input
                name="is_public"
                type="checkbox"
                defaultChecked={selected.is_public}
              />
            </label>
            <button disabled={busy || selected.status === "archived"}>
              Save settings
            </button>
          </form>
          {nextStatus && (
            <button
              type="button"
              disabled={busy}
              onClick={() => transition(nextStatus)}
            >
              Move to {nextStatus}
            </button>
          )}
          <section>
            <h3>Tracks ({dashboard.track_count})</h3>
            <ul>
              {tracks.map((track) => (
                <li key={track.public_id}>{track.name}</li>
              ))}
            </ul>
            <form onSubmit={addTrack}>
              <label>
                Track name{" "}
                <input
                  value={trackName}
                  onChange={(e) => setTrackName(e.target.value)}
                  required
                />
              </label>
              <button disabled={busy}>Add track</button>
            </form>
          </section>
          <section>
            <h3>Base prizes ({dashboard.base_prize_count})</h3>
            <ul>
              {prizes.map((prize) => (
                <li key={prize.public_id}>
                  {prize.name} ({prize.kind})
                </li>
              ))}
            </ul>
            <form onSubmit={addPrize}>
              <label>
                Prize name{" "}
                <input
                  value={prizeName}
                  onChange={(e) => setPrizeName(e.target.value)}
                  required
                />
              </label>
              <label>
                Type{" "}
                <select
                  value={prizeKind}
                  onChange={(e) => setPrizeKind(e.target.value)}
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
                  ].map((kind) => (
                    <option key={kind} value={kind}>
                      {kind}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Track{" "}
                <select
                  value={prizeTrack}
                  onChange={(e) => setPrizeTrack(e.target.value)}
                >
                  <option value="">All tracks</option>
                  {tracks.map((track) => (
                    <option key={track.public_id} value={track.public_id}>
                      {track.name}
                    </option>
                  ))}
                </select>
              </label>
              {prizeKind === "cash" && (
                <>
                  <label>
                    Amount{" "}
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={prizeAmount}
                      onChange={(e) => setPrizeAmount(e.target.value)}
                      required
                    />
                  </label>
                  <label>
                    Currency{" "}
                    <input
                      maxLength={3}
                      value={prizeCurrency}
                      onChange={(e) => setPrizeCurrency(e.target.value)}
                      required
                    />
                  </label>
                </>
              )}
              <button disabled={busy}>Add prize</button>
            </form>
          </section>
          <StageBuilder
            workspaceId={workspaceId}
            eventId={selected.public_id}
          />
          <PolicyBuilder
            workspaceId={workspaceId}
            eventId={selected.public_id}
          />
          <TeamPanel workspaceId={workspaceId} eventId={selected.public_id} />
          <FormBuilder workspaceId={workspaceId} eventId={selected.public_id} />
          <PageBuilder workspaceId={workspaceId} eventId={selected.public_id} />
          <EvaluationBuilder
            workspaceId={workspaceId}
            eventId={selected.public_id}
          />
          <CommunityVotingBuilder
            workspaceId={workspaceId}
            eventId={selected.public_id}
          />
          <WebhooksPanel
            key={`webhooks-${selected.public_id}`}
            workspaceId={workspaceId}
            eventId={selected.public_id}
          />
          <AwardsPanel
            key={`awards-${selected.public_id}`}
            workspaceId={workspaceId}
            eventId={selected.public_id}
          />
          <OperationsCenter
            key={`operations-${selected.public_id}`}
            workspaceId={workspaceId}
            eventId={selected.public_id}
          />
          <CommunicationsPanel
            key={`communications-${selected.public_id}`}
            workspaceId={workspaceId}
            eventId={selected.public_id}
          />
          <ConfigHistoryPanel
            key={`config-history-${selected.public_id}`}
            workspaceId={workspaceId}
            eventId={selected.public_id}
          />
        </article>
      )}
    </section>
  );
}
