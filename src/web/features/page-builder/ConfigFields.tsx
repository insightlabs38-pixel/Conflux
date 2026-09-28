import type { ChangeEvent } from "react";
import { Button } from "../../components/Button";
import { configDefaults, type ConfigSchema } from "./configSchema";

export function ConfigFields({
  schema,
  config,
  onChange,
}: {
  schema: ConfigSchema;
  config: Record<string, unknown>;
  onChange: (config: Record<string, unknown>) => void;
}) {
  return (
    <>
      {Object.entries(schema.properties ?? {}).map(([key, field]) => {
        const value = config[key] ?? field.default;
        const change = (next: unknown) => onChange({ ...config, [key]: next });
        if (field.type === "array") {
          const items = value as Record<string, unknown>[];
          return (
            <div key={key}>
              {items.map((item, index) => (
                <div key={index}>
                  <ConfigFields
                    schema={field.items!}
                    config={item}
                    onChange={(next) =>
                      change(items.map((row, i) => (i === index ? next : row)))
                    }
                  />
                  <Button
                    variant="secondary"
                    onClick={() => change(items.filter((_, i) => i !== index))}
                  >
                    Remove
                  </Button>
                </div>
              ))}
              <Button
                variant="secondary"
                disabled={items.length >= field.maxItems!}
                onClick={() => change([...items, configDefaults(field.items!)])}
              >
                Add item
              </Button>
            </div>
          );
        }
        if (field.type === "integer")
          return (
            <label key={key}>
              {field.title}{" "}
              <input
                type="number"
                step={1}
                min={field.minimum}
                max={field.maximum}
                value={Number(value)}
                onChange={(event) =>
                  change(
                    event.target.value === "" ? "" : Number(event.target.value),
                  )
                }
              />
            </label>
          );
        if (field.type === "string") {
          const props = {
            value: String(value ?? ""),
            maxLength: field.maxLength,
            required: field["x-nonblank"],
            onChange: (
              event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
            ) => change(event.target.value),
          };
          return (
            <label key={key}>
              {field.title}{" "}
              {field["x-widget"] === "textarea" ? (
                <textarea {...props} />
              ) : (
                <input {...props} />
              )}
            </label>
          );
        }
        return (
          <p key={key} role="alert">
            Unsupported configuration type.
          </p>
        );
      })}
    </>
  );
}
