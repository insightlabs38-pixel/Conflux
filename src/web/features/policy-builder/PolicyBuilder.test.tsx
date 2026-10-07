import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { withQuery } from "../../lib/test-router";
import { PolicyBuilder } from "./PolicyBuilder";

describe("policy builder", () => {
  it("offers policy/binding/gate entry points without requiring raw JSON", () => {
    const html = renderToStaticMarkup(
      withQuery(
        <PolicyBuilder workspaceId="workspace-id" eventId="event-id" />,
      ),
    );
    expect(html).toContain("Add policy");
    expect(html).toContain("Bind policy to action");
    expect(html).toContain("Add gate");
  });
});
