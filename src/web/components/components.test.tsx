import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { AppShell } from "./AppShell";
import { Status, Tag } from "./Status";
import { Button } from "./Button";
import { Card } from "./Card";
import { DeniedState } from "./DeniedState";
import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";
import { LoadingState } from "./LoadingState";
import { SkipLink } from "./SkipLink";
import { VisuallyHidden } from "./VisuallyHidden";

describe("Button", () => {
  it("defaults to a primary, non-submitting button and forwards handlers", () => {
    const html = renderToStaticMarkup(
      <Button variant="primary" onClick={vi.fn()}>
        Go
      </Button>,
    );
    expect(html).toContain('type="button"');
    expect(html).toContain("cx-button--primary");
    expect(html).toContain("Go");
  });

  it("applies the requested variant", () => {
    const html = renderToStaticMarkup(<Button variant="danger">Delete</Button>);
    expect(html).toContain("cx-button--danger");
  });
});

describe("Status and Tag", () => {
  it("renders the requested tone with an icon and the word", () => {
    const html = renderToStaticMarkup(<Status tone="success">Ready</Status>);
    expect(html).toContain("cx-status--success");
    expect(html).toContain("<svg");
    expect(html).toContain("Ready");
  });
  it("renders a neutral attribute as plain text in a tag, with no icon", () => {
    const html = renderToStaticMarkup(<Tag>Hardware</Tag>);
    expect(html).toContain("cx-tag");
    expect(html).not.toContain("<svg");
  });
});

describe("Card", () => {
  it("renders an optional title as a heading", () => {
    const html = renderToStaticMarkup(<Card title="Team">content</Card>);
    expect(html).toContain("<h3");
    expect(html).toContain("Team");
    expect(html).toContain("content");
  });

  it("omits the heading when no title is given", () => {
    expect(renderToStaticMarkup(<Card>content</Card>)).not.toContain("<h3");
  });
});

describe("state primitives", () => {
  it("LoadingState announces via role=status", () => {
    expect(renderToStaticMarkup(<LoadingState />)).toContain('role="status"');
  });

  it("EmptyState renders a title and optional action", () => {
    const html = renderToStaticMarkup(
      <EmptyState
        title="No projects yet"
        why="Projects appear here once a team creates one."
        next={<Button variant="primary">Create one</Button>}
      />,
    );
    expect(html).toContain("No projects yet");
    expect(html).toContain("Projects appear here once a team creates one.");
    expect(html).toContain("Create one");
  });
  it("EmptyState has a place for the one next action and omits it when the viewer has none", () => {
    expect(
      renderToStaticMarkup(<EmptyState title="Nothing" why="Because." />),
    ).not.toContain("cx-state__next");
    expect(
      renderToStaticMarkup(
        <EmptyState
          title="Nothing"
          why="Because."
          next={<a href="/x">Do it</a>}
        />,
      ),
    ).toContain('cx-state__next"><a href="/x">Do it</a>');
  });

  it("ErrorState announces via role=alert and offers retry", () => {
    const html = renderToStaticMarkup(
      <ErrorState message="Network failed" onRetry={vi.fn()} />,
    );
    expect(html).toContain('role="alert"');
    expect(html).toContain("Network failed");
    expect(html).toContain("Try again");
  });

  it("DeniedState announces via role=alert", () => {
    const html = renderToStaticMarkup(<DeniedState />);
    expect(html).toContain('role="alert"');
    expect(html).toContain("Access denied");
  });
});

describe("accessibility baseline", () => {
  it("SkipLink points at the shell's main landmark id", () => {
    expect(
      renderToStaticMarkup(<SkipLink targetId="main-content" />),
    ).toContain('href="#main-content"');
  });

  it("VisuallyHidden content is present in markup for assistive tech", () => {
    expect(
      renderToStaticMarkup(<VisuallyHidden>Column: status</VisuallyHidden>),
    ).toContain("Column: status");
  });

  it("AppShell wires the skip link to a keyboard-focusable main landmark and labels nav", () => {
    const html = renderToStaticMarkup(
      <AppShell nav={<a href="/x">Link</a>}>body</AppShell>,
    );
    expect(html).toContain('href="#main-content"');
    // tabindex="-1" makes the jump target programmatically focusable without
    // adding it to the normal tab order, per the standard skip-link pattern.
    expect(html).toContain('id="main-content"');
    expect(html).toContain('tabindex="-1"');
    expect(html).toContain('aria-label="Primary"');
  });

  it("the skip link is the first element in document order, before header nav", () => {
    const html = renderToStaticMarkup(
      <AppShell nav={<a href="/x">Link</a>}>body</AppShell>,
    );
    expect(html.indexOf("cx-skip-link")).toBeLessThan(
      html.indexOf("cx-shell__nav"),
    );
  });

  it("AppShell renders the brand as a page heading by default, or a paragraph when the page owns its own h1", () => {
    expect(renderToStaticMarkup(<AppShell>body</AppShell>)).toContain("<h1");
    expect(
      renderToStaticMarkup(<AppShell brandAs="p">body</AppShell>),
    ).not.toContain("<h1");
  });
});

describe("DeniedState", () => {
  it("states the denial and draws the server's explanation as sent, never one of its own", () => {
    const plain = renderToStaticMarkup(<DeniedState />);
    expect(plain).toContain("Access denied");
    expect(plain).not.toContain("cx-explain");
    const explained = renderToStaticMarkup(
      <DeniedState
        message="You cannot publish."
        explanation={{
          outcome: "blocked",
          summary: "Two approvals are missing.",
          reasons: [
            {
              code: "approvals",
              severity: "blocker",
              message: "Needs 2 of 3 approvers.",
              fix: { destination: "results", section: null },
            },
          ],
          total: 1,
          truncated: false,
        }}
      />,
    );
    expect(explained).toContain("Two approvals are missing.");
    expect(explained).toContain("Needs 2 of 3 approvers.");
    expect(explained).toContain("Resolve in");
  });
});
