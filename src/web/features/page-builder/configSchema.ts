export type ConfigSchema = {
  type: "object" | "string" | "integer" | "array";
  title?: string;
  default?: unknown;
  properties?: Record<string, ConfigSchema>;
  items?: ConfigSchema;
  maxLength?: number;
  minimum?: number;
  maximum?: number;
  maxItems?: number;
  "x-nonblank"?: boolean;
  "x-widget"?: string;
  "x-create-default"?: string | null;
  additionalProperties?: boolean;
};

export function configDefaults(
  schema: ConfigSchema,
  creating = false,
): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(schema.properties ?? {}).map(([key, field]) => [
      key,
      structuredClone(
        creating ? (field["x-create-default"] ?? field.default) : field.default,
      ),
    ]),
  );
}

export function configError(schema: ConfigSchema, value: unknown): string {
  const label = schema.title ?? "Configuration";
  if (schema.type === "object") {
    if (!value || typeof value !== "object" || Array.isArray(value))
      return `${label} must be an object.`;
    if (
      schema.additionalProperties === false &&
      Object.keys(value).some((key) => !(key in (schema.properties ?? {})))
    )
      return `${label} has unknown fields.`;
    for (const [key, field] of Object.entries(schema.properties ?? {})) {
      const error = configError(
        field,
        Object.prototype.hasOwnProperty.call(value, key)
          ? (value as Record<string, unknown>)[key]
          : field.default,
      );
      if (error) return error;
    }
    return "";
  }
  if (schema.type === "string") {
    if (typeof value !== "string") return `${label} must be text.`;
    if (schema["x-nonblank"] && !value.trim()) return `${label} is required.`;
    if (Array.from(value).length > schema.maxLength!)
      return `${label} must be at most ${schema.maxLength} characters.`;
    return "";
  }
  if (schema.type === "integer") {
    return typeof value === "number" &&
      Number.isInteger(value) &&
      value >= schema.minimum! &&
      value <= schema.maximum!
      ? ""
      : `${label} must be an integer from ${schema.minimum} to ${schema.maximum}.`;
  }
  if (schema.type === "array") {
    if (!Array.isArray(value) || value.length > schema.maxItems!)
      return `${label} must have at most ${schema.maxItems} items.`;
    for (const item of value) {
      const error = configError(schema.items!, item);
      if (error) return error;
    }
    return "";
  }
  return "Unsupported configuration type.";
}
