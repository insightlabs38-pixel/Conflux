import { useState } from "react";
import { Button } from "../../components/Button";
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
  typography?: string;
  personality?: string;
  density?: string;
  width?: string;
  hero?: string;
  background?: string;
  project_card?: string;
};
const choices: Record<string, string[]> = {
  typography: ["system", "editorial", "technical"],
  personality: ["restrained", "expressive", "square"],
  density: ["comfortable", "compact"],
  width: ["standard", "wide"],
  hero: ["split", "poster", "editorial"],
  background: ["canvas", "paper"],
  project_card: ["visual", "compact"],
};
const labels: Record<string, string> = {
  typography: "Typography",
  personality: "Corner style",
  density: "Section spacing",
  width: "Content width",
  hero: "Hero layout",
  background: "Background",
  project_card: "Project cards",
};

export function ThemeSettings({
  theme,
  config,
  eventId,
  onSave,
}: {
  theme: "default" | "dark" | "minimal";
  config: ThemeConfig;
  eventId: string;
  onSave: (
    theme: "default" | "dark" | "minimal",
    config: ThemeConfig,
  ) => Promise<void>;
}) {
  const [draft, setDraft] = useState(config);
  const [mode, setMode] = useState(theme);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  function update(key: string, value: string) {
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
                "hero",
                "width",
                "density",
                "background",
                "project_card",
              ] as const
            ).map((key) => (
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
      </fieldset>
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
        <Button type="submit" disabled={saving}>
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
