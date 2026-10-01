import type { Subject } from "../lib/threads";
import { Button } from "./Button";
import { Modal } from "./Modal";
import { ThreadPanel } from "./ThreadPanel";

/** A thread in a dialog, for opening from a row of a grid. */
export function NotesDialog({
  subject,
  title,
  onClose,
}: {
  subject: Subject;
  title: string;
  onClose: () => void;
}) {
  return (
    <Modal titleId="notes-title" onClose={onClose}>
      <h2 id="notes-title">{title}</h2>
      <ThreadPanel subject={subject} />
      <div className="cx-consequence__actions">
        <Button variant="secondary" onClick={onClose}>
          Close
        </Button>
      </div>
    </Modal>
  );
}
