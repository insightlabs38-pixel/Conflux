import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { FormBuilder } from "./FormBuilder";

describe("form builder", () => {
  it("offers a form creation entry point", () => {
    const html = renderToStaticMarkup(
      <FormBuilder workspaceId="workspace" eventId="event" />,
    );
    expect(html).toContain("New form name");
    expect(html).toContain("No forms yet.");
  });
});
