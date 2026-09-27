import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { JudgeWorkspace } from "./JudgeWorkspace";

describe("judge workspace", () => {
  it("prompts for an event before the first fetch resolves", () => {
    const html = renderToStaticMarkup(<JudgeWorkspace workspaceId="workspace-id" />);
    expect(html).toContain("Judging");
    expect(html).toContain("Choose an event");
  });
});
