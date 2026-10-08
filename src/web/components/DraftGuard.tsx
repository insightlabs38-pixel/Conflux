import { useEffect, useId, useState, type ReactNode } from "react";
import { discardDrafts, hasDrafts, useAnyDrafts } from "../lib/drafts";
import { Modal } from "./Modal";

/**
 * What stands between unsaved edits and losing them (PD-F005-B03-T02). While any draft exists the
 * browser asks before a reload or closing the tab, and signing out asks first and says it discards
 * them. Drafts are in memory only, so these are the only two ways to lose them besides closing the
 * place they are in (WorkspaceTabs) - and each of those asks.
 */
export function useDraftGuard(signOut: (() => void) | undefined): {
  requestSignOut: (() => void) | undefined;
  dialog: ReactNode;
} {
  const any = useAnyDrafts();
  const [asking, setAsking] = useState(false);
  const titleId = useId();
  useEffect(() => {
    if (!any) return;
    const warn = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [any]);
  return {
    requestSignOut:
      signOut && (() => (hasDrafts() ? setAsking(true) : signOut())),
    dialog:
      asking && signOut ? (
        <Modal titleId={titleId} onClose={() => setAsking(false)}>
          <h2 id={titleId}>Sign out with unsaved changes?</h2>
          <p>
            Some places have changes that are not saved. Signing out discards
            them.
          </p>
          <div className="cx-consequence__actions">
            <button type="button" onClick={() => setAsking(false)}>
              Keep editing
            </button>
            <button
              type="button"
              onClick={() => {
                setAsking(false);
                discardDrafts();
                signOut();
              }}
            >
              Discard and sign out
            </button>
          </div>
        </Modal>
      ) : null,
  };
}
