import { useState, type ReactNode } from "react";
import { Button } from "../../components/Button";
import { EmptyState } from "../../components/EmptyState";
import { useWorkspaceNavigation } from "../../components/WorkspaceNavigation";

/**
 * Content of an optional module (PD-F001-B01-T04). While the module is off for the event it shows
 * what the module is and how to turn it on, instead of an empty tab; once on (or holding content)
 * it renders the children. Turning a module on is an audited server change, so this only asks.
 */
export function ModuleGate({
  module,
  eventId,
  children,
}: {
  module: string;
  eventId: string;
  children: ReactNode;
}) {
  const navigation = useWorkspaceNavigation();
  const modules = navigation?.modules;
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const state = modules?.modules?.find((item) => item.key === module);
  // Unknown (still loading, or this role has no module list): show the content, never a dead end.
  if (!modules || !state || state.enabled) return <>{children}</>;
  // The list may still describe another event (or the workspace union) right after a switch.
  const settled = modules.eventId === eventId;
  return (
    <EmptyState title={`${state.label} is not turned on for this event.`}>
      <p>{state.description}</p>
      {error && <p role="alert">{error}</p>}
      <Button
        type="button"
        disabled={busy || !settled}
        onClick={() => {
          setBusy(true);
          setError("");
          modules
            .setEnabled(eventId, module, true)
            .catch((cause: unknown) =>
              setError(
                cause instanceof Error ? cause.message : "Could not turn on.",
              ),
            )
            .finally(() => setBusy(false));
        }}
      >
        Turn on {state.label.toLowerCase()}
      </Button>
    </EmptyState>
  );
}
