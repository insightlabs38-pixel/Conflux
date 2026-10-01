import { useEffect, useRef, type KeyboardEvent, type ReactNode } from "react";

/**
 * A modal dialog: focus moves in, stays in (Tab wraps), and returns to what opened it; Escape
 * asks to close. Shared by the consequence and bulk-planner dialogs so they behave identically.
 */
export function Modal({
  titleId,
  onClose,
  children,
}: {
  /** Id of the heading inside `children` that names the dialog. */
  titleId: string;
  onClose: () => void;
  children: ReactNode;
}) {
  const dialog = useRef<HTMLDivElement>(null);
  const close = useRef(onClose);
  close.current = onClose;

  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    dialog.current?.focus();
    return () => opener?.focus?.();
  }, []);

  // Escape works wherever focus is, including after the focused button was removed by the
  // dialog's own content (a confirmation that closes): the keystroke then lands on the body.
  useEffect(() => {
    function escape(event: globalThis.KeyboardEvent) {
      if (event.key !== "Escape" || event.defaultPrevented) return;
      event.stopPropagation();
      close.current();
    }
    document.addEventListener("keydown", escape);
    return () => document.removeEventListener("keydown", escape);
  }, []);

  function keydown(event: KeyboardEvent) {
    if (event.key !== "Tab" || !dialog.current) return;
    const focusable = [
      ...dialog.current.querySelectorAll<HTMLElement>(
        "button:not([disabled]), [href], input, select, textarea",
      ),
    ];
    if (focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const active = document.activeElement;
    if (event.shiftKey && (active === first || active === dialog.current)) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && active === last) {
      event.preventDefault();
      first.focus();
    }
  }

  return (
    <div className="cx-consequence__backdrop">
      <div
        ref={dialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className="cx-consequence"
        onKeyDown={keydown}
      >
        {children}
      </div>
    </div>
  );
}
