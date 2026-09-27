import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { CommunityVotingBuilder } from "./CommunityVotingBuilder";

describe("community voting builder", () => {
  it("renders nothing before the plan has loaded", () => {
    const html = renderToStaticMarkup(
      <CommunityVotingBuilder workspaceId="workspace-id" eventId="event-id" />,
    );
    expect(html).toBe("");
  });
});
