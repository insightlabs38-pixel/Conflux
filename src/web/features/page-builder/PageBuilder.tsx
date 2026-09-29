import { useEffect, useState } from "react";
import { blockTypes } from "./blockSchemas.generated";
import { configDefaults, configError, type ConfigSchema } from "./configSchema";
import { ConfigFields } from "./ConfigFields";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { WorkflowSections } from "../../components/WorkflowSections";

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
    <div className="cx-block-form">
      {error && <p role="alert">{error}</p>}
      <ConfigFields
        schema={schemas[block.kind].schema}
        config={config}
        onChange={setConfig}
      />
      <div className="cx-block-form__actions">
        <Button disabled={!dirty || saving} onClick={save}>
          {saving ? "Saving…" : "Save block"}
        </Button>
        <span role="status" className="cx-muted">
          {saving ? "Saving…" : dirty ? "Unsaved changes" : "All changes saved"}
        </span>
      </div>
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
  const [selectedId, setSelectedId] = useState("");
  const [confirmingId, setConfirmingId] = useState("");

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
      const created = await request<Block>(base + "blocks/", "POST", {
        kind: addKind,
        config: defaultConfig(addKind),
      });
      await refresh();
      setSelectedId(created.public_id);
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
    setConfirmingId("");
    try {
      await request(base + `blocks/${block.public_id}/`, "DELETE");
      setSelectedId("");
      await refresh();
    } catch (cause) {
      setError(message(cause));
    }
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

  const selected =
    blocks.find((block) => block.public_id === selectedId) ?? blocks[0];

  const content = (
    <div className="cx-block-editor">
      <div className="cx-block-outline">
        {blocks.length === 0 ? (
          <EmptyState title="This event's public page has no blocks yet." />
        ) : (
          <ol aria-label="Page blocks">
            {blocks.map((block, index) => (
              <li
                key={block.public_id}
                data-current={
                  block.public_id === selected?.public_id || undefined
                }
              >
                <button
                  type="button"
                  className="cx-block-outline__select"
                  aria-current={
                    block.public_id === selected?.public_id ? "true" : undefined
                  }
                  onClick={() => setSelectedId(block.public_id)}
                >
                  <span className="cx-block-outline__index">{index + 1}</span>
                  <span>
                    <strong>{KIND_LABELS[block.kind]}</strong>
                    <small>{summarize(block)}</small>
                  </span>
                </button>
                <span className="cx-block-outline__move">
                  <Button
                    variant="secondary"
                    disabled={index === 0}
                    aria-label={`Move ${KIND_LABELS[block.kind]} up`}
                    onClick={() => void move(index, -1)}
                  >
                    Move up
                  </Button>
                  <Button
                    variant="secondary"
                    disabled={index === blocks.length - 1}
                    aria-label={`Move ${KIND_LABELS[block.kind]} down`}
                    onClick={() => void move(index, 1)}
                  >
                    Move down
                  </Button>
                </span>
              </li>
            ))}
          </ol>
        )}
        <div className="cx-block-add">
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
        </div>
      </div>
      {selected && (
        <section
          className="cx-block-detail"
          aria-label={`Edit ${KIND_LABELS[selected.kind]} block`}
        >
          <header>
            <h4>{KIND_LABELS[selected.kind]}</h4>
            {confirmingId === selected.public_id ? (
              <span
                className="cx-block-confirm"
                role="group"
                aria-label="Confirm removal"
              >
                <span>Remove this block from the public page?</span>
                <Button
                  variant="danger"
                  onClick={() => void removeBlock(selected)}
                >
                  Confirm remove
                </Button>
                <Button variant="secondary" onClick={() => setConfirmingId("")}>
                  Keep block
                </Button>
              </span>
            ) : (
              <Button
                variant="secondary"
                onClick={() => setConfirmingId(selected.public_id)}
              >
                Remove
              </Button>
            )}
          </header>
          <BlockEditor
            key={selected.public_id}
            block={selected}
            onSave={(config) => saveBlock(selected, config)}
          />
        </section>
      )}
    </div>
  );

  return (
    <Card title="Public page">
      <p className="cx-block-intro">
        Compose the public event page from blocks, set its appearance, and check
        accessibility.{" "}
        <a href={`/e/${eventId}/`} target="_blank" rel="noopener noreferrer">
          Preview public page
        </a>
      </p>
      {error && <p role="alert">{error}</p>}
      <WorkflowSections
        label="Page editor"
        sections={[
          {
            id: "content",
            label: "Content",
            description: `${blocks.length} block${blocks.length === 1 ? "" : "s"}`,
            content,
          },
          {
            id: "appearance",
            label: "Appearance",
            description: "Theme and brand",
            content: page ? (
              <ThemeSettings
                key={page.public_id}
                theme={page.theme}
                config={page.theme_config || {}}
                eventId={eventId}
                onSave={setAppearance}
              />
            ) : (
              <p className="cx-muted">Loading appearance…</p>
            ),
          },
          {
            id: "accessibility",
            label: "Accessibility",
            description:
              warnings.length > 0
                ? `${warnings.length} to review`
                : "All clear",
            content:
              warnings.length > 0 ? (
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
              ) : (
                <p className="cx-muted">
                  The automated audit found no issues with this page.
                </p>
              ),
          },
        ]}
      />
    </Card>
  );
}
