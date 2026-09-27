import type { ReactNode } from "react";
import { SkipLink } from "./SkipLink";

const MAIN_ID = "main-content";

/** Shared page chrome: skip link, header/nav landmark, main landmark. */
export function AppShell({
  nav,
  children,
  brand = "Conflux",
  brandAs: Brand = "h1",
}: {
  nav?: ReactNode;
  children: ReactNode;
  brand?: string;
  /** The page's h1 lives wherever the page's actual title is; pass "p" here
   * when the shell wraps a page that renders its own h1 (e.g. an event name). */
  brandAs?: "h1" | "p";
}) {
  return (
    <div className="cx-shell">
      <SkipLink targetId={MAIN_ID} />
      <header className="cx-shell__header">
        <Brand className="cx-shell__brand">{brand}</Brand>
        {nav && (
          <nav className="cx-shell__nav" aria-label="Primary">
            {nav}
          </nav>
        )}
      </header>
      <main id={MAIN_ID} className="cx-shell__main" tabIndex={-1}>
        {children}
      </main>
    </div>
  );
}
