import { Badge } from "../../components/Badge";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { useLoad } from "../pvs/http";

type Preview = {
  version: number;
  verified: boolean;
  artifacts: {
    id: string;
    title: string;
    kind: string;
    drift: string | null;
    download_url: string | null;
  }[];
};
export function FrozenSubmissionPreview({
  base,
  stageId,
}: {
  base: string;
  stageId: string;
}) {
  const { data, loading, error, reload } = useLoad<Preview>(
    `${base}submissions/${stageId}/preview/`,
  );
  return (
    <section
      aria-label="Frozen judge-visible evidence"
      className="cx-frozen-preview"
    >
      <h4>What a judge can inspect</h4>
      <p>
        Evidence from the finalized version. Private participant artifacts stay
        outside this preview.
      </p>
      {loading && <LoadingState label="Loading frozen evidence…" />}
      {error && <ErrorState message={error.message} onRetry={reload} />}
      {data && Array.isArray(data.artifacts) && (
        <>
          <p>
            <Badge tone={data.verified ? "success" : "warning"}>
              {data.verified
                ? "Evidence verified"
                : "Evidence changed since finalization"}
            </Badge>{" "}
            · Version {data.version}
          </p>
          <ul className="cx-evidence-list">
            {data.artifacts.map((artifact) => (
              <li key={artifact.id}>
                <strong>{artifact.title}</strong>
                <span>{artifact.kind}</span>
                {artifact.drift ? (
                  <Badge tone="danger">
                    {artifact.drift.replaceAll("_", " ")}
                  </Badge>
                ) : (
                  artifact.download_url && (
                    <a
                      className="cx-button cx-button--secondary"
                      href={artifact.download_url}
                    >
                      Download frozen artifact
                    </a>
                  )
                )}
              </li>
            ))}
          </ul>
          {data.artifacts.length === 0 && (
            <p>No judge-visible artifacts in this version.</p>
          )}
        </>
      )}
    </section>
  );
}
