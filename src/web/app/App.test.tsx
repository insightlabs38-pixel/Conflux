import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { App } from "./App";

describe("bootstrap shell", () => {
  it("renders a stable heading", () => {
    const html = renderToStaticMarkup(<App />);
    expect(html).toMatch(/<h1[^>]*>Conflux<\/h1>/);
  });
});
