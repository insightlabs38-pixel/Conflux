import { describe, expect, it } from "vitest";
import { resolveOperation } from "./api";
import { previewAsUrl } from "./previewContext";

// The request the preview-as client makes must be an operation the checked OpenAPI contract
// documents (PD-F002-B03-T01), so the web goes through the generated client and cannot drift.
const W = "00000000-0000-4000-8000-000000000001";

describe("preview-as client and the OpenAPI contract", () => {
  it("POST preview-as is a documented operation", () => {
    expect(resolveOperation("POST", previewAsUrl(W, "form"))).not.toBeNull();
  });
});
