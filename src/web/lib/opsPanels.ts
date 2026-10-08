import type { ComponentType } from "react";

/**
 * The contextual utility slot of operations mode (PD-F005-B03-T03). The pane beside the page is a
 * slot, not a fixed set of contents: a panel is registered with an id, a name, who may have it and
 * the component that draws it, and appears in the pane's chooser. Panels are read-only and own no
 * data of their own - each reads through an existing hook - and they report when their data was
 * last fetched so the pane can show the one health line. Today's panels live in
 * components/opsPanels.tsx; a later operator workflow adds one by registering it here.
 */
export type OpsPanelContext = {
  workspaceId: string;
  /** The selected event, or "" when none is. */
  eventId: string;
  organizer: boolean;
  /** The live topic that hints this pane to refresh (lib/realtime.ts). */
  topic: string;
  /** Tell the pane when the data on show was last fetched (ms since the epoch). */
  report: (updatedAt: number | null) => void;
};

export type OpsPanel = {
  id: string;
  label: string;
  /** Who is offered it; the server still decides what the reads return. */
  when?: (who: { organizer: boolean }) => boolean;
  Panel: ComponentType<OpsPanelContext>;
};

const panels: OpsPanel[] = [];

/** Add a panel. Returns a function that removes it (tests, hot reload). */
export function registerOpsPanel(panel: OpsPanel) {
  panels.push(panel);
  return () => {
    const at = panels.indexOf(panel);
    if (at >= 0) panels.splice(at, 1);
  };
}

export const opsPanelsFor = (who: { organizer: boolean }): OpsPanel[] =>
  panels.filter((panel) => !panel.when || panel.when(who));

/** What operations mode opens on when first turned on: the first panel this person is offered. */
export const firstOpsPanel = (who: { organizer: boolean }): string =>
  opsPanelsFor(who)[0]?.id ?? "";
