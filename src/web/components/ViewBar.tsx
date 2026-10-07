import { useEffect, useState } from "react";
import { useUrlParam } from "../lib/urlState";
import {
  createView,
  deleteView,
  sameDefinition,
  updateView,
  useSavedViews,
  viewsBase,
  type SavedView,
  type ViewDefinition,
} from "../lib/savedViews";
import { Button } from "./Button";
import { useMe } from "../hooks/useMe";
import {
  rememberView,
  togglePinnedView,
  usePinnedViews,
} from "../lib/shellPreferences";

/**
 * Pick, save, rename, share and delete saved views of one entity. The selected view is the `view_<entity>`
 * URL param (a public id, so a link reopens it); an id that is not in the list (deleted, private to
 * someone else, another event) is dropped with `replace`. `current` is what the list shows now, so
 * the bar can say when it differs from the selected view.
 */
export function ViewBar({
  workspaceId,
  eventId,
  entity,
  current,
  onApply,
}: {
  workspaceId: string;
  eventId: string;
  entity: string;
  current: ViewDefinition;
  /** A view was chosen (or cleared: null): show the list as that definition. */
  onApply: (view: SavedView | null) => void;
}) {
  const base = viewsBase(workspaceId, eventId);
  const load = useSavedViews(base, entity);
  // One param per entity: a page can hold several lists, and each only knows its own views.
  const [selectedId, select] = useUrlParam(`view_${entity}`);
  const [naming, setNaming] = useState<"new" | "rename" | null>(null);
  const [name, setName] = useState("");
  const [removing, setRemoving] = useState(false);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState("");
  const [note, setNote] = useState("");

  const user = useMe().data?.public_id ?? "";
  const pins = usePinnedViews(user, workspaceId);
  const views = load.data ?? [];
  const selected = views.find((v) => v.public_id === selectedId) ?? null;
  const pinned =
    !!selected &&
    pins.some(
      (pin) =>
        pin.event === eventId &&
        pin.entity === entity &&
        pin.view === selected.public_id,
    );
  const changed = selected ? !sameDefinition(selected.query, current) : false;

  // An unknown or no-longer-visible id falls back to "no view"; the URL is corrected quietly.
  useEffect(() => {
    if (load.data && !load.loading && selectedId && !selected)
      select("", { replace: true });
  }, [load.data, load.loading, selectedId, selected, select]);
  // A view opened from a link is applied once it is known.
  const [applied, setApplied] = useState("");
  useEffect(() => {
    if (selected && applied !== selected.public_id) {
      setApplied(selected.public_id);
      onApply(selected);
    }
  }, [selected, applied, onApply]);

  async function act(work: () => Promise<void>, done: string) {
    setBusy(true);
    setFailure("");
    setNote("");
    try {
      await work();
      await load.reload();
      setNote(done);
    } catch (cause) {
      setFailure(cause instanceof Error ? cause.message : "Request failed.");
    } finally {
      setBusy(false);
    }
  }

  const mine = views.filter((v) => v.mine);
  const shared = views.filter((v) => !v.mine);

  return (
    <div role="group" aria-label="Saved views">
      {load.error && (
        <p role="alert">
          {load.error.message}{" "}
          <button type="button" onClick={() => void load.reload()}>
            Try again
          </button>
        </p>
      )}
      <label>
        View{" "}
        <select
          value={selected?.public_id ?? ""}
          disabled={busy}
          onChange={(e) => {
            const next = views.find((v) => v.public_id === e.target.value);
            setApplied(next?.public_id ?? "");
            if (next)
              rememberView(user, workspaceId, {
                event: eventId,
                entity,
                view: next.public_id,
              });
            select(e.target.value, { replace: true });
            onApply(next ?? null);
            setNaming(null);
            setRemoving(false);
          }}
        >
          <option value="">Default</option>
          {mine.length > 0 && (
            <optgroup label="My views">
              {mine.map((v) => (
                <option key={v.public_id} value={v.public_id}>
                  {v.name}
                </option>
              ))}
            </optgroup>
          )}
          {shared.length > 0 && (
            <optgroup label="Shared by organizers">
              {shared.map((v) => (
                <option key={v.public_id} value={v.public_id}>
                  {v.name} ({v.owner})
                </option>
              ))}
            </optgroup>
          )}
        </select>
      </label>
      {selected && user && (
        <button
          type="button"
          aria-pressed={pinned}
          title="Pinned views are offered first in the palette (Ctrl K) on this device"
          onClick={() => {
            if (
              !togglePinnedView(user, workspaceId, {
                event: eventId,
                entity,
                view: selected.public_id,
              })
            )
              setNote("You can pin up to 12 views; unpin one first.");
          }}
        >
          {pinned ? "Unpin view" : "Pin view"}
        </button>
      )}
      {changed && <span role="status">Changed since saved</span>}
      {selected && !selected.mine && (
        <span className="cx-muted">
          Shared by {selected.owner}; save your changes as your own view.
        </span>
      )}

      <div>
        {selected?.mine && (
          <Button
            variant="secondary"
            disabled={busy || !changed}
            onClick={() =>
              void act(async () => {
                await updateView(base, selected, { query: current });
              }, "View saved.")
            }
          >
            Save
          </Button>
        )}
        <Button
          variant="secondary"
          disabled={busy}
          onClick={() => {
            setNaming("new");
            setName("");
          }}
        >
          Save as new view
        </Button>
        {selected?.mine && (
          <>
            <Button
              variant="secondary"
              disabled={busy}
              onClick={() => {
                setNaming("rename");
                setName(selected.name);
              }}
            >
              Rename
            </Button>
            <label>
              <input
                type="checkbox"
                checked={selected.visibility === "organizers"}
                disabled={busy}
                onChange={(e) =>
                  void act(
                    async () => {
                      await updateView(base, selected, {
                        visibility: e.target.checked ? "organizers" : "private",
                      });
                    },
                    e.target.checked
                      ? "Shared with organizers."
                      : "Now private.",
                  )
                }
              />{" "}
              Shared with organizers
            </label>
          </>
        )}
        {selected && (
          <Button
            variant="secondary"
            onClick={() =>
              void navigator.clipboard
                .writeText(window.location.href)
                .then(() => setNote("Link copied."))
                .catch(() => setNote("Could not copy; copy the address bar."))
            }
          >
            Copy link
          </Button>
        )}
        {selected?.mine && (
          <Button
            variant="secondary"
            disabled={busy}
            onClick={() => setRemoving(true)}
          >
            Delete view
          </Button>
        )}
      </div>

      {naming && (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void act(
              async () => {
                if (naming === "new") {
                  const created = await createView(base, {
                    entity,
                    name,
                    query: current,
                  });
                  // The list must know the new view before the URL names it, or the
                  // unknown-id correction would drop it again (a refetch can lag the render).
                  load.update((list) => [...(list ?? []), created]);
                  setApplied(created.public_id);
                  select(created.public_id, { replace: true });
                } else if (selected) {
                  await updateView(base, selected, { name });
                }
                setNaming(null);
              },
              naming === "new" ? "View saved." : "View renamed.",
            );
          }}
        >
          <label>
            Name{" "}
            <input
              value={name}
              maxLength={80}
              autoFocus
              onChange={(e) => setName(e.target.value)}
            />
          </label>
          <Button
            variant="primary"
            type="submit"
            disabled={busy || !name.trim()}
          >
            {naming === "new" ? "Save view" : "Rename view"}
          </Button>
          <Button variant="secondary" onClick={() => setNaming(null)}>
            Cancel
          </Button>
        </form>
      )}

      {removing && selected && (
        <div role="alertdialog" aria-label="Delete view">
          <p>
            Delete the view “{selected.name}”?{" "}
            {selected.visibility === "organizers"
              ? "Organizers it was shared with lose it. "
              : ""}
            The data it shows is not touched.
          </p>
          <Button
            variant="danger"
            disabled={busy}
            onClick={() =>
              void act(async () => {
                await deleteView(base, selected);
                select("", { replace: true });
                onApply(null);
                setRemoving(false);
              }, "View deleted.")
            }
          >
            Delete “{selected.name}”
          </Button>
          <Button variant="secondary" onClick={() => setRemoving(false)}>
            Keep it
          </Button>
        </div>
      )}
      {failure && <p role="alert">{failure}</p>}
      <span role="status">{note}</span>
    </div>
  );
}
