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

  function keydown(event: KeyboardEvent) {
    if (event.key === "Escape") {
      event.stopPropagation();
      close.current();
      return;
    }
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
