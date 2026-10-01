import { useEffect, useState, type FormEvent } from "react";
import { EntityGrid } from "../../components/EntityGrid";
import { NotesDialog } from "../../components/NotesDialog";
import { apiRequest } from "../../lib/api";
import type { EntityRow } from "../../lib/entityQuery";

type Settings = {
  mode: "open" | "application" | "invite_only";
  capacity: number | null;
  waitlist_enabled: boolean;
};
type InviteCode = {
  public_id: string;
  code: string;
  max_uses: number;
  use_count: number;
  revoked_at: string | null;
};
type Application = { id: string; username: string; status: string };

function request<T>(
  url: string,
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE" = "GET",
  body?: object,
): Promise<T> {
  return apiRequest<T>(url, {
    method,
    body,
    describe: (status, detail) =>
      (detail as { detail?: string } | undefined)?.detail ||
      `Registration request failed (${status}).`,
  });
}

export function RegistrationPanel({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/`;
  const [settings, setSettings] = useState<Settings | null>(null);
  const [mode, setMode] = useState<Settings["mode"]>("open");
  const [capacity, setCapacity] = useState("");
  const [waitlistEnabled, setWaitlistEnabled] = useState(false);
  const [codes, setCodes] = useState<InviteCode[]>([]);
  const [maxUses, setMaxUses] = useState("1");
  const [listVersion, setListVersion] = useState(0);
  const [notes, setNotes] = useState<{ id: string; name: string } | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function refresh() {
    const [nextSettings, nextCodes] = await Promise.all([
      request<Settings>(base + "registration-settings/"),
      request<InviteCode[]>(base + "registration-invite-codes/"),
    ]);
    setSettings(nextSettings);
    setMode(nextSettings.mode);
    setCapacity(nextSettings.capacity?.toString() ?? "");
    setWaitlistEnabled(nextSettings.waitlist_enabled);
    setCodes(nextCodes);
  }

  useEffect(() => {
    let active = true;
    refresh().catch((cause: unknown) => {
      if (active)
        setError(
          cause instanceof Error
            ? cause.message
            : "Registration could not load.",
        );
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
      setError(
        cause instanceof Error ? cause.message : "Registration request failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  function saveSettings(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      await request<Settings>(base + "registration-settings/", "PUT", {
        mode,
        capacity: capacity.trim() === "" ? null : Number(capacity),
        waitlist_enabled: waitlistEnabled,
      });
      await refresh();
    });
  }

  function createCode(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      await request<InviteCode>(base + "registration-invite-codes/", "POST", {
        max_uses: Number(maxUses) || 1,
      });
      setMaxUses("1");
      await refresh();
    });
  }

  function revokeCode(code: InviteCode) {
    void run(async () => {
      await request<void>(
        base + `registration-invite-codes/${code.public_id}/`,
        "DELETE",
      );
      await refresh();
    });
  }

  function decide(application: Application, decision: string) {
    void run(async () => {
      await request<unknown>(
        base + `applications/${application.id}/decide/`,
        "POST",
        { decision },
      );
      await refresh();
      setListVersion((version) => version + 1);
    });
  }

  return (
    <section aria-label="Event registration">
      <h3>Registration</h3>
      {error && <p role="alert">{error}</p>}
      <form onSubmit={saveSettings}>
        <label>
          Mode{" "}
          <select
            value={mode}
            onChange={(event) =>
              setMode(event.target.value as Settings["mode"])
            }
          >
            <option value="open">Open</option>
            <option value="application">Application review</option>
            <option value="invite_only">Invite only</option>
          </select>
        </label>
        <label>
          Capacity (blank for unlimited){" "}
          <input
            type="number"
            min={1}
            value={capacity}
            onChange={(event) => setCapacity(event.target.value)}
          />
        </label>
        <label>
          <input
            type="checkbox"
            checked={waitlistEnabled}
            onChange={(event) => setWaitlistEnabled(event.target.checked)}
          />{" "}
          Waitlist once capacity is reached
        </label>
        <button disabled={busy}>Save registration settings</button>
        {settings && <p>Current mode: {settings.mode}</p>}
      </form>

      {mode === "invite_only" && (
        <>
          <h4>Invite codes</h4>
          <ul>
            {codes.map((code) => (
              <li key={code.public_id}>
                {code.code} · {code.use_count}/{code.max_uses} used
                {code.revoked_at ? " · revoked" : ""}
                {!code.revoked_at && (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => revokeCode(code)}
                  >
                    Revoke
                  </button>
                )}
              </li>
            ))}
          </ul>
          <form onSubmit={createCode}>
            <label>
              Max uses{" "}
              <input
                type="number"
                min={1}
                value={maxUses}
                onChange={(event) => setMaxUses(event.target.value)}
              />
            </label>
            <button disabled={busy}>Create invite code</button>
          </form>
        </>
      )}

      <h4>Applications</h4>
      <EntityGrid
        workspaceId={workspaceId}
        eventId={eventId}
        entity="applications"
        label="Applications"
        rowLabel={(row: EntityRow) => String(row.username ?? row.id)}
        refreshToken={listVersion}
        empty={<p>People who apply will appear here.</p>}
        actions={(row: EntityRow) => {
          const application = row as unknown as Application;
          const decidable =
            application.status === "pending" ||
            application.status === "waitlisted";
          return (
            <>
              <button
                type="button"
                aria-label={`Notes on ${application.username}`}
                onClick={() =>
                  setNotes({ id: application.id, name: application.username })
                }
              >
                Notes
              </button>
              {decidable && (
                <>
                  <button
                    type="button"
                    disabled={busy}
                    aria-label={`Approve ${application.username}`}
                    onClick={() => decide(application, "approved")}
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    aria-label={`Waitlist ${application.username}`}
                    onClick={() => decide(application, "waitlisted")}
                  >
                    Waitlist
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    aria-label={`Reject ${application.username}`}
                    onClick={() => decide(application, "rejected")}
                  >
                    Reject
                  </button>
                </>
              )}
            </>
          );
        }}
      />
      {notes && (
        <NotesDialog
          title={`Organizer notes on ${notes.name}`}
          subject={{
            workspaceId,
            eventId,
            type: "application",
            id: notes.id,
            audience: "organizers",
          }}
          onClose={() => setNotes(null)}
        />
      )}
    </section>
  );
}
