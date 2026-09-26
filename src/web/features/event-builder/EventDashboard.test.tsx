import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { EventDashboard } from "./EventDashboard";

describe("event dashboard", () => {
  it("offers event creation and a clear organizer entry point", () => {
    const html = renderToStaticMarkup(
      <EventDashboard workspaceId="workspace-id" />,
    );
    expect(html).toContain("Create event");
    expect(html).toContain("Workspace events");
  });
});
