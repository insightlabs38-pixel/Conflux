import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { TeamPanel } from "./TeamPanel";

describe("team panel", () => {
  it("shows a loading state before the first status fetch resolves", () => {
    const html = renderToStaticMarkup(
      <TeamPanel workspaceId="workspace-id" eventId="event-id" />,
    );
    expect(html).toContain("My team");
    expect(html).toContain("Loading");
  });
});
