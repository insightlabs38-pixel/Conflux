import { Status } from "../../components/Status";
import { describeProblem } from "../../lib/api";
import { useLoad } from "../../hooks/useLoad";

type Workflow = {
  source: "preset" | "custom" | "none";
  preset: { key: string; version: number; label: string } | null;
  stages: string[];
  differences: { code: string; message: string }[];
};

/**
 * Whether the stages and judging still follow the format the event started from. Nothing here
 * switches anything: the organizer edits stages and judging freely below, and this says what is
 * still the format's and what has become custom. Editing is never blocked or reset.
 */
export function WorkflowStatus({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const load = useLoad<Workflow>(
    `/api/v1/workspaces/${workspaceId}/events/${eventId}/workflow/`,
    { describe: describeProblem },
  );
  const data = load.data;
  return (
    <section aria-label="Workflow source">
      <h3>
        Workflow{" "}
        {data && (
          <Status tone={data.source === "preset" ? "success" : "neutral"}>
            {data.source === "preset"
              ? "Follows the format"
              : data.source === "custom"
                ? "Customized"
                : "Built by hand"}
          </Status>
        )}
      </h3>
      {load.error && (
        <p role="alert">
          {load.error.message}{" "}
          <button type="button" onClick={() => void load.reload()}>
            Try again
          </button>
        </p>
      )}
      {!data && !load.error && <p className="cx-muted">Checking workflow…</p>}
      {data?.source === "preset" && data.preset && (
        <p>
          The stages and judging are the {data.preset.label} format&apos;s.
          Change anything below and only that part becomes custom; the rest
          keeps following the format.
        </p>
      )}
      {data?.source === "custom" && data.preset && (
        <>
          <p>Started from the {data.preset.label} format. What differs now:</p>
          <ul>
            {data.differences.map((d, index) => (
              <li key={`${d.code}-${index}`}>{d.message}</li>
            ))}
          </ul>
        </>
      )}
      {data?.source === "none" && (
        <p>
          This event was not started from a format, so its stages and judging
          are entirely yours.
        </p>
      )}
      {data && (
        <button type="button" onClick={() => void load.reload()}>
          Check again
        </button>
      )}
    </section>
  );
}
