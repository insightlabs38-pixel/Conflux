import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { EvaluationBuilder } from "./EvaluationBuilder";

describe("evaluation builder", () => {
  it("prompts for a stage before the first fetch resolves", () => {
    const html = renderToStaticMarkup(
      <EvaluationBuilder workspaceId="workspace-id" eventId="event-id" />,
    );
    expect(html).toContain("Judging");
    expect(html).toContain("Add a stage first");
  });
});
