import { useEffect, useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";

type Theme = "default" | "dark" | "minimal";
type Kind =
  | "hero"
  | "tracks"
  | "prizes"
  | "schedule"
  | "sponsors"
  | "faq"
  | "resources"
  | "gallery"
  | "results"
  | "rich_text"
  | "cta";
type Block = {
  public_id: string;
  kind: Kind;
  position: number;
  config: Record<string, unknown>;
};
type Page = { public_id: string; theme: Theme };
type AuditWarning = {
  category: "contrast" | "heading" | "accessible-name" | "keyboard";
  severity: string;
  message: string;
  block_public_id: string | null;
};

const KIND_LABELS: Record<Kind, string> = {
  hero: "Hero",
  tracks: "Tracks (live)",
  prizes: "Prizes (live)",
  schedule: "Schedule (live)",
  sponsors: "Sponsors",
  faq: "FAQ",
  resources: "Resources",
  gallery: "Gallery preview (live)",
  results: "Results (live)",
  rich_text: "Rich text",
  cta: "Call to action",
};
const LIVE_KINDS = new Set<Kind>(["tracks", "prizes", "schedule", "results"]);
const LIST_FIELDS: Partial<Record<Kind, [string, string]>> = {
  faq: ["question", "answer"],
  sponsors: ["name", "url"],
  resources: ["label", "url"],
};

function message(value: unknown): string {
  if (typeof value === "string") return value;
  if (value instanceof Error) return value.message;
  if (Array.isArray(value)) return value.map(message).join(" ");
  if (value && typeof value === "object")
    return Object.entries(value)
      .map(([key, item]) => `${key}: ${message(item)}`)
      .join(" ");
  return "Request failed.";
}

async function request<T>(
  url: string,
  method = "GET",
  body?: object,
): Promise<T> {
  const response = await fetch(url, {
    method,
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    let detail: unknown = `Request failed (${response.status}).`;
    try {
      detail = await response.json();
    } catch {
      /* Retain status message. */
    }
    throw new Error(message(detail));
  }
  return response.status === 204
    ? (undefined as T)
    : (response.json() as Promise<T>);
}

function defaultConfig(kind: Kind): Record<string, unknown> {
  if (kind === "hero")
    return { title: "", subtitle: "", cta_label: "", cta_href: "" };
  if (kind === "cta") return { label: "", href: "" };
  if (kind === "rich_text") return { html: "" };
  if (kind === "gallery") return { limit: 6 };
  if (LIST_FIELDS[kind]) return { items: [] };
  return {};
}

function summarize(block: Block): string {
  if (block.kind === "hero") return String(block.config.title ?? "");
  if (block.kind === "cta") return String(block.config.label ?? "");
  if (block.kind === "rich_text") return "Rich text block";
  if (LIST_FIELDS[block.kind]) {
    const items = (block.config.items as unknown[] | undefined) ?? [];
    return `${items.length} item(s)`;
  }
  return "";
}

function ListEditor({
  fields,
  items,
  onChange,
}: {
  fields: [string, string];
  items: Record<string, string>[];
  onChange: (items: Record<string, string>[]) => void;
}) {
  return (
    <div>
      {items.map((item, index) => (
        <div key={index}>
          {fields.map((field) => (
            <label key={field}>
              {field}{" "}
              <input
                value={item[field] ?? ""}
                onChange={(event) => {
                  const next = items.slice();
                  next[index] = { ...item, [field]: event.target.value };
                  onChange(next);
                }}
              />
            </label>
          ))}
          <Button
            variant="secondary"
            onClick={() => onChange(items.filter((_, i) => i !== index))}
          >
            Remove
          </Button>
        </div>
      ))}
      <Button
        variant="secondary"
        onClick={() =>
          onChange([
            ...items,
            Object.fromEntries(fields.map((field) => [field, ""])),
          ])
        }
      >
        Add item
      </Button>
    </div>
  );
}

function BlockEditor({
  block,
  onSave,
}: {
  block: Block;
  onSave: (config: Record<string, unknown>) => Promise<void>;
}) {
  const [config, setConfig] = useState(block.config);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const dirty = JSON.stringify(config) !== JSON.stringify(block.config);

  async function save() {
    setSaving(true);
    setError("");
    try {
      await onSave(config);
    } catch (cause) {
      setError(message(cause));
    } finally {
      setSaving(false);
    }
  }

  if (LIVE_KINDS.has(block.kind)) {
    return <p>This block renders the event's live data automatically.</p>;
  }

  return (
    <div>
      {error && <p role="alert">{error}</p>}
      {block.kind === "hero" && (
        <>
          <label>
            Title{" "}
            <input
              value={String(config.title ?? "")}
              onChange={(e) => setConfig({ ...config, title: e.target.value })}
            />
          </label>
          <label>
            Subtitle{" "}
            <input
              value={String(config.subtitle ?? "")}
              onChange={(e) =>
                setConfig({ ...config, subtitle: e.target.value })
              }
            />
          </label>
          <label>
            CTA label{" "}
            <input
              value={String(config.cta_label ?? "")}
              onChange={(e) =>
                setConfig({ ...config, cta_label: e.target.value })
              }
            />
          </label>
          <label>
            CTA link{" "}
            <input
              value={String(config.cta_href ?? "")}
              onChange={(e) =>
                setConfig({ ...config, cta_href: e.target.value })
              }
            />
          </label>
        </>
      )}
      {block.kind === "cta" && (
        <>
          <label>
            Label{" "}
            <input
              value={String(config.label ?? "")}
              onChange={(e) => setConfig({ ...config, label: e.target.value })}
            />
          </label>
          <label>
            Link{" "}
            <input
              value={String(config.href ?? "")}
              onChange={(e) => setConfig({ ...config, href: e.target.value })}
            />
          </label>
        </>
      )}
      {block.kind === "rich_text" && (
        <label>
          HTML (sanitized on save){" "}
          <textarea
            value={String(config.html ?? "")}
            onChange={(e) => setConfig({ ...config, html: e.target.value })}
          />
        </label>
      )}
      {block.kind === "gallery" && (
        <label>
          Projects to preview{" "}
          <input
            type="number"
            min={1}
            max={24}
            value={Number(config.limit ?? 6)}
            onChange={(e) =>
              setConfig({ ...config, limit: Number(e.target.value) })
            }
          />
        </label>
      )}
      {LIST_FIELDS[block.kind] && (
        <ListEditor
          fields={LIST_FIELDS[block.kind]!}
          items={(config.items as Record<string, string>[] | undefined) ?? []}
          onChange={(items) => setConfig({ ...config, items })}
        />
      )}
      <Button disabled={!dirty || saving} onClick={save}>
        {saving ? "Saving…" : "Save block"}
      </Button>
    </div>
  );
}

export function PageBuilder({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/page/`;
  const [page, setPage] = useState<Page | null>(null);
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [addKind, setAddKind] = useState<Kind>("hero");
  const [warnings, setWarnings] = useState<AuditWarning[]>([]);
  const [error, setError] = useState("");

  async function refreshAudit() {
    setWarnings(await request<AuditWarning[]>(base + "accessibility-audit/"));
  }

  async function refresh() {
    const [nextPage, nextBlocks] = await Promise.all([
      request<Page>(base),
      request<Block[]>(base + "blocks/"),
    ]);
    setPage(nextPage);
    setBlocks(nextBlocks);
    await refreshAudit();
  }

  useEffect(() => {
    refresh().catch((cause: unknown) => setError(message(cause)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceId, eventId]);

  async function setTheme(theme: Theme) {
    try {
      const updated = await request<Page>(base, "PATCH", { theme });
      setPage(updated);
      await refreshAudit();
    } catch (cause) {
      setError(message(cause));
    }
  }

  async function addBlock() {
    try {
      await request<Block>(base + "blocks/", "POST", {
        kind: addKind,
        config: defaultConfig(addKind),
      });
      await refresh();
    } catch (cause) {
      setError(message(cause));
    }
  }

  async function saveBlock(block: Block, config: Record<string, unknown>) {
    const updated = await request<Block>(
      base + `blocks/${block.public_id}/`,
      "PATCH",
      {
        config,
      },
    );
    setBlocks((items) =>
      items.map((item) =>
        item.public_id === block.public_id ? updated : item,
      ),
    );
    await refreshAudit();
  }

  async function removeBlock(block: Block) {
    await request(base + `blocks/${block.public_id}/`, "DELETE");
    await refresh();
  }

  async function move(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= blocks.length) return;
    const next = blocks.slice();
    [next[index], next[target]] = [next[target], next[index]];
    setBlocks(next);
    try {
      await request<Block[]>(base + "blocks/reorder/", "POST", {
        block_ids: next.map((block) => block.public_id),
      });
    } catch (cause) {
      setError(message(cause));
      await refresh();
    }
  }

  return (
    <Card title="Public page">
      {error && <p role="alert">{error}</p>}
      {page && (
        <label>
          Theme{" "}
          <select
            value={page.theme}
            onChange={(e) => void setTheme(e.target.value as Theme)}
          >
            <option value="default">Default</option>
            <option value="dark">Dark</option>
            <option value="minimal">Minimal</option>
          </select>
        </label>
      )}
      {warnings.length > 0 && (
        <div role="status" aria-label="Accessibility warnings">
          <h4>Accessibility warnings</h4>
          <ul>
            {warnings.map((warning, index) => (
              <li key={index}>
                <Badge tone="warning">{warning.category}</Badge>{" "}
                {warning.message}
              </li>
            ))}
          </ul>
        </div>
      )}
      {blocks.length === 0 ? (
        <EmptyState title="This event's public page has no blocks yet." />
      ) : (
        <ol aria-label="Page blocks">
          {blocks.map((block, index) => (
            <li key={block.public_id}>
              <Badge tone="info">{KIND_LABELS[block.kind]}</Badge>{" "}
              {summarize(block)}
              <div>
                <Button
                  variant="secondary"
                  onClick={() => void move(index, -1)}
                >
                  Move up
                </Button>
                <Button variant="secondary" onClick={() => void move(index, 1)}>
                  Move down
                </Button>
                <Button
                  variant="danger"
                  onClick={() => void removeBlock(block)}
                >
                  Remove
                </Button>
              </div>
              <BlockEditor
                block={block}
                onSave={(config) => saveBlock(block, config)}
              />
            </li>
          ))}
        </ol>
      )}
      <label>
        Add block{" "}
        <select
          value={addKind}
          onChange={(e) => setAddKind(e.target.value as Kind)}
        >
          {Object.entries(KIND_LABELS).map(([kind, label]) => (
            <option key={kind} value={kind}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <Button onClick={() => void addBlock()}>Add</Button>
    </Card>
  );
}
