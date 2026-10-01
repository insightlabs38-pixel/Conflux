import { useState } from "react";
import { changeSummary, sha256Hex, type Provenance } from "../lib/provenance";
import { humanSize } from "../lib/preview";

type Check = "idle" | "working" | "match" | "differs" | "unavailable";

/**
 * Shows what a result was made from: who, when, from what, under which rules, and the digest of
 * the file it produced. A person can pick a downloaded file and see whether it is exactly that
 * file; the check runs in the browser and nothing is uploaded.
 */
export function ProvenanceView({
  provenance,
  label,
}: {
  provenance: Provenance;
  label?: string;
}) {
  const [check, setCheck] = useState<Check>("idle");
  const { output } = provenance;

  async function verify(file: File | undefined) {
    if (!file || !output) return;
    setCheck("working");
    const found = await sha256Hex(await file.arrayBuffer());
    setCheck(
      found === null
        ? "unavailable"
        : found === output.sha256
          ? "match"
          : "differs",
    );
  }

  return (
    <section className="cx-provenance" aria-label={label ?? "Provenance"}>
      <p>{provenance.summary}</p>
      <dl className="cx-artifact__facts">
        <div>
          <dt>Made by</dt>
          <dd>{provenance.by?.username ?? "The system"}</dd>
        </div>
        <div>
          <dt>When</dt>
          <dd>
            <time dateTime={provenance.at}>
              {new Date(provenance.at).toLocaleString()}
            </time>
          </dd>
        </div>
        <div>
          <dt>From</dt>
          <dd>
            {provenance.source.kind} {provenance.source.id}
          </dd>
        </div>
        {provenance.inputs.refs.length > 0 && (
          <div>
            <dt>Based on</dt>
            <dd>
              {provenance.inputs.refs
                .map((ref) => ref.label ?? `${ref.kind} ${ref.id}`)
                .join(", ")}
            </dd>
          </div>
        )}
        {provenance.inputs.digest && (
          <div>
            <dt>Inputs digest</dt>
            <dd className="cx-provenance__digest">
              {provenance.inputs.digest}
            </dd>
          </div>
        )}
        {provenance.rules && (
          <div>
            <dt>Rules</dt>
            <dd>
              {provenance.rules.name} (version {provenance.rules.version})
            </dd>
          </div>
        )}
        {provenance.changes && (
          <div>
            <dt>Changes</dt>
            <dd>{changeSummary(provenance.changes)}</dd>
          </div>
        )}
        {output && (
          <div>
            <dt>File</dt>
            <dd>
              {output.name} ({humanSize(output.bytes)})
            </dd>
          </div>
        )}
        {output && (
          <div>
            <dt>SHA-256</dt>
            <dd className="cx-provenance__digest">{output.sha256}</dd>
          </div>
        )}
      </dl>
      {output && (
        <p>
          <label>
            Check a downloaded file{" "}
            <input
              type="file"
              onChange={(event) => void verify(event.target.files?.[0])}
            />
          </label>{" "}
          <span role="status">
            {check === "working" && "Checking…"}
            {check === "match" && "This is exactly the file recorded here."}
            {check === "differs" && "This is not the file recorded here."}
            {check === "unavailable" && "This browser cannot check files."}
          </span>
        </p>
      )}
    </section>
  );
}
