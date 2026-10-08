import { useState } from "react";
import { useDraft } from "../../hooks/useDraft";
import { Button } from "../../components/Button";
import { PagePreview } from "./PagePreview";
import {
  Field,
  Select,
  TextInput,
  ButtonLink,
} from "../../components/Foundation";

export type ThemeConfig = {
  accent?: string;
  logo_url?: string;
  banner_url?: string;
  banner_mobile_url?: string;
  banner_focus_x?: number;
  banner_focus_y?: number;
  typography?: string;
  personality?: string;
  density?: string;
  width?: string;
  hero?: string;
  hero_size?: string;
  background?: string;
  project_card?: string;
};
const choices: Record<string, string[]> = {
  typography: ["system", "editorial", "technical"],
  personality: ["restrained", "expressive", "square"],
  density: ["comfortable", "compact"],
  width: ["standard", "wide"],
  hero: ["split", "poster", "editorial"],
  hero_size: ["compact", "none", "standard", "immersive"],
  background: ["canvas", "paper"],
  project_card: ["visual", "compact"],
};
const heroSizeHint =
  "Compact is a short band with the title, status and one action. None keeps only the title and the action. Standard allows larger art. Immersive is a full-width image above the title and needs a hero image URL.";
const labels: Record<string, string> = {
  typography: "Typography",
  personality: "Corner style",
  density: "Section spacing",
  width: "Content width",
  hero: "Hero layout",
  hero_size: "Hero size",
  background: "Background",
  project_card: "Project cards",
};

export function ThemeSettings({
  theme,
  config,
  eventId,
  workspaceId,
  onSave,
}: {
  theme: "default" | "dark" | "minimal";
  config: ThemeConfig;
  eventId: string;
  workspaceId?: string;
  onSave: (
    theme: "default" | "dark" | "minimal",
    config: ThemeConfig,
  ) => Promise<void>;
}) {
  // The edits are a draft the shell knows about: they survive going to another place and coming
  // back, and the place shows as holding unsaved changes (hooks/useDraft.ts).
  const [form, setForm, formState] = useDraft(
    `theme:${eventId}`,
    { draft: config, mode: theme },
    "Event appearance",
  );
  const { draft, mode } = form;
  const setDraft = (change: (current: ThemeConfig) => ThemeConfig) =>
    setForm((current) => ({ ...current, draft: change(current.draft) }));
  const setMode = (next: typeof theme) =>
    setForm((current) => ({ ...current, mode: next }));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  function update(key: string, value: string | number) {
    setSaved(false);
    setDraft((current) => ({ ...current, [key]: value }));
  }
  return (
    <form
      className="cx-theme-editor"
      aria-label="Event appearance"
      onSubmit={async (event) => {
        event.preventDefault();
        setSaving(true);
        setError("");
        setSaved(false);
        try {
          await onSave(mode, draft);
          formState.saved();
          setSaved(true);
        } catch (cause) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Could not save appearance.",
          );
        } finally {
          setSaving(false);
        }
      }}
    >
      <fieldset disabled={saving}>
        <legend>Event appearance</legend>
        <p>
          Choose a layout and brand treatment. Changes apply to the public event
          site. Images are optional; initials provide a deterministic fallback.
        </p>
        <fieldset className="cx-theme-group" disabled={saving}>
          <legend>Brand</legend>
          <div className="cx-grid">
            <Field
              label="Accent color"
              hint="Six-digit hex; at least 4.5:1 contrast is required. Leave blank for the theme default."
            >
              {(props) => (
                <TextInput
                  {...props}
                  value={draft.accent || ""}
                  placeholder="#126454"
                  onChange={(event) => update("accent", event.target.value)}
                />
              )}
            </Field>
            {(["logo_url", "banner_url"] as const).map((key) => (
              <Field
                key={key}
                label={key === "logo_url" ? "Logo image URL" : "Hero image URL"}
                hint="Absolute HTTP(S) image URL; no scripts or embedded markup."
              >
                {(props) => (
                  <TextInput
                    {...props}
                    type="url"
                    value={draft[key] || ""}
                    onChange={(event) => update(key, event.target.value)}
                  />
                )}
              </Field>
            ))}
          </div>
          <details className="cx-theme-art">
            <summary>Hero image crop and phone image</summary>
            <div className="cx-grid">
              <Field
                label="Phone hero image URL"
                hint="Optional. Shown instead of the hero image on a phone; needs the hero image first."
              >
                {(props) => (
                  <TextInput
                    {...props}
                    type="url"
                    value={draft.banner_mobile_url || ""}
                    onChange={(event) =>
                      update("banner_mobile_url", event.target.value)
                    }
                  />
                )}
              </Field>
              {(
                [
                  [
                    "banner_focus_x",
                    "Focal point, left to right",
                    "from the left",
                  ],
                  [
                    "banner_focus_y",
                    "Focal point, top to bottom",
                    "from the top",
                  ],
                ] as const
              ).map(([key, label, where]) => (
                <Field
                  key={key}
                  label={label}
                  hint={`${draft[key] ?? 50}% ${where}. The crop keeps this point in view.`}
                >
                  {(props) => (
                    <input
                      {...props}
                      type="range"
                      min={0}
                      max={100}
                      step={1}
                      value={draft[key] ?? 50}
                      onChange={(event) =>
                        update(key, Number(event.target.value))
                      }
                    />
                  )}
                </Field>
              ))}
            </div>
            <Button
              variant="secondary"
              type="button"
              disabled={
                (draft.banner_focus_x ?? 50) === 50 &&
                (draft.banner_focus_y ?? 50) === 50
              }
              onClick={() => {
                update("banner_focus_x", 50);
                update("banner_focus_y", 50);
              }}
            >
              Centre the crop
            </Button>
          </details>
          {/^#[0-9a-fA-F]{6}$/.test(draft.accent ?? "") && (
            <p className="cx-theme-swatch" aria-hidden="true">
              <span style={{ background: draft.accent }} />
              Accent preview
            </p>
          )}
        </fieldset>
        <fieldset className="cx-theme-group" disabled={saving}>
          <legend>Style</legend>
          <div className="cx-grid">
            <Field label="Theme">
              {(props) => (
                <Select
                  {...props}
                  value={mode}
                  onChange={(event) => {
                    setMode(event.target.value as typeof mode);
                    setSaved(false);
                  }}
                >
                  <option value="default">Default / light</option>
                  <option value="dark">Dark</option>
                  <option value="minimal">Minimal</option>
                </Select>
              )}
            </Field>
            {(["typography", "personality"] as const).map((key) => (
              <Field key={key} label={labels[key]}>
                {(props) => (
                  <Select
                    {...props}
                    value={draft[key] || choices[key][0]}
                    onChange={(event) => update(key, event.target.value)}
                  >
                    {choices[key].map((value) => (
                      <option key={value} value={value}>
                        {value}
                      </option>
                    ))}
                  </Select>
                )}
              </Field>
            ))}
          </div>
        </fieldset>
        <fieldset className="cx-theme-group" disabled={saving}>
          <legend>Layout</legend>
          <div className="cx-grid">
            {(
              [
                "hero_size",
                "hero",
                "width",
                "density",
                "background",
                "project_card",
              ] as const
            ).map((key) => (
              <Field
                key={key}
                label={labels[key]}
                hint={key === "hero_size" ? heroSizeHint : undefined}
              >
                {(props) => (
                  <Select
                    {...props}
                    value={draft[key] || choices[key][0]}
                    onChange={(event) => update(key, event.target.value)}
                  >
                    {choices[key].map((value) => (
                      <option
                        key={value}
                        value={value}
                        disabled={
                          key === "hero_size" &&
                          value === "immersive" &&
                          !draft.banner_url
                        }
                      >
                        {value}
                      </option>
                    ))}
                  </Select>
                )}
              </Field>
            ))}
          </div>
        </fieldset>
      </fieldset>
      {workspaceId && (
        <details
          className="cx-theme-preview"
          onToggle={(event) => setPreviewing(event.currentTarget.open)}
        >
          <summary>Preview at desktop, tablet and mobile widths</summary>
          {previewing && (
            <PagePreview
              workspaceId={workspaceId}
              eventId={eventId}
              theme={mode}
              config={draft}
            />
          )}
        </details>
      )}
      {error && <p role="alert">{error}</p>}
      {saved && <p role="status">Event appearance saved.</p>}
      {!saved &&
        !saving &&
        JSON.stringify(draft) !== JSON.stringify(config) && (
          <p role="status" className="cx-muted">
            Unsaved changes
          </p>
        )}
      <div className="cx-stack cx-stack--horizontal">
        <Button variant="primary" type="submit" disabled={saving}>
          {saving ? "Saving…" : "Save appearance"}
        </Button>
        <ButtonLink
          href={`/e/${eventId}/`}
          variant="secondary"
          target="_blank"
          rel="noopener"
        >
          Open public preview
        </ButtonLink>
      </div>
    </form>
  );
}
