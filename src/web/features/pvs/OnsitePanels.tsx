import { useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { api, eventBase, messageOf, useLoad } from "./http";

type Summary = {
  participants: number;
  rsvp: { in_person: number; remote: number; not_attending: number };
  no_response: number;
  checked_in: number;
  projects: number;
  projects_placed: number;
  slots: number;
  slots_free: number;
};
type Location = {
  public_id: string;
  kind: "room" | "table" | "booth";
  name: string;
  capacity: number | null;
  assigned: number;
  parent: string | null;
};
type Placement = {
  project: string;
  project_name: string;
  location_name: string;
  kind: string;
  room: string | null;
};
type AttendanceRow = {
  person: string;
  username: string;
  mode: string;
  checked_in: boolean;
};
type AutoAssign = {
  applied: boolean;
  assignments: { project: string; location: string }[];
  unplaced: string[];
};

const MODE_LABEL: Record<string, string> = {
  in_person: "In person",
  remote: "Remote",
  not_attending: "Not attending",
};

/**
 * Check-in desk, room/table state and placements. Volunteers get the pass
 * scanner and read-only state; organizers also get manual check-in and
 * layout controls (the API enforces the same split).
 */
export function OnsiteOperationsPanel({
  workspaceId,
  eventId,
  canManage,
}: {
  workspaceId: string;
  eventId: string;
  canManage: boolean;
}) {
  const base = eventBase(workspaceId, eventId);
  const summary = useLoad<Summary>(`${base}onsite-summary/`);
  const attendance = useLoad<AttendanceRow[]>(`${base}attendance/`);
  const locations = useLoad<Location[]>(`${base}locations/`);
  const placements = useLoad<Placement[]>(`${base}project-locations/`);
  const [token, setToken] = useState("");
  const [status, setStatus] = useState("");
  const [problem, setProblem] = useState("");
  const [name, setName] = useState("");
  const [kind, setKind] = useState("table");
  const [capacity, setCapacity] = useState("");
  const [plan, setPlan] = useState<AutoAssign | null>(null);

  function refresh() {
    summary.reload();
    attendance.reload();
    locations.reload();
    placements.reload();
  }

  async function run(action: () => Promise<void>) {
    setProblem("");
    try {
      await action();
    } catch (cause) {
      setProblem(messageOf(cause));
    }
  }

  const scan = () =>
    run(async () => {
      const result = await api<{
        username: string;
        already_checked_in: boolean;
      }>(`${base}checkins/scan/`, "POST", { token: token.trim() });
      setStatus(
        result.already_checked_in
          ? `${result.username} was already checked in.`
          : `${result.username} checked in.`,
      );
      setToken("");
      refresh();
    });

  const manualCheckIn = (person: string, username: string) =>
    run(async () => {
      await api(`${base}check-ins/`, "POST", { participant: person });
      setStatus(`${username} checked in.`);
      refresh();
    });

  const addLocation = () =>
    run(async () => {
      await api(`${base}locations/`, "POST", {
        kind,
        name,
        ...(capacity ? { capacity: Number(capacity) } : {}),
      });
      setName("");
      setCapacity("");
      locations.reload();
      summary.reload();
    });

  const autoAssign = (apply: boolean) =>
    run(async () => {
      const result = await api<AutoAssign>(
        `${base}locations/auto-assign/`,
        "POST",
        { apply, kind: "table" },
      );
      setPlan(apply ? null : result);
      if (apply) {
        setStatus(`Placed ${result.assignments.length} projects.`);
        refresh();
      }
    });

  const nameOf = (id: string) =>
    placements.data?.find((row) => row.project === id)?.project_name ??
    locations.data?.find((row) => row.public_id === id)?.name ??
    id.slice(0, 8);

  return (
    <section aria-label="On-site operations">
      <h3>On-site operations</h3>
      {problem && <p role="alert">{problem}</p>}
      {status && <p role="status">{status}</p>}
      {summary.loading && <LoadingState label="Loading on-site summary…" />}
      {summary.error && (
        <ErrorState message={summary.error.message} onRetry={summary.reload} />
      )}
      {summary.data && (
        <p>
          {summary.data.checked_in} of {summary.data.participants} participants
          checked in · RSVP: {summary.data.rsvp.in_person} in person,{" "}
          {summary.data.rsvp.remote} remote, {summary.data.rsvp.not_attending}{" "}
          not attending, {summary.data.no_response} no response ·{" "}
          {summary.data.projects_placed} of {summary.data.projects} projects
          placed ({summary.data.slots_free} slots free)
        </p>
      )}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void scan();
        }}
      >
        <label>
          Scan or paste a participant pass{" "}
          <input
            required
            value={token}
            onChange={(event) => setToken(event.target.value)}
            autoComplete="off"
          />
        </label>{" "}
        <button>Check in</button>
      </form>
      {canManage && attendance.data && (
        <>
          {attendance.data.length === 0 ? (
            <EmptyState title="Nobody has RSVP'd yet." />
          ) : (
            <div
              className="cx-scroll-region"
              role="region"
              aria-label="Attendance table"
              tabIndex={0}
            >
              <table>
                <caption>Attendance and manual check-in</caption>
                <thead>
                  <tr>
                    <th scope="col">Participant</th>
                    <th scope="col">RSVP</th>
                    <th scope="col">Checked in</th>
                  </tr>
                </thead>
                <tbody>
                  {attendance.data.map((row) => (
                    <tr key={row.person}>
                      <th scope="row">{row.username}</th>
                      <td>{MODE_LABEL[row.mode] ?? row.mode}</td>
                      <td>
                        {row.checked_in ? (
                          <Badge tone="success">Checked in</Badge>
                        ) : (
                          <Button
                            variant="secondary"
                            onClick={() =>
                              void manualCheckIn(row.person, row.username)
                            }
                            aria-label={`Check in ${row.username}`}
                          >
                            Check in
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
      <h4>Rooms, tables and booths</h4>
      {locations.data && locations.data.length === 0 && (
        <EmptyState title="No rooms or tables have been set up." />
      )}
      {locations.data && locations.data.length > 0 && (
        <div
          className="cx-scroll-region"
          role="region"
          aria-label="Locations table"
          tabIndex={0}
        >
          <table>
            <thead>
              <tr>
                <th scope="col">Name</th>
                <th scope="col">Kind</th>
                <th scope="col">Capacity</th>
                <th scope="col">Assigned</th>
              </tr>
            </thead>
            <tbody>
              {locations.data.map((location) => (
                <tr key={location.public_id}>
                  <th scope="row">{location.name}</th>
                  <td>{location.kind}</td>
                  <td>{location.capacity ?? "–"}</td>
                  <td>{location.assigned}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {placements.data && placements.data.length > 0 && (
        <ul aria-label="Project placements">
          {placements.data.map((row) => (
            <li key={row.project}>
              {row.project_name} → {row.room ? `${row.room} / ` : ""}
              {row.location_name}
            </li>
          ))}
        </ul>
      )}
      {canManage && (
        <Card title="Layout" as="h4">
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void addLocation();
            }}
          >
            <label>
              Name{" "}
              <input
                required
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
            </label>{" "}
            <label>
              Kind{" "}
              <select
                value={kind}
                onChange={(event) => setKind(event.target.value)}
              >
                <option value="room">Room</option>
                <option value="table">Table</option>
                <option value="booth">Booth</option>
              </select>
            </label>{" "}
            <label>
              Capacity{" "}
              <input
                type="number"
                min={1}
                value={capacity}
                onChange={(event) => setCapacity(event.target.value)}
              />
            </label>{" "}
            <button>Add location</button>
          </form>
          <p>
            Auto-assign places projects with in-person members that have no
            table yet.
          </p>
          <Button variant="secondary" onClick={() => void autoAssign(false)}>
            Preview auto-assign
          </Button>
          {plan && (
            <div role="status">
              <p>
                {plan.assignments.length} placement
                {plan.assignments.length === 1 ? "" : "s"} proposed,{" "}
                {plan.unplaced.length} unplaced.
              </p>
              <ul>
                {plan.assignments.map((item) => (
                  <li key={item.project}>
                    {nameOf(item.project)} → {nameOf(item.location)}
                  </li>
                ))}
              </ul>
              {plan.assignments.length > 0 && (
                <Button onClick={() => void autoAssign(true)}>
                  Apply these placements
                </Button>
              )}
            </div>
          )}
        </Card>
      )}
    </section>
  );
}

/** Participant: RSVP, check-in pass and their expo table. */
export function MyOnsitePanel({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const base = eventBase(workspaceId, eventId);
  const mine = useLoad<{ mode: string | null }>(`${base}my-attendance/`);
  const pass = useLoad<{ token: string }>(`${base}my-pass/`);
  const [problem, setProblem] = useState("");
  const [saved, setSaved] = useState("");

  async function rsvp(mode: string) {
    setProblem("");
    setSaved("");
    try {
      await api(`${base}my-attendance/`, "PUT", { mode });
      setSaved(`RSVP saved: ${MODE_LABEL[mode]}.`);
      mine.reload();
    } catch (cause) {
      setProblem(messageOf(cause));
    }
  }

  return (
    <section aria-label="Attending in person">
      <h3>Attending</h3>
      {mine.loading && <LoadingState label="Loading your RSVP…" />}
      {mine.error && (
        <ErrorState message={mine.error.message} onRetry={mine.reload} />
      )}
      {problem && <p role="alert">{problem}</p>}
      {mine.data && (
        <label>
          Your RSVP{" "}
          <select
            value={mine.data.mode ?? ""}
            onChange={(event) => void rsvp(event.target.value)}
          >
            <option value="" disabled>
              Not answered yet
            </option>
            {Object.entries(MODE_LABEL).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
      )}
      {saved && <p role="status">{saved}</p>}
      {mine.data?.mode === "in_person" && pass.data && (
        <Card title="Your check-in pass" as="h4">
          <img
            src={`${base}my-pass/qr/`}
            alt="Check-in QR code"
            width={160}
            height={160}
          />
          <p>
            Show this code at the desk. If scanning fails, give a volunteer this
            pass text:
          </p>
          <code>{pass.data.token}</code>
        </Card>
      )}
    </section>
  );
}
