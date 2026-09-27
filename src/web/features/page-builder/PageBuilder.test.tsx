import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { PageBuilder } from "./PageBuilder";

describe("page builder", () => {
  it("shows an empty state before the first fetch resolves", () => {
    const html = renderToStaticMarkup(
      <PageBuilder workspaceId="workspace-id" eventId="event-id" />,
    );
    expect(html).toContain("Public page");
    expect(html).toContain("no blocks yet");
  });
});
