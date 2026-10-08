import { useCallback, useId, useState } from "react";
import { useLocation } from "react-router";
import { useMe } from "../hooks/useMe";
import { useWideDisplay } from "../hooks/useWideDisplay";
import { opsPanelsFor } from "../lib/opsPanels";
import { liveOpsTopic } from "../lib/realtime";
import { setOpsPane, useOpsPane } from "../lib/shellPreferences";
import { LiveStatus } from "./LiveStatus";
import { useWorkspaceNavigation } from "./WorkspaceNavigation";
import "./opsPanels";

/**
 * The contextual utility slot of operations mode (spec 005, PD-F005-B03-T03), shown beside the page
 * from 1800px and only while the person has it on. It hosts one registered panel at a time
 * (lib/opsPanels.ts), read-only and live; the choice of panel is a device choice, and a stored one
 * that no longer exists or is not offered falls back to the first. The pane owns no data and no
 * rules: its health line is the one the live lists use, fed by what the panel reports.
 */
export function OperationsHost() {
  const user = useMe().data?.public_id ?? "";
  const pane = useOpsPane(user);
  const wide = useWideDisplay();
  return wide && pane ? <OperationsPane pane={pane} /> : null;
}

function OperationsPane({ pane }: { pane: string }) {
  const navigation = useWorkspaceNavigation();
  const location = useLocation();
  const user = useMe().data?.public_id ?? "";
  const heading = useId();
  const [updatedAt, report] = useState<number | null>(null);
  const reportStable = useCallback((at: number | null) => report(at), []);
  const workspaceId = navigation?.workspaceId ?? "";
  const organizer =
    navigation?.role === "organizer" || navigation?.role === "admin";
  const eventId = new URLSearchParams(location.search).get("event") ?? "";
  const offered = opsPanelsFor({ organizer });
  const shown = offered.find((panel) => panel.id === pane) ?? offered[0];
  const topic = liveOpsTopic(workspaceId, eventId || "none", "pane");
  if (!shown) return null;

  return (
    <aside className="cx-opspane" aria-labelledby={heading}>
      <div className="cx-opspane__head">
        <h2 id={heading}>Operations</h2>
        <button type="button" onClick={() => setOpsPane(user, "")}>
          Close pane
        </button>
      </div>
      <div role="group" aria-label="Pane shows" className="cx-opspane__choice">
        {offered.map((panel) => (
          <button
            key={panel.id}
            type="button"
            aria-pressed={panel.id === shown.id}
            onClick={() => setOpsPane(user, panel.id)}
          >
            {panel.label}
          </button>
        ))}
      </div>
      <LiveStatus topic={topic} updatedAt={updatedAt} />
      <shown.Panel
        key={shown.id}
        workspaceId={workspaceId}
        eventId={eventId}
        organizer={organizer}
        topic={topic}
        report={reportStable}
      />
    </aside>
  );
}
