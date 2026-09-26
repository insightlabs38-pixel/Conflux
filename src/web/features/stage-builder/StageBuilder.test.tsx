import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { StageBuilder } from "./StageBuilder";

describe("stage builder", () => {
  it("offers stage/transition/advancement entry points", () => {
    const html = renderToStaticMarkup(
      <StageBuilder workspaceId="workspace-id" eventId="event-id" />,
    );
    expect(html).toContain("Add stage");
    expect(html).toContain("Add transition");
    expect(html).toContain("Run advancement");
    expect(html).toContain("Evidence");
  });
});
