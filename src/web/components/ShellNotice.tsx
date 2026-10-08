import { useLayoutEffect, useRef, useState } from "react";
import { onNotice } from "../lib/shellNotice";

const SHOWN_MS = 4000;

/** The shell's one message line: a polite live region, readable by screen readers, gone in a few seconds. */
export function ShellNotice() {
  const [message, setMessage] = useState("");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useLayoutEffect(
    () =>
      onNotice((next) => {
        setMessage(next);
        if (timer.current) clearTimeout(timer.current);
        timer.current = setTimeout(() => setMessage(""), SHOWN_MS);
      }),
    [],
  );
  return (
    <div className="cx-notice" role="status" aria-live="polite">
      {message}
    </div>
  );
}
