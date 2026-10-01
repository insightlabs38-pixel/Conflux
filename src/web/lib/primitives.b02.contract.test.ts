import { describe, expect, it } from "vitest";
import { resolveOperation } from "./api";
import { extensionsUrl } from "./extensions";
import { preferencesUrl } from "./notifications";
import { previewUrl } from "./preview";
import { previewUrl as richPreviewUrl } from "./rich";
import { comparisonUrl, versionsUrl } from "./versions";

// Every request the second batch of shared-primitive clients makes must be an operation the
// checked OpenAPI contract documents (PD-F002-B02-T91), so the web goes through the generated
// client and cannot drift from the API.
const W = "00000000-0000-4000-8000-000000000001";
const E = "00000000-0000-4000-8000-000000000002";
const ID = "00000000-0000-4000-8000-000000000003";
const path = (url: string) => url.split("?")[0];
const ref = { event: E, form: ID };

const REQUESTS: [string, string][] = [
  ["POST", richPreviewUrl(W)],
  ["GET", previewUrl(W, "project_artifact", { event: E, project: ID })],
  ["GET", previewUrl(W, "job_output", { job: ID, name: "archive.json" })],
  ["GET", versionsUrl(W, "form", ref)],
  ["GET", comparisonUrl(W, "form", ref, "1", "draft")],
  ["GET", preferencesUrl(W)],
  ["PUT", preferencesUrl(W)],
  ["GET", extensionsUrl(W)],
  ["GET", `/api/v1/audit/${W}/events/${E}/config-history/`],
  ["POST", `/api/v1/audit/${W}/events/${E}/config-history/${ID}/restore/`],
];

describe("second-batch shared-primitive clients and the OpenAPI contract", () => {
  it.each(REQUESTS)("%s %s is a documented operation", (method, url) => {
    expect(resolveOperation(method, path(url))).not.toBeNull();
  });
});
