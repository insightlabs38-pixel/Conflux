/**
 * <conflux-gallery> (EMB-001): a dependency-light Web Component that renders
 * an event's public project gallery from Conflux's public JSON API
 * (GET /api/v1/events/<event>/gallery/). Ships as a single, self-contained,
 * zero-runtime-dependency bundle -- see docs/embed/README.md and
 * examples/embed.html for self-hosted usage (EMB-002).
 *
 * Attributes:
 *   event      (required) the event's public_id (UUID).
 *   api-base   (optional, default: same origin as the embedding page)
 *              e.g. "https://myevent.example.com".
 *   q          (optional) initial search filter, forwarded as ?q=.
 */

const TAG_NAME = "conflux-gallery";

interface GalleryItem {
  public_id: string;
  name: string;
  description: string;
  track: string | null;
  team: string | null;
  url: string;
}

const STYLE = `
  :host { display: block; font-family: system-ui, sans-serif; }
  .grid { list-style: none; margin: 0; padding: 0; display: grid; gap: 1rem;
          grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); }
  .card { border: 1px solid #ddd; border-radius: 8px; padding: 1rem; }
  .card h3 { margin: 0 0 0.5rem; font-size: 1rem; }
  .card a { color: inherit; text-decoration: none; }
  .card a:hover { text-decoration: underline; }
  .description { font-size: 0.9rem; opacity: 0.85; }
  .badge { display: inline-block; font-size: 0.75rem; padding: 0.1rem 0.5rem;
           border-radius: 999px; background: #eee; margin-right: 0.25rem; }
  .team { font-size: 0.85rem; opacity: 0.7; }
`;

function escapeHtml(value: string): string {
  const div = document.createElement("div");
  div.textContent = value;
  return div.innerHTML;
}

function renderCard(item: GalleryItem): string {
  const track = item.track
    ? `<span class="badge">${escapeHtml(item.track)}</span>`
    : "";
  const team = item.team ? `<p class="team">${escapeHtml(item.team)}</p>` : "";
  const description = item.description
    ? `<p class="description">${escapeHtml(item.description)}</p>`
    : "";
  return `
    <li class="card">
      <h3><a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.name)}</a></h3>
      ${description}
      ${track}
      ${team}
    </li>
  `;
}

class ConfluxGallery extends HTMLElement {
  static get observedAttributes() {
    return ["api-base", "event", "q"];
  }

  private root: ShadowRoot;

  constructor() {
    super();
    this.root = this.attachShadow({ mode: "open" });
  }

  connectedCallback() {
    void this.render();
  }

  attributeChangedCallback() {
    if (this.isConnected) void this.render();
  }

  private shell(inner: string) {
    this.root.innerHTML = `<style>${STYLE}</style><div class="conflux-gallery">${inner}</div>`;
  }

  private galleryUrl(eventId: string): string {
    const apiBase = this.getAttribute("api-base") ?? "";
    const q = this.getAttribute("q") ?? "";
    const url = new URL(
      `${apiBase}/api/v1/events/${eventId}/gallery/`,
      window.location.href,
    );
    if (q) url.searchParams.set("q", q);
    return url.toString();
  }

  private async render() {
    const eventId = this.getAttribute("event");
    if (!eventId) {
      this.shell(
        '<p role="alert">conflux-gallery requires an "event" attribute.</p>',
      );
      return;
    }
    this.shell("<p>Loading projects&hellip;</p>");

    let items: GalleryItem[];
    try {
      const response = await fetch(this.galleryUrl(eventId));
      if (!response.ok) {
        throw new Error(
          `Gallery request failed with status ${response.status}.`,
        );
      }
      items = await response.json();
    } catch (error) {
      this.shell(
        `<p role="alert">Couldn't load the gallery: ${escapeHtml(String(error))}</p>`,
      );
      return;
    }

    if (items.length === 0) {
      this.shell("<p>No projects match yet.</p>");
      return;
    }
    this.shell(`<ul class="grid">${items.map(renderCard).join("")}</ul>`);
  }
}

if (typeof customElements !== "undefined" && !customElements.get(TAG_NAME)) {
  customElements.define(TAG_NAME, ConfluxGallery);
}

export { ConfluxGallery };
