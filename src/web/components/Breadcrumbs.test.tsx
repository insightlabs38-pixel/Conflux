// @vitest-environment happy-dom
import { renderToStaticMarkup } from "react-dom/server";
import { StaticRouter } from "react-router";
import { describe, expect, it } from "vitest";
import { Breadcrumbs } from "./Foundation";

const render = (node: React.ReactElement) =>
  renderToStaticMarkup(<StaticRouter location="/">{node}</StaticRouter>);

describe("breadcrumbs", () => {
  it("show nothing for a destination or a page one level below it", () => {
    expect(render(<Breadcrumbs items={[{ label: "Participants" }]} />)).toBe(
      "",
    );
    expect(
      render(
        <Breadcrumbs
          items={[{ label: "Participants" }, { label: "Team Alpha" }]}
        />,
      ),
    ).toBe("");
  });

  it("list the ancestors of a page three levels deep, never the page itself", () => {
    const html = render(
      <Breadcrumbs
        workspaceId="w1"
        items={[
          { label: "Gauss Hack", target: { view: "overview", event: "e1" } },
          { label: "Participants", target: { view: "participants" } },
          { label: "Team Alpha" },
        ]}
      />,
    );
    expect(html).toContain('aria-label="Breadcrumb"');
    expect(html).toContain('href="/w/w1/overview?event=e1"');
    expect(html).toContain('href="/w/w1/participants"');
    expect(html).toContain("Gauss Hack");
    expect(html).toContain("Participants");
    expect(html).not.toContain("Team Alpha"); // the heading says it
  });

  it("falls back to plain links outside the workspace routes", () => {
    const html = render(
      <Breadcrumbs
        items={[
          { label: "Home", href: "/" },
          { label: "Events", href: "/events" },
          { label: "Current" },
        ]}
      />,
    );
    expect(html).toContain('<a href="/">Home</a>');
    expect(html).toContain('<a href="/events">Events</a>');
  });
});
