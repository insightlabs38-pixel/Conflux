import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { StaticRouter } from "react-router";
import { EventDashboard } from "./EventDashboard";
import { withQuery } from "../../lib/test-router";

describe("event dashboard", () => {
  it("offers event creation and a clear organizer entry point", () => {
    const html = renderToStaticMarkup(
      withQuery(
        <StaticRouter location="/w/workspace-id/overview">
          <EventDashboard workspaceId="workspace-id" />
        </StaticRouter>,
      ),
    );
    expect(html).toContain("Create event");
    expect(html).toContain("Workspace events");
  });
});
