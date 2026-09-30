import { describe, expect, it } from "vitest";

/**
 * Ratchet for the frontend transport (PD-B04-T03): application code reaches the network only
 * through `lib/api.ts` (which sends documented operations through the generated typed client).
 * A new raw `fetch(` fails here; extend the allowlist only for a documented reason.
 */
const sources = import.meta.glob(
  ["../**/*.{ts,tsx}", "!../**/*.test.{ts,tsx}"],
  {
    query: "?raw",
    import: "default",
    eager: true,
  },
) as Record<string, string>;

const allowed: Record<string, string> = {
  "./api.ts": "the transport itself",
  "../features/api-explorer/ApiExplorer.tsx":
    "public schema read (credentials omitted) and the free-form try-it request",
  "../features/artifacts/ArtifactPanel.tsx":
    "presigned uploads to object storage, which must not receive app credentials",
};

const rawFetch = /(?<![.\w])fetch\(/;

describe("frontend transport", () => {
  it("scans the application sources", () => {
    expect(Object.keys(sources).length).toBeGreaterThan(50);
  });

  it("uses raw fetch only in the allowlisted files", () => {
    const offenders = Object.entries(sources)
      .filter(([file, text]) => rawFetch.test(text) && !(file in allowed))
      .map(([file]) => file);
    expect(offenders).toEqual([]);
  });

  it("keeps every allowlisted file real (no stale exceptions)", () => {
    for (const file of Object.keys(allowed))
      expect(rawFetch.test(sources[file] ?? ""), file).toBe(true);
  });

  it("does not build a second client or hand-roll credentials outside the transport", () => {
    const offenders = Object.entries(sources)
      .filter(
        ([file, text]) =>
          !(file in allowed) &&
          (text.includes("new ConfluxClient(") ||
            text.includes('credentials: "include"')),
      )
      .map(([file]) => file);
    expect(offenders).toEqual([]);
  });
});
