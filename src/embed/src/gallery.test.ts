import { beforeEach, describe, expect, it, vi } from "vitest";
import "./gallery";

const flush = () =>
  new Promise((resolve) => setTimeout(resolve, 0)).then(
    () => new Promise((resolve) => setTimeout(resolve, 0)),
  );

describe("conflux-gallery", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
    vi.unstubAllGlobals();
  });

  it("registers the custom element", () => {
    expect(customElements.get("conflux-gallery")).toBeDefined();
  });

  it("warns when the event attribute is missing", async () => {
    const el = document.createElement("conflux-gallery");
    document.body.appendChild(el);
    await flush();
    expect(el.shadowRoot?.textContent).toContain(
      'requires an "event" attribute',
    );
  });

  it("fetches and renders gallery items from the public API", async () => {
    const items = [
      {
        public_id: "1",
        name: "Widget",
        description: "A widget.",
        track: "Hardware",
        team: "Team A",
        url: "/e/x/projects/1/",
      },
    ];
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => items });
    vi.stubGlobal("fetch", fetchMock);

    const el = document.createElement("conflux-gallery");
    el.setAttribute("event", "abc-123");
    document.body.appendChild(el);
    await flush();

    expect(el.shadowRoot?.textContent).toContain("Widget");
    expect(el.shadowRoot?.textContent).toContain("Hardware");
    expect(el.shadowRoot?.textContent).toContain("Team A");
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/events/abc-123/gallery/"),
    );
  });

  it("forwards the q attribute as a query parameter", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => [] });
    vi.stubGlobal("fetch", fetchMock);

    const el = document.createElement("conflux-gallery");
    el.setAttribute("event", "abc-123");
    el.setAttribute("q", "widget");
    document.body.appendChild(el);
    await flush();

    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("q=widget"));
  });

  it("shows an empty state when there are no projects", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => [] }),
    );
    const el = document.createElement("conflux-gallery");
    el.setAttribute("event", "abc-123");
    document.body.appendChild(el);
    await flush();
    expect(el.shadowRoot?.textContent).toContain("No projects match yet");
  });

  it("shows an error state when the request fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue({ ok: false, status: 500, json: async () => ({}) }),
    );
    const el = document.createElement("conflux-gallery");
    el.setAttribute("event", "abc-123");
    document.body.appendChild(el);
    await flush();
    expect(el.shadowRoot?.textContent).toContain("Couldn't load the gallery");
  });

  it("escapes untrusted project fields to prevent injected markup", async () => {
    const items = [
      {
        public_id: "1",
        name: "<img src=x onerror=alert(1)>",
        description: "",
        track: null,
        team: null,
        url: "/e/x/projects/1/",
      },
    ];
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => items }),
    );
    const el = document.createElement("conflux-gallery");
    el.setAttribute("event", "abc-123");
    document.body.appendChild(el);
    await flush();

    expect(el.shadowRoot?.querySelector("img")).toBeNull();
    expect(el.shadowRoot?.innerHTML).toContain("&lt;img");
  });
});
