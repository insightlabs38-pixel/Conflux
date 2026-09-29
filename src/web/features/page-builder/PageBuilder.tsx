import { useEffect, useState } from "react";
import { blockTypes } from "./blockSchemas.generated";
import { configDefaults, configError, type ConfigSchema } from "./configSchema";
import { ConfigFields } from "./ConfigFields";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";

import { ThemeSettings, type ThemeConfig } from "./ThemeSettings";

type Theme = "default" | "dark" | "minimal";
type Kind = keyof typeof blockTypes;
type Block = {
  public_id: string;
  kind: Kind;
  position: number;
  config: Record<string, unknown>;
};
type Page = { public_id: string; theme: Theme; theme_config?: ThemeConfig };
type AuditWarning = {
  category: "contrast" | "heading" | "accessible-name" | "keyboard";
  severity: string;
  message: string;
  block_public_id: string | null;
};

const schemas = blockTypes as Record<
  Kind,
  { title: string; schema: ConfigSchema }
>;
const KIND_LABELS = Object.fromEntries(
  Object.entries(schemas).map(([kind, definition]) => [kind, definition.title]),
) as Record<Kind, string>;
const LIST_FIELDS = Object.fromEntries(
  Object.entries(schemas)
    .filter(
      ([, definition]) => definition.schema.properties?.items?.type === "array",
    )
    .map(([kind, definition]) => [
      kind,
      Object.keys(definition.schema.properties!.items.items!.properties!),
    ]),
);

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
  return configDefaults(schemas[kind].schema, true);
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

function BlockEditor({
  block,
  onSave,
}: {
  block: Block;
  onSave: (config: Record<string, unknown>) => Promise<Record<string, unknown>>;
}) {
  const [config, setConfig] = useState(block.config);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const dirty = JSON.stringify(config) !== JSON.stringify(block.config);

  async function save() {
    const invalid = configError(schemas[block.kind].schema, config);
    if (invalid) {
      setError(invalid);
      return;
    }
    setSaving(true);
    setError("");
    try {
      setConfig(await onSave(config));
    } catch (cause) {
      setError(message(cause));
    } finally {
      setSaving(false);
    }
  }

  if (Object.keys(schemas[block.kind].schema.properties ?? {}).length === 0) {
    return <p>This block renders the event's live data automatically.</p>;
  }

  return (
    <div>
      {error && <p role="alert">{error}</p>}
      <ConfigFields
        schema={schemas[block.kind].schema}
        config={config}
        onChange={setConfig}
      />
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

  async function setAppearance(theme: Theme, theme_config: ThemeConfig) {
    const cleaned = Object.fromEntries(
      Object.entries(theme_config).filter(([, value]) => value !== ""),
    );
    const updated = await request<Page>(base, "PATCH", {
      theme,
      theme_config: cleaned,
    });
    setPage(updated);
    setError("");
    await refreshAudit();
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
    return updated.config;
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
        <ThemeSettings
          key={page.public_id}
          theme={page.theme}
          config={page.theme_config || {}}
          eventId={eventId}
          onSave={setAppearance}
        />
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
