import { useCallback, useMemo, useState } from "react";
import { BulkPlanner } from "../../components/BulkPlanner";
import { NotesDialog } from "../../components/NotesDialog";
import { EntityGrid } from "../../components/EntityGrid";
import { Button } from "../../components/Button";
import { countOf } from "../../lib/selection";

const CHUNK = 100; // the planner takes at most 100 explicit targets per operation

/**
 * Every project of the event as a grid, with the one bulk action organizers reach for first:
 * select projects, pick a track, see exactly what would change, apply, keep the receipt.
 */
export function ProjectsGrid({
  workspaceId,
  eventId,
  tracks,
}: {
  workspaceId: string;
  eventId: string;
  tracks: { public_id: string; name: string }[];
}) {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [track, setTrack] = useState("");
  const [planning, setPlanning] = useState(false);
  const [version, setVersion] = useState(0);
  const [notes, setNotes] = useState<{ id: string; name: string } | null>(null);
  const ids = useMemo(() => [...selected], [selected]);
  const names = useMemo(
    () => ({
      tracks: Object.fromEntries(tracks.map((t) => [t.public_id, t.name])),
    }),
    [tracks],
  );
  const trackName = tracks.find((t) => t.public_id === track)?.name ?? "";

  const operations = useMemo(() => {
    const chunks = [];
    for (let i = 0; i < ids.length; i += CHUNK)
      chunks.push({
        action: "move",
        projects: ids.slice(i, i + CHUNK),
        track,
      });
    return chunks;
  }, [ids, track]);

  // "Move 3 projects to Track A" in the palette: it fills in the track and opens the same preview
  // as the button, so the consequence step is never skipped
  const moveCommands = useCallback(
    (chosen: string[]) =>
      chosen.length > CHUNK * 20
        ? []
        : tracks.map((t) => ({
            id: `move-${t.public_id}`,
            label: `Move ${countOf(chosen.length, "projects")} to ${t.name}`,
            run: () => {
              setTrack(t.public_id);
              setPlanning(true);
            },
          })),
    [tracks],
  );

  return (
    <div>
      {selected.size > 0 && (
        <div role="group" aria-label="Bulk actions">
          <span role="status">{selected.size} selected</span>{" "}
          <label>
            Move to track{" "}
            <select value={track} onChange={(e) => setTrack(e.target.value)}>
              <option value="" />
              {tracks.map((t) => (
                <option key={t.public_id} value={t.public_id}>
                  {t.name}
                </option>
              ))}
            </select>
          </label>
          <Button
            variant="secondary"
            disabled={!track || operations.length > 20}
            onClick={() => setPlanning(true)}
          >
            Preview move
          </Button>
          {tracks.length === 0 && (
            <span className="cx-muted"> Add a track under Setup first.</span>
          )}
        </div>
      )}
      <EntityGrid
        workspaceId={workspaceId}
        eventId={eventId}
        entity="projects"
        label="Projects"
        rowLabel={(row) => String(row.name ?? row.id)}
        selectable
        onSelect={setSelected}
        selectionCommands={moveCommands}
        actions={(row) => (
          <Button
            variant="secondary"
            aria-label={`Notes on ${String(row.name ?? row.id)}`}
            onClick={() =>
              setNotes({ id: String(row.id), name: String(row.name ?? row.id) })
            }
          >
            Notes
          </Button>
        )}
        refreshToken={version}
        empty={<p>Projects appear here once teams create them.</p>}
      />
      {notes && (
        <NotesDialog
          title={`Organizer notes on ${notes.name}`}
          subject={{
            workspaceId,
            eventId,
            type: "project",
            id: notes.id,
            audience: "organizers",
          }}
          onClose={() => setNotes(null)}
        />
      )}
      {planning && (
        <BulkPlanner
          workspaceId={workspaceId}
          eventId={eventId}
          title={`Move ${selected.size} ${selected.size === 1 ? "project" : "projects"} to ${trackName}`}
          applyLabel={`Move to ${trackName}`}
          operations={operations}
          names={names}
          onApplied={() => {
            setVersion((v) => v + 1);
            setSelected(new Set());
          }}
          onClose={() => setPlanning(false)}
        />
      )}
    </div>
  );
}
